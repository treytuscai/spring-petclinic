# Prometheus Setup Notes

This is the quick guide for how Prometheus is wired in this repo.

At the moment, Prometheus scrapes:
- itself (`prometheus:9090`)
- Jenkins (`jenkins:8080`) at `/prometheus/`

Configuration lives in `prometheus/prometheus.yml`, and that file is mounted into the Prometheus container by `docker-compose.yml`.

## Running it

From the project root, this is usually enough:

```bash
docker compose up -d jenkins prometheus grafana
```

If you already run everything via compose, `docker compose up -d` works too.

## Useful URLs

- Prometheus: http://localhost:9090
- Jenkins: http://localhost:8080
- Grafana: http://localhost:3000

Grafana defaults in this project:
- username: `admin`
- password: `admin`

## Quick health check

Open Prometheus, then go to Status -> Targets.
You should see both `prometheus` and `jenkins` as `UP`.

In the Prometheus query box, run:

```promql
up
```

If both are healthy, you should get `1` for each target.

## Adding another service to scrape

Add another job under `scrape_configs` in `prometheus/prometheus.yml`, for example:

```yaml
  - job_name: my-service
    static_configs:
      - targets:
          - my-service:8081
```

Then reload by restarting the Prometheus container:

```bash
docker compose restart prometheus
```

## Troubleshooting

If a target is down:

```bash
docker compose ps
docker compose logs prometheus --tail=100
docker compose logs jenkins --tail=100
```

If Jenkins metrics return 404/403:
- confirm the metrics path is exactly `/prometheus/`
- if Jenkins requires auth for metrics, Prometheus needs matching access
- test from inside the Prometheus container:

```bash
docker compose exec prometheus wget -qO- http://jenkins:8080/prometheus/ | head
```

If Prometheus fails after config edits:

```bash
docker compose restart prometheus
docker compose logs prometheus --tail=200
```

## Repo-specific details

- Prometheus config is mounted read-only: `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro`
- Jenkins, Prometheus, and Grafana communicate over `devsecops-net`
- Use Docker service names (like `jenkins`) in targets, not `localhost`
