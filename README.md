Perfetto — il contenuto del README è chiaro e ben strutturato. Ti propongo una versione leggermente più ordinata, con formattazione Markdown migliorata (titoli coerenti, evidenziazione di comandi e note), e le due sezioni separate con le bandiere 🇮🇹 e 🇬🇧 come richiesto:

---

# 🇮🇹 NCIs

## 🐳 Docker

Bisogna buildare due immagini: una per la topologia `top.py` e una per la topologia `complex_top.py`.
Per farlo, utilizzare i seguenti comandi:

```bash
sudo docker build -t ryu-top .
sudo docker build -t ryu-complex-top .
```

> [!IMPORTANT]
> Ci sono **due file `host_info.json`**, uno per la topologia semplice (`top.py`) e uno per quella complessa (`complex_top.py`).
> **Sostituire il file `.json` appropriato prima di eseguire il comando di build del controller.**

Per avviare il controller:

```bash
sudo docker run --rm -it --net=host my-ryu-app
```

Per rimuovere le immagini non necessarie:

```bash
sudo docker system prune -a
```

---

## 🧪 Comandi di Test

### Host h3

* **Connessione UDP** al server sulla porta di default `5001`:

  ```bash
  iperf -s -u -i 1
  ```

* **Connessione TCP** alla porta `5002`:

  ```bash
  iperf -s -p 5002 -i 1
  ```

### Host h1

```bash
iperf -c 10.0.0.3 -u -p 5001 -t 20 -b 2M -i 1
```

### Host h2

```bash
iperf -c 10.0.0.3 -p 5002 -t 20 -b 2M -i 1
```

---

## 🔍 Verifica delle Regole Installate

```bash
sudo ovs-ofctl dump-flows s1
```

---

## 🎯 Obiettivi

1. **Over Blocking**

   * [ ] Migliorare la logica di blocco.
2. **Static Threshold**

   * [ ] Implementare una soglia adattiva dinamica.
3. **Controller-Centric Blocking Decisions**

   * [ ] Aumentare la modularità con strutture dati condivise per permettere a moduli esterni o admin di contribuire alle policy.
4. **Lack of Modular Detection and Mitigation Design**

   * [ ] Separare le varie operazioni e funzionalità del controller.
5. **Inflexible Blocking/Unblocking Policy**

   * [ ] Implementare un meccanismo di *exponential backoff*.
6. **Topology Sensitivity**

   * [ ] Testare con una topologia composta da 10 switch.

---

# 🇬🇧 NCIs

## 🐳 Docker

You need to build two images: one for the `top.py` topology and one for the `complex_top.py` topology.
Use the following commands:

```bash
sudo docker build -t ryu-top .
sudo docker build -t ryu-complex-top .
```

> [!IMPORTANT]
> There are **two `host_info.json` files**, one for the simple topology (`top.py`) and one for the complex one (`complex_top.py`).
> **Replace the `.json` file with the appropriate one before running the controller build command.**

To start the controller:

```bash
sudo docker run --rm -it --net=host my-ryu-app
```

To remove all unused images:

```bash
sudo docker system prune -a
```

---

## 🧪 Test Commands

### Host h3

* **UDP connection** to the server on default port `5001`:

  ```bash
  iperf -s -u -i 1
  ```

* **TCP connection** to port `5002`:

  ```bash
  iperf -s -p 5002 -i 1
  ```

### Host h1

```bash
iperf -c 10.0.0.3 -u -p 5001 -t 20 -b 2M -i 1
```

### Host h2

```bash
iperf -c 10.0.0.3 -p 5002 -t 20 -b 2M -i 1
```

---

## 🔍 Verify Installed Rules

```bash
sudo ovs-ofctl dump-flows s1
```

---

## 🎯 Objectives

1. **Over Blocking**

   * [ ] Improve blocking logic.
2. **Static Threshold**

   * [ ] Implement dynamic adaptive thresholding.
3. **Controller-Centric Blocking Decisions**

   * [ ] Increase modularity with shared data structures to allow external modules or admins to contribute to policies.
4. **Lack of Modular Detection and Mitigation Design**

   * [ ] Separate controller operations and functionalities.
5. **Inflexible Blocking/Unblocking Policy**

   * [ ] Implement an *exponential backoff* mechanism.
6. **Topology Sensitivity**

   * [ ] Test with a 10-switch topology.

---

Vuoi che aggiunga anche una breve **introduzione iniziale** (es. una riga che spiega lo scopo del progetto, tipo “Network Controller Improvements for SDN Experiments”)? Potrebbe rendere il README più completo.
