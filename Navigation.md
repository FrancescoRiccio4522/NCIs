# Navigazione al contenuto della cartella
I file di configurazione d'esempio, forniti dai professori, sono:
- topology.py
- SimpleSwitch13.py

Il primo rappresenta la topologia di partenza, il secondo il controller fornito dalla repository **ryu**. Poiché quest'ultimo per essere utilizzato c'è bisogno di una versione di **python** precedente alle **3.10**, si è deciso di optare per la configurazione di un Dockerfile, senza un dockercompose, poiché l'immagine da creare è una sola (per ora).

## Solution
