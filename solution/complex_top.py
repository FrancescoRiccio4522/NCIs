#!/usr/bin/python
from mininet.log import setLogLevel, info
from mininet.net import Mininet, CLI
from mininet.node import RemoteController
from mininet.link import TCLink

class Environment(object):
    def __init__(self): 
        
        self.net = Mininet(link=TCLink, controller=RemoteController)
        try: 
            info("*** Starting controller\n")
            self.net.addController('C1', controller=RemoteController, port=6633)
            
            info("*** Adding hosts\n")
            # Host legittimi (come nella vecchia topologia)
            self.h1 = self.net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1')
            self.h2 = self.net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2')
            self.h3 = self.net.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3')
            self.h4 = self.net.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.4')
            
            # Host attaccanti distribuiti su switch diversi - in caso di test multi-attacco rimuovere i commenti
            self.attacker1 = self.net.addHost('attacker1', mac='00:00:00:00:00:11', ip='10.0.0.11')
            self.attacker2 = self.net.addHost('attacker2', mac='00:00:00:00:00:12', ip='10.0.0.12')
            self.attacker3 = self.net.addHost('attacker3', mac='00:00:00:00:00:13', ip='10.0.0.13')
            
            info("*** Adding switches\n")
            # 10 switch in struttura ad albero binario perfetto
            self.s1 = self.net.addSwitch('s1')   # Livello 0 - Root
            self.s2 = self.net.addSwitch('s2')   # Livello 1 - Left branch
            self.s3 = self.net.addSwitch('s3')   # Livello 1 - Middle branch
            self.s4 = self.net.addSwitch('s4')   # Livello 1 - Right branch
            self.s5 = self.net.addSwitch('s5')   # Livello 2 - Under s2
            self.s6 = self.net.addSwitch('s6')   # Livello 2 - Under s3
            self.s7 = self.net.addSwitch('s7')   # Livello 2 - Under s4
            self.s8 = self.net.addSwitch('s8')   # Livello 3 - Under s5
            self.s9 = self.net.addSwitch('s9')   # Livello 3 - Under s6
            self.s10 = self.net.addSwitch('s10') # Livello 3 - Under s7
            
            info("*** Adding links\n")
            
            # Collegamenti host legittimi - switch (100 Mbps)
            self.net.addLink(self.h1, self.s2, bw=100, delay='2ms', max_queue_size=1000)
            self.net.addLink(self.h2, self.s6, bw=100, delay='2ms', max_queue_size=1000)
            self.net.addLink(self.h3, self.s9, bw=100, delay='2ms', max_queue_size=1000)
            self.net.addLink(self.h4, self.s10, bw=100, delay='2ms', max_queue_size=1000)

            # Collegamenti attaccanti - switch
            self.net.addLink(self.attacker1, self.s3, bw=100, delay='2ms', max_queue_size=1000)
            self.net.addLink(self.attacker2, self.s7, bw=100, delay='2ms', max_queue_size=1000)
            self.net.addLink(self.attacker3, self.s8, bw=100, delay='2ms', max_queue_size=1000)

            # Collegamenti tra switch - Struttura ad ALBERO BINARIO (150 Mbps)
            # Livello 0-1
            self.net.addLink(self.s1, self.s2, bw=150, delay='25ms', max_queue_size=1000)
            self.net.addLink(self.s1, self.s3, bw=150, delay='25ms', max_queue_size=1000)
            self.net.addLink(self.s1, self.s4, bw=150, delay='25ms', max_queue_size=1000)

            # Livello 1-2
            self.net.addLink(self.s2, self.s5, bw=150, delay='25ms', max_queue_size=1000)
            self.net.addLink(self.s3, self.s6, bw=150, delay='25ms', max_queue_size=1000)
            self.net.addLink(self.s4, self.s7, bw=150, delay='25ms', max_queue_size=1000)

            # Livello 2-3
            self.net.addLink(self.s5, self.s8, bw=150, delay='25ms', max_queue_size=1000)
            self.net.addLink(self.s6, self.s9, bw=150, delay='25ms', max_queue_size=1000)
            self.net.addLink(self.s7, self.s10, bw=150, delay='25ms', max_queue_size=1000)
            
            info("*** Starting network\n")
            self.net.build()
            self.net.start()
            self.net.pingAll()
            
            self.h3.cmd('iperf -s &')
            
            info("*** Network topology summary:\n")
            info("*** Structure: Perfect Binary Tree (4 levels, NO CYCLES)\n")
            info("*** Level 0: s1 (root)\n")
            info("*** Level 1: s2, s3, s4\n") 
            info("*** Level 2: s5, s6, s7\n")
            info("*** Level 3: s8, s9, s10\n")
            info("*** Legitimate hosts: h1(s2), h2(s6), h3(s9), h4(s10)\n")
            info("*** Attackers: attacker1(s3), attacker1(s7), attacker1(s8)\n") # - in caso di test multi-attacco rimuovere il commento
            
        except Exception as e:
            info(f"!!! Errore durante l'inizializzazione della rete: {e}\n")
            self.net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    info('*** Avvio dell\'ambiente complesso\n')
    env = Environment()
    info("*** Avvio CLI\n")
    CLI(env.net)
    env.net.stop()
