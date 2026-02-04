# Shiny Dashboard


# Docker setup and run

## Install Docker
- **macOS / Windows**: Install Docker Desktop and start it.
- **Linux**: Install Docker Engine via your distro package manager and start the service.

## Build the project
From the repository root:
```bash
docker build -t shiny-dashboard .
```

## Run the Server
```bash
docker run --rm -p 8000:8000 shiny-dashboard
```
Then open `http://localhost:8000` in a non-chrome based browser. It'll still work in chrome, but my feelings will be hurt.
