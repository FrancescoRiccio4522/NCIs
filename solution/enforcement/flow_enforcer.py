RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

class FlowEnforcer:
    """
    Gestione blocchi UDP a livello di singolo host
    """

    def init(self, controller):
        self.controller = controller  # per logger e block_udp_flow

    def block(self, dp, key, attacker_ip, unblock_delay):
        """Blocca solo il flusso sospetto di quell'IP verso 10.0.0.3:5001"""
        shared_data.blocked.add(key)

        self.controller.logger.warning(
            f"{RED}[BLOCK] UDP {attacker_ip} → 10.0.0.3:5001 | restoring in {unblock_delay}s {RESET}"
        )
        self.controller.block_udp_flow(dp, attacker_ip, "10.0.0.3", 5001)
        hub.spawn(self.unblock, dp, key, attacker_ip, unblock_delay)

    def unblock(self, dp, key, src_ip, delay):
        """Sblocca il flusso dopo delay"""
        hub.sleep(delay)
        parser = dp.ofproto_parser
        ofproto = dp.ofproto
        
        #Ripristina traffico UDP specifico
        match = parser.OFPMatch(
            eth_type=0x800,
            ip_proto=17,
            ipv4_src=src_ip,
            ipv4_dst="10.0.0.3",
            udp_dst=5001
        )
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=dp,
            priority=20,
            match=match,
            instructions=inst,
            command=ofproto.OFPFC_MODIFY
        )
        dp.send_msg(mod)

        self.controller.logger.info(f"{GREEN}[UNBLOCK] UDP {src_ip} → 10.0.0.3:5001 restored{RESET}")
        shared_data.blocked.discard(key)