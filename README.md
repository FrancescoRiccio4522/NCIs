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
1) Overblocking
   - [ ] Aggiungere Whitelist
2) Static Threshold
   - [ ] Soglia adattiva (percentile)
3) Controller-Centric Blocking Decisions
   - [ ] Aumentare la modularità con strutture dati condivise per permettere a moduli esterni o admin di contribuire alle policies
4) Lack of Modular Detection and Mitigation Design
   - [ ] Separazione tra le varie operazioni e funzionalità del controller (già c'è ma può essere migliorato)
5) Inflexible Blocking/Unblocking Policy
   - [ ] exponential backoff (già c'è)


## Obiettivo Alternativo (al posto di 2 o 5)
Certo 🙂 ecco la traduzione dell’**obiettivo alternativo** che avevi proposto:

### **Rilevamento limitato ai pattern classici di DoS**

* **Difetto**: vengono rilevati solo attacchi DoS ad alto throughput e a tasso costante.
* **Problema**: la strategia di rilevamento e mitigazione è progettata per un singolo attaccante, ma fallisce contro attacchi **stealthy** (a bitrate variabile) o **DDoS distribuiti e bursty**.
* **Possibile soluzione**: simulare diversi pattern di attacco e rilevarli utilizzando metriche aggiuntive, come la **varianza dei burst** e gli **intervalli tra i flussi**.

