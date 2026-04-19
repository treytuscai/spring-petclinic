# Grafana (Monitoring Dashboards)

Grafana is the visualization layer of the monitoring stack. It connects to Prometheus as a data source and renders Jenkins build and health metrics on a pre-configured dashboard. No UI configuration is required. The data source and dashboard are fully provisioned on first boot via mounted YAML and JSON files.

The full data flow:
```
Jenkins (Prometheus Metrics plugin) -> /prometheus endpoint
Prometheus (scrapes Jenkins every 15s)
Grafana (queries Prometheus via provisioned data source)
Browser at http://localhost:3000
```

## Files Added

Grafana-specific additions are in two places:

- **`docker-compose.yml`**: Grafana service block (attached to the shared `devsecops-net` network)
- **`grafana/provisioning/`**: auto-configuration for the data source and dashboard

```
spring-petclinic/
├── docker-compose.yml
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasource.yml            Prometheus as default data source
        └── dashboards/
            ├── dashboard.yml             Dashboard provider config
            └── jenkins-dashboard.json    Jenkins metrics dashboard
```

## Docker Compose Service Block

```yaml
grafana:
  image: grafana/grafana:latest
  container_name: grafana
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_USER=admin
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - ./grafana/provisioning:/etc/grafana/provisioning
  depends_on:
    - prometheus
  networks:
    - devsecops-net
```

Description:
- **Port 3000** is mapped to the host, Grafana UI at `http://localhost:3000`
- **Admin credentials** are seeded at first boot via environment variables (`admin` / `admin`)
- **Provisioning directory** is mounted into the container, making configuration declarative and repeatable
- **`depends_on: prometheus`** ensures Prometheus starts first
- **`devsecops-net`** is the shared Docker network that also connects Prometheus and Jenkins. This is what allows Grafana to reach Prometheus by container name

## Provisioning: Data Source

`grafana/provisioning/datasources/datasource.yml`:

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

On boot, Grafana reads this file and registers Prometheus as the default data source. The URL `http://prometheus:9090` works because Docker's internal DNS resolves `prometheus` to the Prometheus container on `devsecops-net`.

## Provisioning: Dashboard

`grafana/provisioning/dashboards/dashboard.yml`:

```yaml
apiVersion: 1

providers:
  - name: 'Jenkins'
    orgId: 1
    folder: 'Jenkins'
    type: file
    disableDeletion: false
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
      foldersFromFilesStructure: false
```

This tells Grafana to load any dashboard JSON in `/etc/grafana/provisioning/dashboards` on startup and place it in a folder called **Jenkins** in the UI.

The dashboard itself (`jenkins-dashboard.json`) is taken from community dashboard [ID 9964 — "Jenkins: Performance and Health Overview"](https://grafana.com/grafana/dashboards/9964/).

## Dashboard Panels

The dashboard queries Prometheus for metrics exposed by the **Prometheus Metrics plugin** running inside Jenkins (installed via the Jenkins Dockerfile). It consists of 19 panels in four rows. It visualizes Jenkins health, build outcomes (success/failure/unstable/aborted), JVM memory/CPU, executors, and queue metrics.

## Verifying the Grafana Setup

Once the stack is running:

1. Open `http://localhost:3000` and log in with `admin` / `admin`
2. Navigate to Connections -> **Data sources**, confirm **Prometheus** is listed as the default
3. Click Prometheus, scroll down, click **Save & test**, should report *"Successfully queried the Prometheus API"*
4. Navigate to **Dashboards** -> **Jenkins** folder -> **Jenkins: Performance and Health Overview**
5. Confirm panels are rendering data (not "No data")

If all panels show "No data", the Grafana layer is fine. The issue is upstream. See troubleshooting below.

## Troubleshooting

**Dashboard shows "No data" on every panel**

This is almost always an upstream issue, not a Grafana issue. Check in order:
1. Prometheus targets at `http://localhost:9090/targets`. The `jenkins` job should be **UP**
2. Jenkins metrics endpoint at `http://localhost:8080/prometheus` should return a wall of `jenkins_*` metrics
3. If step 2 returns Not Found, the Prometheus Metrics plugin is missing from Jenkins

**Data source test fails with "HTTP Error Bad Gateway"**

Grafana cannot reach Prometheus over the Docker network.
- Confirm both containers are on `devsecops-net`: `docker network inspect spring-petclinic_devsecops-net`
- Confirm `datasource.yml` uses `http://prometheus:9090`
- Restart Grafana: `docker compose restart grafana`

**Admin password not accepted**

`GF_SECURITY_ADMIN_PASSWORD` only seeds the password on first boot. If Grafana has booted previously with a different password, either change it through the UI or reset the container:
```bash
docker compose down -v
docker compose up -d grafana
```

**Port 3000 already in use**

Remap the host port in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"
```