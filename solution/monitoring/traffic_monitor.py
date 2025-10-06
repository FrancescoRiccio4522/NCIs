from ryu.lib import hub
from shared import shared_data

class TrafficMonitor:
    def __init__(self, sleep_time=2):
        self.sleep_time = sleep_time
        hub.spawn(self.monitor)

    def monitor(self):
        while True:
            for dp in shared_data.datapaths.values():
                req = dp.ofproto_parser.OFPPortStatsRequest(dp, 0, dp.ofproto.OFPP_ANY)
                dp.send_msg(req)
            hub.sleep(self.sleep_time)