import statistics
from collections import defaultdict, deque
from shared import shared_data

class PolicyEngine:
    """
    Usa shared_data per comunicare
    """
    def __init__(self, history_length=10, var_threshold=2e13):
        self.history_length = history_length
        self.var_threshold = var_threshold
        self.traffic_history = defaultdict(lambda: deque(maxlen=history_length))

    def update(self, dpid, port, rx_bps):
        """TODO"""
        self.traffic_history[(dpid, port)].append(rx_bps)
        return self.traffic_history[(dpid, port)]

    def evaluate(self, dpid, port, rx_bps):
        """TODO"""
        history = self.traffic_history[(dpid, port)]
        if len(history) < 5:
            return False, 0, 0
        avg = statistics.mean(history)
        var = statistics.variance(history)
        threshold_dyn = max(avg * 1.5, 10e6)
        suspicious = rx_bps > threshold_dyn * 1.2 and var > self.var_threshold
        return suspicious, var, threshold_dyn