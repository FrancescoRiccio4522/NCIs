from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
from ryu.lib import hub
import json
import logging
from ryu import cfg

# Import dei moduli separati
from monitoring.traffic_monitor import TrafficMonitor
from policies.policy_engine import PolicyEngine
from enforcement.flow_enforcer import FlowEnforcer
from shared import shared_data

cfg.CONF.ofp_tcp_listen_port = 6633

class SDNController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    SLEEP_TIME = 2  
    VAR_THRESHOLD = 2e13
    BASE_DELAY = 5
    MAX_DELAY = 30

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger.setLevel(logging.INFO)
        
        # RIMOSSO: self.datapaths = {} (ora in shared_data)
        self.mac_to_port = {}  # Manteniamo questo qui perché specifico del learning switch
        
        # Carica host info in shared_data invece che in self
        data = self.load_host_info_json("config/host_info.json")
        shared_data.host_info = data.get("host_info", {})
        
        # Inizializza moduli separati
        self.policy_engine = PolicyEngine(var_threshold=self.VAR_THRESHOLD)
        self.flow_enforcer = FlowEnforcer(self)  # Passa self per logger e block_udp_flow
        self.traffic_monitor = TrafficMonitor(self.SLEEP_TIME)  # Non passa più self

    def load_host_info_json(self, path):
        """IDENTICO all'originale"""
        with open(path) as f:
            return json.load(f)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def port_stats_reply_handler(self, ev):
        """
        QUASI identico, ma usa shared_data invece di self.flow_enforcer.blocked
        """
        dp = ev.msg.datapath
        dpid = dp.id
        for stat in ev.msg.body:
            port = stat.port_no
            if port == 4294967294:
                continue
                
            rx_bps = (stat.rx_bytes * 8) / self.SLEEP_TIME
            tx_bps = (stat.tx_bytes * 8) / self.SLEEP_TIME
            print(f"[PORT {port}] RX: {rx_bps / 1e6:.2f} Mbps | TX: {tx_bps / 1e6:.2f} Mbps")
            
            self.policy_engine.update(dpid, port, rx_bps)
            suspicious, var, threshold_dyn = self.policy_engine.evaluate(dpid, port, rx_bps)
            
            key = f"{dpid}-{port}"
            
            # CAMBIATO: usa shared_data invece di self.host_info e self.flow_enforcer.blocked
            if suspicious and key in shared_data.host_info and not shared_data.is_blocked(key):
                attacker = shared_data.host_info[key]
                
                # CAMBIATO: usa shared_data.block_counts invece di self.flow_enforcer.block_counts
                shared_data.block_counts[key] = shared_data.block_counts.get(key, 0) + 1
                num_blocks = shared_data.block_counts[key]
                
                unblock_delay = min(2 ** num_blocks * self.BASE_DELAY, self.MAX_DELAY)
                self.flow_enforcer.block(dp, key, attacker['ip'], unblock_delay)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        QUASI identico, ma usa shared_data.datapaths invece di self.datapaths
        """
        dp = ev.msg.datapath
        
        # CAMBIATO: salva in shared_data invece che in self.datapaths
        shared_data.datapaths[dp.id] = dp
        
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=0, match=match, instructions=inst)
        dp.send_msg(mod)
        self.logger.info(f"[+] Switch registrato: {dp.id}")

    def block_udp_flow(self, dp, src_ip, dst_ip):
        """IDENTICO all'originale - FlowEnforcer chiama questa funzione"""
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, ipv4_src=src_ip, ipv4_dst=dst_ip)
        actions = []
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=20, match=match, instructions=inst)
        dp.send_msg(mod)
        self.logger.info(f"[BLOCKLIST] Rule installed on switch {dp.id} for {src_ip} → {dst_ip}")

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """IDENTICO all'originale - gestione learning switch"""
        msg = ev.msg
        dp = msg.datapath
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        dpid = dp.id
        self.mac_to_port.setdefault(dpid, {})[eth.src] = in_port
        out_port = self.mac_to_port[dpid].get(eth.dst, ofproto.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=eth.dst, eth_src=eth.src)
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
            dp.send_msg(parser.OFPFlowMod(datapath=dp, priority=1, match=match, instructions=inst))
        data = msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None
        dp.send_msg(parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id, in_port=in_port, actions=actions, data=data))

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, CONFIG_DISPATCHER])
    def state_change_handler(self, ev):
        """
        CAMBIATO: usa shared_data.datapaths invece di self.datapaths
        """
        dp = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            shared_data.datapaths[dp.id] = dp
        elif dp.id in shared_data.datapaths:
            del shared_data.datapaths[dp.id]