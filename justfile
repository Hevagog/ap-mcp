[doc('Default recipe - shows available commands')]
default:
    @just --list --unsorted

[group('docker')]
[doc('cleanup unused images')]
clean-images:
    docker image prune

[group('docker')]
[doc('build the docker image')]
build:
    docker build -t ap-mcp .

[group('docker')]
[doc('run the docker container. Make sure to have a .env file with the Gemini API key named API_KEY')]
run:
    docker run -d -p 5000:5000 --env-file .env ap-mcp

[group('docker')]
[doc('Run an interactive shell in a new container for a service')]
shell:
    docker run -it ap-mcp /bin/sh