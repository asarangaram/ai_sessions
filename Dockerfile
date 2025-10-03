FROM ai_sessions-base AS app

# Workdir is already /app
WORKDIR /app
COPY ./env/.env.docker /env/.env

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglx-mesa0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


# don’t copy — to rely on docker-compose bind mount
COPY ./app /app


CMD ["python", "src/run.py"]
