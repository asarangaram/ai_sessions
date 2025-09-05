# README


## Quick steps

If you are running this container first time, perform settings before running the following command

```
docker compose up -d
```

This will run all components required for Colan App's media Server.

Now the service is available at 
    http://<RPi ip address>:5002


## Settings

### Storage
Decide the storage area and update Volume map in docker-compose.yaml

```
    volumes:
    - ./app:/app
    - /media/anandas/colan_storage/docker/ai_session:/data
      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ - Change if needed
```

### Base Image
Create base image. This will take care of all python pacakge installation and if required, other software requirements.  ** Perform this only once as this takes significant time to build**.

```
    docker build --rm --no-cache -f Dockerfile.base -t ai_sessions-base . # Base image, 
```
=== YOU DON'T NEED TO RUN THIS FURTHER IF YOU DON'T CHANGE ANYTHING IN pyproject.toml FILE. ===

### App Image
```
docker build -t ai_sessions-web .
```

=== YOU DON'T NEED TO RUN THIS FURTHER IF YOU DON'T CHANGE ANYTHING IN app/ FOLDER ===



> ---------------------------------------------------------------------------------------------------

## Useful commands to clean up
### Clean build base

```
docker image prune -af 
docker build --rm --no-cache -f Dockerfile.base -t ai_sessions-base . 
docker image prune -af
```

### Start clean

```
docker system prune -af --volumes
```

### Remove dangling or old unused images

```
docker image prune -a -f
```

### Remove unused images

```
docker image prune -f
```
### `Nuke`

```
docker rmi -f $(docker images -aq)  ## images
docker rm -f $(docker ps -aq) ## containers
docker volume rm $(docker volume ls -q) ### Volumes
```
