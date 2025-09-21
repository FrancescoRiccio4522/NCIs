FROM python:3.9-slim

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install ryu eventlet==0.30.2 dnspython==1.16.0

WORKDIR /app

# Copia TUTTA la struttura modularizzata
COPY controller.py /app/controller.py
COPY config/host_info.json /app/host_info.json

# Copia le cartelle dei moduli
COPY shared/ /app/shared/
COPY monitoring/ /app/monitoring/
COPY policies/ /app/policies/
COPY enforcement/ /app/enforcement/

# Comando aggiornato con il nuovo nome file
CMD ["ryu-manager", "controller.py"]