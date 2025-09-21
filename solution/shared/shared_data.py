from collections import defaultdict

class SharedData:
    """
    Container semplice per dati condivisi tra moduli
    Sostituisce le chiamate dirette tra classi
    """
    def __init__(self):
        # Blocklist condivisa (invece di self.blocked nel FlowEnforcer)
        self.blocked = set()
        self.external_blocks = set()  # NOVITÀ: per blocchi esterni
        self.block_counts = {}
        
        # Dati condivisi
        self.datapaths = {}  # Switch connessi
        self.host_info = {}  # Info host dal JSON
        
        # Callbacks semplici per comunicazione
        self.on_suspicious_detected = None  # PolicyEngine → FlowEnforcer
        self.on_block_applied = None       # FlowEnforcer → Logger
    
    def is_blocked(self, key):
        """Controlla se bloccato da qualsiasi fonte"""
        return key in self.blocked or key in self.external_blocks
    
    def add_external_block(self, key, reason="external"):
        """NOVITÀ: Permette a moduli esterni di bloccare"""
        self.external_blocks.add(key)
        print(f"[EXTERNAL BLOCK] {key} - {reason}")
    
    def remove_external_block(self, key):
        """NOVITÀ: Rimozione blocchi esterni"""
        self.external_blocks.discard(key)
        print(f"[EXTERNAL UNBLOCK] {key}")
    
    def get_all_blocked(self):
        """Tutti gli elementi bloccati"""
        return self.blocked | self.external_blocks

