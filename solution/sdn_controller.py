# Copyright (C) 2011 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from operator import attrgetter
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib import hub
import time

timeInterval = 10

# Codici di escape ANSI per i colori
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"



class SimpleSwitch13(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    global timeInterval
    global RED
    global RESET
    global GREEN 

    def __init__(self, *args, **kwargs):
        super(SimpleSwitch13, self).__init__(*args, **kwargs)
        self.send_req = 0
        self.rec_res = 0
        self.threshold=700000 #80-90% del percorso critico
        self.time = 0
        self.datapaths = {}
        self.mac_to_port = {}
        self.monitoring_stats = {}
        self.alarm_switch_port = {}
        self.monitor_thread = hub.spawn(self._monitor)

    # MONITORING

    # Funzione di aggiunta e rimozione switch dalla struttura datapath
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    # Funzione di richiesta delle stats agli switch
    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)
        self.send_req = time.perf_counter()

    # Funzione di monitoraggio sempre attiva, ogni 10 secondi chiede a ogni switch di inviare
    # le sue stats di ogni porta
    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            self.logger.info('\n#########################################################')
            hub.sleep(timeInterval)

    # Funzione di stampa alla ricezione delle stats
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body

        self.rec_res = time.perf_counter()

        # Intervallo calcolato come 10 + differenza tra tempo di richiesta e risposta delle stats
        self.time = timeInterval + (self.rec_res - self.send_req)
        print(self.time)

        """
        Per il Monitoring:
        1. E' stato creato un  dizionario, monitoring_stats, in cui è presente la coppia {id_switch: {no_porta: [starts], ...}, ...}
        2. Se id_switch non è presente nella struttura, aggiungiamo  la coppia  all'interno del dizionario con le stats iniziali.
        3. Se è già presente, aggiorniamo le stats con quelle di questa iterazione di monitoraggio.
        """

        if ev.msg.datapath.id not in self.monitoring_stats.keys():
            self.logger.info('datapath         port     '
                             'rx-pkts   rx-bytes/s   rx-error   '
                             'tx-pkts   tx-bytes/s   tx-error')
            self.logger.info('---------------- --------   '
                             '-------    --------   --------   '
                             '--------   --------   --------')
            for stat in sorted(body, key=attrgetter('port_no')):
                self.logger.info('%016x %8d   %8d   %8d    %8d    %8d    %8d   %8d',
                                 ev.msg.datapath.id, stat.port_no,
                                 stat.rx_packets, stat.rx_bytes / self.time, stat.rx_errors,
                                 stat.tx_packets, stat.tx_bytes / self.time, stat.tx_errors)

            self.monitoring_stats[ev.msg.datapath.id] = {
                stat.port_no: [stat.rx_packets, stat.rx_bytes, stat.rx_errors, stat.tx_packets, stat.tx_bytes, stat.tx_errors]
                for stat in sorted(body, key=attrgetter('port_no'))
            }

            #Inizializzazione della struttura di alarm, questo sarà un contatore, a 3 (dopo 30 secondi) scatterà l'allarme per quella porta.
            self.alarm_switch_port[ev.msg.datapath.id] = {stat.port_no: [0, 0] for stat in sorted(body, key=attrgetter('port_no'))}

        else:
            previous = self.monitoring_stats[ev.msg.datapath.id]
            self.logger.info('datapath         port     '
                             'rx-pkts   rx-bytes/s   rx-error   '
                             'tx-pkts   tx-bytes/s   tx-error')
            self.logger.info('---------------- --------    '
                             '--------   --------   --------   '
                             '--------   --------   --------')
            for stat in sorted(body, key=attrgetter('port_no')):
                self.logger.info('%016x %8x   %8d   %8d   %8d   %8d   %8d   %8d',
                                 ev.msg.datapath.id, stat.port_no,
                                 (stat.rx_packets - previous[stat.port_no][0]),
                                 (stat.rx_bytes - previous[stat.port_no][1]) / self.time,
                                 stat.rx_errors - previous[stat.port_no][2],
                                 (stat.tx_packets - previous[stat.port_no][3]),
                                 (stat.tx_bytes - previous[stat.port_no][4]) / self.time,
                                 stat.tx_errors - previous[stat.port_no][5])
               
			#gestione del contatore Alarm	
                if  (((stat.rx_bytes - previous[stat.port_no][1]) / self.time) > self.threshold  or  ((stat.tx_bytes - previous[stat.port_no][4]) / self.time) > self.threshold):
                
                    if  self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][0] < 3: #Se per 30 secondi la threshold è superata, allora allarma. 
                    
                        self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][0] = self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][0] + 1
                else:
                    if  self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][0] > 0:
                    
                        self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][0] = self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][0] - 1
				
				
				
				
                if  self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][0] == 3: #blocco della porta
                    print(RED + "ALLARME SULLA PORTA " + str(stat.port_no) + " dello Switch " + str(ev.msg.datapath.id) + RESET)
                   
                    self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][1] =  1 
                    
                    print(self.alarm_switch_port)
                    
                    #BLOCCARE FLUSSO
                    time.sleep(1)
                    
                    self.lock_flow(ev, stat.port_no)
                    
                elif self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][0] == 2 and self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][1] == 1:
                	print( RED + "ALLARME SULLA PORTA " + str(stat.port_no) + " dello Switch " + str(ev.msg.datapath.id) + RESET)
                	
                	
                elif self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][0] == 1 and self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][1] == 1 : #sblocco della porta 
                    self.alarm_switch_port[ev.msg.datapath.id][stat.port_no][1] = 0 
                    self.unlock_flow(ev, stat.port_no)
                    
                
 
                
                    


            self.monitoring_stats[ev.msg.datapath.id] = {
                stat.port_no: [stat.rx_packets, stat.rx_bytes, stat.rx_errors, stat.tx_packets, stat.tx_bytes, stat.tx_errors]
                for stat in sorted(body, key=attrgetter('port_no'))
            }

           


#Remediation per l'allarme

    def lock_flow (self, ev, port_no):
	
        ofproto = ev.msg.datapath.ofproto
        parser = ev.msg.datapath.ofproto_parser
		
        match = parser.OFPMatch(in_port=port_no) 
		
        instructions=[]
		
        flow_mod = parser.OFPFlowMod(datapath=ev.msg.datapath, priority=2, match=match, instructions=instructions, command=ofproto.OFPFC_ADD, out_port= ofproto.OFPP_ANY, out_group = ofproto.OFPG_ANY, flags=ofproto.OFPFF_SEND_FLOW_REM)
		
        ev.msg.datapath.send_msg(flow_mod)
        print(RED + "Blocked traffic on port %s of switch %s " + RESET, port_no, ev.msg.datapath.id) 
	


    def unlock_flow(self, ev, port_no):
	
        ofproto = ev.msg.datapath.ofproto
        parser = ev.msg.datapath.ofproto_parser
        
        match = parser.OFPMatch(in_port=port_no) 
        
        flow_mod = parser.OFPFlowMod(datapath=ev.msg.datapath, priority=2, match=match, command=ofproto.OFPFC_DELETE, out_port= ofproto.OFPP_ANY, out_group = ofproto.OFPG_ANY, flags=ofproto.OFPFF_SEND_FLOW_REM)
        
        ev.msg.datapath.send_msg(flow_mod)
        
        print(GREEN + "Unlocked traffic on port %s of switch %s" + RESET , port_no, ev.msg.datapath.id)
		
		
		
		
		

    # Configurazione / Codice già fornito
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)
