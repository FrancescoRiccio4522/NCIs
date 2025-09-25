
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
from ryu.lib import hub
import json
import statistics
from collections import defaultdict, deque
import logging
from ryu import cfg

cfg.CONF.ofp_tcp_listen_port = 6633

class TrafficMonitor:
    def __init__(self, controller):
        self.controller = controller
        hub.spawn(self.monitor) # Avviamo un thread asincrono per il monitoraggio

    def monitor(self):
        while True:
            for dp in self.controller.datapaths.values():
                 # Richiesta OFP per raccogliere statistiche di porta
                req = dp.ofproto_parser.OFPPortStatsRequest(dp, 0, dp.ofproto.OFPP_ANY)
                dp.send_msg(req)
            hub.sleep(self.controller.SLEEP_TIME)

class PolicyEngine:
    def __init__(self, history_length=10, var_threshold=2e13): 
        self.history_length = history_length
        self.var_threshold = var_threshold
        self.traffic_history = defaultdict(lambda: deque(maxlen=history_length))

    def update(self, dpid, port, rx_bps):
        self.traffic_history[(dpid, port)].append(rx_bps)
        return self.traffic_history[(dpid, port)]

    def evaluate(self, dpid, port, rx_bps):
        history = self.traffic_history[(dpid, port)]
        if len(history) < 5:
            return False, 0, 0  # Non valutiamo se lo storico contiene meno di 5 campioni
        avg = statistics.mean(history)
        var = statistics.variance(history)
        threshold_dyn = max(avg * 1.5, 10e6)
        suspicious = rx_bps > threshold_dyn * 1.2 and var > self.var_threshold
        return suspicious, var, threshold_dyn

class FlowEnforcer:
    def __init__(self, controller):
        self.controller = controller
        self.blocked = set()    #creiamo un set di elementi per tenere traccia dei blocchi attivi
        self.block_counts = defaultdict(int)    #contiamo il numero di blocchi

    def block(self, dp, key, attacker_ip, unblock_delay):
        self.blocked.add(key)
        self.controller.logger.warning(f"[BLOCK] UDP da {attacker_ip} verso 10.0.0.3 | unblock after {unblock_delay}s")
        self.controller.block_udp_flow(dp, attacker_ip, "10.0.0.3")
        hub.spawn(self.unblock, dp, key, attacker_ip, unblock_delay)

    def unblock(self, dp, key, src_ip, delay):
        hub.sleep(delay)
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        match = parser.OFPMatch(eth_type=0x800, ip_proto=17, ipv4_src=src_ip)
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)] # ripristino forwarding
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)] 
        mod = parser.OFPFlowMod(datapath=dp, priority=20, match=match, instructions=inst, command=ofproto.OFPFC_MODIFY) 
        dp.send_msg(mod)
        self.controller.logger.info(f"[UNBLOCK] UDP da {src_ip} ripristinato")
        self.blocked.discard(key)

class SDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    SLEEP_TIME = 2  
    VAR_THRESHOLD = 2e13
    BASE_DELAY = 5
    MAX_DELAY = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        self.datapaths = {}    #usiamo un dizionario per memorizzare gli switch attivi
        self.mac_to_port = {}  
        data = self.load_host_info_json("host_info.json") # Caricamento indirizzo IP degli host monitorati
        self.host_info = data.get("host_info", {})
        self.policy_engine = PolicyEngine(var_threshold=self.VAR_THRESHOLD)
        self.flow_enforcer = FlowEnforcer(self)
        self.traffic_monitor = TrafficMonitor(self)

    def load_host_info_json(self, path):
        with open(path) as f:
            return json.load(f)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        dp = ev.msg.datapath
        dpid = dp.id
        for stat in ev.msg.body:
            port = stat.port_no
            if port == 4294967294:
                continue    # la porta local viene ignorata
            rx_bps = (stat.rx_bytes * 8) / self.SLEEP_TIME  # Conversione da byte a bit e normalizzazione dividendo per SLEEP_TIME
            tx_bps = (stat.tx_bytes * 8) / self.SLEEP_TIME
            print(f"[PORT {port}] RX: {rx_bps / 1e6:.2f} Mbps | TX: {tx_bps / 1e6:.2f} Mbps")
            self.policy_engine.update(dpid, port, rx_bps)
            suspicious, var, threshold_dyn = self.policy_engine.evaluate(dpid, port, rx_bps)
            key = f"{dpid}-{port}"
            if suspicious and key in self.host_info and key not in self.flow_enforcer.blocked:  #se un host e' sospetto e il suo IP(key) si trova nel json ma non risulta bloccato allora viene contrassegnato come un "attacker"
                attacker = self.host_info[key]
                self.flow_enforcer.block_counts[key] += 1   # Viene incrementato il contatore dei blocchi dell'host con quel determineto IP 
                num_blocks = self.flow_enforcer.block_counts[key]
                unblock_delay = min(2 ** num_blocks * self.BASE_DELAY, self.MAX_DELAY)  # Backoff esponenziale per lo sblocco del traffico
                self.flow_enforcer.block(dp, key, attacker['ip'], unblock_delay)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        dp = ev.msg.datapath
        self.datapaths[dp.id] = dp
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=0, match=match, instructions=inst)
        dp.send_msg(mod)
        self.logger.info(f"[+] Switch registrato: {dp.id}")

    def block_udp_flow(self, dp, src_ip, dst_ip):   # Funzione per installare la regola di blocco sullo switch
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, ipv4_src=src_ip, ipv4_dst=dst_ip)
        actions = []
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=20, match=match, instructions=inst)
        dp.send_msg(mod)
        self.logger.info(f"[BLOCKLIST] Rule installed on switch {dp.id} for {src_ip} → {dst_ip}")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):   # Funzione che serve per gestire i pacchetti in ingresso
        msg = ev.msg
        dp = msg.datapath
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        in_port = msg.match['in_port']  # Porta di ingresso del pacchetto
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        dpid = dp.id
        self.mac_to_port.setdefault(dpid, {})[eth.src] = in_port
        out_port = self.mac_to_port[dpid].get(eth.dst, ofproto.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]    # Prepara le azioni per inoltrare il pacchetto:
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=eth.dst, eth_src=eth.src)
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
            dp.send_msg(parser.OFPFlowMod(datapath=dp, priority=1, match=match, instructions=inst))
        data = msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        dp.send_msg(parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data))

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, CONFIG_DISPATCHER])
    def state_change_handler(self, ev): # Funzione che tiene traccia degli switch attivi e disconessi
        dp = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            self.datapaths[dp.id] = dp
        elif dp.id in self.datapaths:
            del self.datapaths[dp.id]
