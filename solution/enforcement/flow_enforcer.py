from ryu.lib import hub
from collections import defaultdict
from shared import shared_data

# Codici di escape ANSI per i colori
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

class FlowEnforcer:
    """
    Ua shared_data invece di self.blocked
    """
    
    def __init__(self, controller):
        # Manteniamo il riferimento al controller per block_udp_flow() e logger
        self.controller = controller

    def block(self, dp, key, attacker_ip, unblock_delay):
        """
        Usa shared_data.blocked
        """
        # PRIMA: self.blocked.add(key)
        shared_data.blocked.add(key)
        
        self.controller.logger.warning(f"{RED}[BLOCK] Connection UDP from {attacker_ip} to 10.0.0.3 | restoring the connection after {unblock_delay}s {RESET}")
        self.controller.block_udp_flow(dp, attacker_ip, "10.0.0.3")
        hub.spawn(self.unblock, dp, key, attacker_ip, unblock_delay)

    def unblock(self, dp, key, src_ip, delay):
        """
        Usa shared_data.blocked
        """
        hub.sleep(delay)
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        match = parser.OFPMatch(eth_type=0x800, ip_proto=17, ipv4_src=src_ip)
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=dp, priority=20, match=match, instructions=inst, command=ofproto.OFPFC_MODIFY)
        dp.send_msg(mod)
        
        self.controller.logger.info(f"{GREEN}[UNBLOCK] Connection UDP from {src_ip} restored{RESET}")
        
        # PRIMA: self.blocked.discard(key)  
        shared_data.blocked.discard(key)