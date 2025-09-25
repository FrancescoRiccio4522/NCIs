# policies/policy_engine.py

import statistics
import numpy as np  # AGGIUNTO per percentile
from collections import defaultdict, deque
from shared import shared_data

class PolicyEngine:
    """
    PolicyEngine con soglia basata su percentile invece di media
    """
    def __init__(self, history_length=10, var_threshold=2e13, percentile=90, percentile_multiplier=1.5):
        self.history_length = history_length
        self.var_threshold = var_threshold
        
        # Parametri per percentile
        self.percentile = percentile  # Segnato nel contrller come 95
        self.percentile_multiplier = percentile_multiplier  # moltiplicatore soglia
        
        self.traffic_history = defaultdict(lambda: deque(maxlen=history_length))

    def update(self, dpid, port, rx_bps):
        """IDENTICO all'originale"""
        self.traffic_history[(dpid, port)].append(rx_bps)
        return self.traffic_history[(dpid, port)]

    def evaluate(self, dpid, port, rx_bps):
        """
        MODIFICATO: usa percentile invece di media per soglia dinamica
        """
        history = self.traffic_history[(dpid, port)]
        if len(history) < 5:
            return False, 0, 0
            
        # Calcolo della varianza
        var = statistics.variance(history)
        
        # Soglia basata su percentile
        threshold_percentile = self._calculate_percentile_threshold(history)
        
        # Traffico corrente > soglia percentile * moltiplicatore E alta varianza
        suspicious = rx_bps > threshold_percentile * self.percentile_multiplier and var > self.var_threshold
        
        return suspicious, var, threshold_percentile
    
    def _calculate_percentile_threshold(self, history):
        """
        NUOVO: Calcola soglia basata su percentile
        """
        if len(history) < 3:
            return 10e6  # Soglia minima di fallback
        
        # Converte in lista per numpy
        history_list = list(history)
        
        # Calcola percentile
        percentile_value = np.percentile(history_list, self.percentile)
        
        # Soglia minima di sicurezza
        min_threshold = 10e6
        
        return max(percentile_value, min_threshold)
    
