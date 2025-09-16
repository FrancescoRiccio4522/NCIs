FROM python:3.9-slim
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install ryu eventlet==0.30.2 dnspython==1.16.0
WORKDIR /app
COPY sdn_controller.py /app/sdn_controller.py
COPY host_info.json /app/host_info.json
CMD ["ryu-manager", "sdn_controller.py"]
