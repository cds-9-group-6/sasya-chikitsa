#! /bin/bash

uv pip compile pyproject.toml -o requirements.txt

podman build --arch amd64 -t engine -f Dockerfile .

podman images engine

podman tag localhost/engine:latest quay.io/rajivranjan/engine:latest

podman push quay.io/rajivranjan/engine:latest

podman tag localhost/engine:latest quay.io/rajivranjan/engine:v1

podman push quay.io/rajivranjan/engine:v1

