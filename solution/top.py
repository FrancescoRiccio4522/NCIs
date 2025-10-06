#!/usr/bin/python
from mininet.log import setLogLevel, info
from mininet.net import Mininet, CLI
from mininet.node import RemoteController  # Import del controller
from mininet.link import TCLink

class Environment(object):
    def __init__(self): 
        
        self.net = Mininet(link=TCLink, controller = RemoteController)

        try: 
            info("*** Starting controller\n")
            self.net.addController('C1', controller = RemoteController, port = 6633) 
            

            info("*** Adding hosts\n")
            self.h1 = self.net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1')
            self.h2 = self.net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2')
            self.h3 = self.net.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3')
            self.h4 = self.net.addHost('h4', mac='00:00:00:00:00:04', ip='10.0.0.4')

            info("*** Adding switches\n")
            self.s1 = self.net.addSwitch('s1')
            self.s2 = self.net.addSwitch('s2')
            self.s3 = self.net.addSwitch('s3')
            self.s4 = self.net.addSwitch('s4')

            info("*** Adding links\n")  
            
            # Collegamenti host - switch            
            self.net.addLink(self.h1, self.s1, bw = 50, delay = '2ms')
            self.net.addLink(self.h4, self.s1, bw = 50, delay = '2ms')
            self.net.addLink(self.h2, self.s2, bw = 50, delay = '2ms')
            self.net.addLink(self.h3, self.s4, bw = 50, delay = '2ms')

            # Collegamenti tra switch
            self.net.addLink(self.s1, self.s3, bw = 50, delay = '25ms') 
            self.net.addLink(self.s2, self.s3, bw = 50, delay = '25ms')
            self.net.addLink(self.s4, self.s3, bw = 50, delay = '25ms')

            info("*** Starting network\n")
            self.net.build()
            self.net.start()

            self.net.pingAll()
            self.h3.cmd('iperf -s &')

        except Exception as e:
            info(f"!!! Errore durante l'inizializzazione della rete: {e}\n")
            self.net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    info('*** Avvio dell\'ambiente\n')
    env = Environment()
    info("*** Avvio CLI\n")
    CLI(env.net)
    env.net.stop()
