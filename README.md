# CTF Flag Image Generator

Builds a Docker container with `--build-arg FLAG="..."` and creates `/image.png`.

## Docker Build
```bash
docker build --build-arg FLAG="CTF{your_flag_here}" -t ctf-image .
```

The resulting file mapping is defined in `challenge_files.json`.
