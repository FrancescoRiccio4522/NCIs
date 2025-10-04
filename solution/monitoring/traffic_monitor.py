from ryu.lib import hub
from shared import shared_data

class TrafficMonitor:
    """
    Utilizza shared_data al posto di controller
    """
    def __init__(self, sleep_time=2):
        # Rimuoviamo il riferimento al controller
        self.sleep_time = sleep_time
        hub.spawn(self.monitor)  # Uguale all'originale

    def monitor(self):
        """TODO"""
        while True:
            # Invece di self.controller.datapaths usa shared_state.datapaths
            for dp in shared_data.datapaths.values():
                req = dp.ofproto_parser.OFPPortStatsRequest(dp, 0, dp.ofproto.OFPP_ANY)
                dp.send_msg(req)
            hub.sleep(self.sleep_time)