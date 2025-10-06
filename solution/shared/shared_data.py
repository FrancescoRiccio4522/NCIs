from collections import defaultdict

class SharedData:
    def __init__(self):
        self.blocked = set()
        self.external_blocks = set()  
        self.block_counts = {}
        
        self.datapaths = {}  # Switch connessi
        self.host_info = {}  # Info host dal JSON
        
        self.on_suspicious_detected = None  # PolicyEngine -> FlowEnforcer
        self.on_block_applied = None       # FlowEnforcer -> Logger
    
    def is_blocked(self, key):
        return key in self.blocked or key in self.external_blocks
    
    def add_external_block(self, key, reason="external"):
        self.external_blocks.add(key)
        print(f"[EXTERNAL BLOCK] {key} - {reason}")
    
    def remove_external_block(self, key):
        self.external_blocks.discard(key)
        print(f"[EXTERNAL UNBLOCK] {key}")
    
    def get_all_blocked(self):
        return self.blocked | self.external_blocks

