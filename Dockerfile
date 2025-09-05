FROM ai_sessions-base AS app

# Workdir is already /app
WORKDIR /app
COPY ./env/.env.docker /env/.env


# don’t copy — to rely on docker-compose bind mount
COPY ./app /app


CMD ["python", "src/run.py"]
