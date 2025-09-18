# NCIs

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
- [ ] Aggiungere Whitelist
- [ ] Aumentare la modularità
