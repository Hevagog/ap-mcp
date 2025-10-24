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
    docker compose build

[group('docker')]
[doc('runs docker compose. Make sure to have a .env file with the Gemini API key named API_KEY')]
run:
    docker compose up

[group('docker')]
[doc('Run an interactive shell in a new container for a service')]
shell NAME:
    docker compose run --rm --service-ports {{NAME}} /bin/bash
