import statistics
from collections import defaultdict, deque
from shared import shared_data

class PolicyEngine:
    """
    IDENTICO all'originale, ma usa shared_data per comunicare
    """
    def __init__(self, history_length=10, var_threshold=2e13):
        self.history_length = history_length
        self.var_threshold = var_threshold
        self.traffic_history = defaultdict(lambda: deque(maxlen=history_length))

    def update(self, dpid, port, rx_bps):
        """IDENTICO all'originale"""
        self.traffic_history[(dpid, port)].append(rx_bps)
        return self.traffic_history[(dpid, port)]

    def evaluate(self, dpid, port, rx_bps):
        history = self.traffic_history[(dpid, port)]
        if len(history) < 5:
            return False, 0, 0
        
        avg = statistics.mean(history)
        var = statistics.variance(history)
        threshold_dyn = max(avg * 1.5, 10e6)
        
        # 🆕 AGGIUNGI: Soglia assoluta per traffico molto alto
        ABSOLUTE_HIGH_THRESHOLD = 30e6  # 30 Mbps
        
        # Suspicious se:
        # 1. Spike + alta varianza (attacco bursty) O
        # 2. Traffico costantemente sopra soglia assoluta (attacco sustained)
        spike_and_unstable = rx_bps > threshold_dyn * 1.2 and var > self.var_threshold
        sustained_high = rx_bps > ABSOLUTE_HIGH_THRESHOLD and avg > ABSOLUTE_HIGH_THRESHOLD
        
        suspicious = spike_and_unstable or sustained_high
        
        return suspicious, var, threshold_dyn