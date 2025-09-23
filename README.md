# README

## Start Server
```
PREFER_EVENTLET='1' HOST_NAME=$(hostname) gunicorn -k eventlet -w 1 -b 0.0.0.0:5002 src:application
HOST_NAME=$(hostname) gunicorn -w 1 --threads 100 -b 0.0.0.0:5002 src:application
```

## Quick steps

If you are running this container first time, perform settings before running the following command based on your system. The reason we have different setup is only to get the machine id which don't look trivial

```bash
HOSTNAME=$(hostname) docker compose -f docker-compose.yml -f docker-compose.rpi.yml up -d
HOSTNAME=$(hostname) docker compose -f docker-compose.yml -f docker-compose.linux.yml up -d
HOSTNAME=$(hostname) docker compose -f docker-compose.yml -f docker-compose.mac.yml up -d
```

This will run all components required for Colan App's media Server.

Now the service is available at

http://\<ip address\>:5002

> Thought this looks complex, handling the auto detection on the network by the application requires some level of complexity.
> It is important to have a unique id that is not just hostname. Why? This allows us to clone and use instead of editing the configuration
> for every copy.

## Settings

### Storage

Decide the storage area and update Volume map in docker-compose.yaml

```bash
    volumes:
    - ./app:/app
    - /media/anandas/colan_storage/docker/ai_session:/data
      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ - Change if needed
```

### Base Image

Create base image. This will take care of all python pacakge installation and if required, other software requirements.  **Perform this only once as this takes significant time to build**.

```bash
    docker build --rm --no-cache -f Dockerfile.base -t ai_sessions-base . # Base image, 
```

=== YOU DON'T NEED TO RUN THIS FURTHER IF YOU DON'T CHANGE ANYTHING IN pyproject.toml FILE. ===

### App Image

```bash
docker build -t ai_sessions-web .
```

=== YOU DON'T NEED TO RUN THIS FURTHER IF YOU DON'T CHANGE ANYTHING IN app/ FOLDER ===

> ---------------------------------------------------------------------------------------------------

## Useful commands to clean up

### Clean build base

```bash
docker image prune -af 
docker build --rm --no-cache -f Dockerfile.base -t ai_sessions-base . 
docker image prune -af
```

### Start clean

```bash
docker system prune -af --volumes
```

### Remove dangling or old unused images

```bash
docker image prune -a -f
```

### Remove unused images

```bash
docker image prune -f
```

### `Nuke`

```bash
docker rmi -f $(docker images -aq)  ## images
docker rm -f $(docker ps -aq) ## containers
docker volume rm $(docker volume ls -q) ### Volumes
```
