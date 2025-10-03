# NCIs

## Docker
Bisogna buildare due immagini: una per la topologia top.py e una per la topologia complex_top.py, per farlo si utilizza:
- sudo docker build -t ryu-top . 
- sudo docker build -t ryu-complex-top .

Per avviare il controller:
sudo docker run --rm -it --net=host my-ryu-app

Per rimuovere l'immagine
sudo docker system prune -a

## Comandi h3 
### Connessione UDP al server alla porta di default 5001.

iperf -s -u -i 1

### Connessione TCP alla porta 5002

iperf -s -p 5002 -i 1

## h1 
iperf -c 10.0.0.3 -u -p 5001 -t 20 -b 2M -i 1

## h2

iperf -c 10.0.0.3 -p 5002 -t 20 -b 2M -i 1

## Verifica delle regole installate
sudo ovs-ofctl dump-flows s1


## OBIETTIVI
1) Over blocking
   - [ ] Aggiungere Whitelist
2) Static Threshold
   - [ ] Soglia adattiva
3) Controller-Centric Blocking Decisions
   - [ ] Aumentare la modularità con strutture dati condivise per permettere a moduli esterni o admin di contribuire alle policies
4) Lack of Modular Detection and Mitigation Design
   - [ ] Separazione tra le varie operazioni e funzionalità del controller
5) Inflexible Blocking/Unblocking Policy
   - [ ] Exponential backoff
6) Topology Sensitivity
   - [ ] Test con una topologia con 10 switches

