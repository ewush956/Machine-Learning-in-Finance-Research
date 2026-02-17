
# Shiny Dashboard

## Docker setup and run

### Install Docker
- **macOS / Windows**: Install Docker Desktop and start it.
- **Linux**: Install Docker Engine via your distro package manager and start the service.

### Development 
From the repository root:

```bash
make dev
```
If for whatever reason `make` doesn't work you can run this instead. 
```bash
docker compose up
```

- Uses Docker Compose
- Supports reload on code changes
- No rebuild needed unless dependencies change

Open:
```
http://localhost:8000
```

### Manual Docker build (I have this automated so you shouldn't have to do this, but ya never know...)
If you want to build and run without Compose:

```bash
docker build -t shiny-dashboard .
docker run --rm -p 8000:8000 shiny-dashboard
```

Open:
```
http://localhost:8000
```

Chrome will still work, but my feelings may be hurt.

