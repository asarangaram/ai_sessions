FROM python:3.11-slim

RUN mkdir /data
COPY ./ /app
WORKDIR /app

#RUN apt-get update && apt-get install -y \
#    build-essential \
#    python3-dev \
#    libffi-dev \
#    libssl-dev \
#    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip  --root-user-action=ignore
RUN pip install pip-tools  --root-user-action=ignore
RUN pip-compile --strip-extras ./pyproject.toml    

RUN pip install --no-cache-dir -r requirements.txt --root-user-action=ignore

EXPOSE 5000

# override in docker-compose.yml
#CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "2", "-b", "0.0.0.0:5000", "chat:application"]
CMD ["python", "chat/__init__.py"]

