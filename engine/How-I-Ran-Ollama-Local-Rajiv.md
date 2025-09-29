# Chain of commands to run the llava-llama3:8b model

## Below ollama image/container has both llama3.1:8b and llava-llama3:8b

### Generate the image in both arm64 and amd64 formats

```bash


podman tag localhost/ollama-multi-model:linux-arm64-v1.0 quay.io/rajivranjan/ollama-multi-model:linux-amd64-v1.0
podman tag localhost/ollama-multi-model:linux-arm64-v1.0 quay.io/rajivranjan/ollama-multi-model:linux-arm64-v1.0

```


### Push the images to the quay.io registry

```bash
podman push quay.io/rajivranjan/ollama-multi-model:linux-amd64-v1.0
podman push quay.io/rajivranjan/ollama-multi-model:linux-arm64-v1.0
```

### Run the arm64 image on the apple silicon chipsets

```bash
podman run -it --rm -p 11434:11434 --name my-ollama localhost/ollama-multi-model:linux-arm64-v1.0
```

### Test the setup in local by calling the llava-llama3:8b model in the arm64 image

run the below command from the folder /sasya-chikitsa/engine

```bash
curl -X POST http://localhost:11434/api/generate  -H "Content-Type: application/json"  -d '{"model": "llama3.1:8b","prompt": "How do I treat wheat rust disease?","stream": false}'
```

```bash
printf '{"model": "llava-llama3:8b", "prompt": "What disease does this crop have?", "images": ["%s"], "stream": false}' \
"$(base64 -i apple_leaf.png)" | \
curl -X POST http://localhost:11434/api/generate \
-H "Content-Type: application/json" \
-d @-
```


## below processes ollama image/container with only llama3.1:8b model

```bash

./engine/build-cross-platform.sh --version v1.0 --registry quay.io/rajivranjan --push

podman push quay.io/rajivranjan/ollama-openshift:linux-amd64-v1.0


```