# Spring PetClinic — Full DevSecOps Pipeline Setup

[![Maven Build](https://github.com/spring-projects/spring-petclinic/actions/workflows/maven-build.yml/badge.svg)](https://github.com/spring-projects/spring-petclinic/actions/workflows/maven-build.yml)
[![Gradle Build](https://github.com/spring-projects/spring-petclinic/actions/workflows/gradle-build.yml/badge.svg)](https://github.com/spring-projects/spring-petclinic/actions/workflows/gradle-build.yml)

This guide sets up a complete DevSecOps pipeline including:

- **Jenkins** — CI/CD automation
- **SonarQube** — static code analysis
- **Dastardly (Burp Suite)** — dynamic application security testing (DAST)
- **Prometheus** — metrics collection from Jenkins
- **Grafana** — dashboard visualization of pipeline metrics
- **Ansible** — automated deployment to a production server container

**Overall flow:**

```
git push → Jenkins detects change → Build & Test → SonarQube analysis
→ Quality Gate check → Dastardly DAST scan → Package → Ansible deploy to prod
```

---

## Prerequisites

Before starting, make sure the following are installed on your machine:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (with Compose V2)
- [Git](https://git-scm.com/)

Verify both are available:

```bash
docker --version
docker compose version
git --version
```

---

## 0. Clone the Repository and Start All Services

All services (Jenkins, SonarQube, Prometheus, Grafana) are defined in `docker-compose.yml` and share a Docker network called `devsecops-net` so they can communicate by container name.

### 0.1 Clone the Repository

```bash
git clone https://github.com/treytuscai/spring-petclinic.git
cd spring-petclinic
git checkout feature/integration
```

### 0.2 Start All Services

```bash
docker compose up -d --build
```

This starts the following containers:

| Service    | URL                      | Purpose              |
|------------|--------------------------|----------------------|
| Jenkins    | http://localhost:8080    | CI/CD pipeline       |
| SonarQube  | http://localhost:9000    | Static code analysis |
| Prometheus | http://localhost:9090    | Metrics collection   |
| Grafana    | http://localhost:3000    | Metrics dashboard    |

> ⏳ Wait about **60–90 seconds** for all services to fully initialize before proceeding.

To check that all containers are running:

```bash
docker compose ps
```

All services should show `running`. If a service shows `exited`, check its logs:

```bash
docker compose logs <service-name>
```

---

## 1. Configure Jenkins

### 1.1 Log In

Open http://localhost:8080. This repo uses **Configuration as Code (CasC)**, so Jenkins is pre-configured — no setup wizard or manual plugin installation is required.

Log in with the default credentials:

- **Username:** `admin`
- **Password:** `admin`

> 📝 **Note:** The `initialAdminPassword` file will not exist because CasC bypasses the standard setup wizard. All plugins, credentials, and the pipeline job are automatically configured on startup.

---

## 2. Set Up SonarQube

### 2.1 Log In

Open http://localhost:9000 and log in with the default credentials:

- **Username:** `admin`
- **Password:** `admin`

On first login, SonarQube will prompt you to change the default password. Set a new one and save it.

### 2.2 Generate a Token

Jenkins needs a token to authenticate with SonarQube:

1. Click your avatar (top-right) → **My Account**
2. Go to the **Security** tab
3. Under **Generate Tokens**, select `Global Analysis Token`, enter a name (e.g. `petclinic-token`), and click **Generate**
4. Copy the token immediately — it will not be shown again

### 2.3 Add the SonarQube Token to Jenkins Credentials

1. In Jenkins, go to **Manage Jenkins → Credentials → System → Global credentials → Add Credentials**
2. Fill in:
   - **Kind:** `Secret text`
   - **Secret:** paste your SonarQube token from Step 2.2
   - **ID:** `sonar-token`
   - **Description:** `SonarQube Token`
3. Click **Create**

### 2.4 Configure the SonarQube Server in Jenkins

1. Go to **Manage Jenkins → System**
2. Scroll down to **SonarQube servers** and click **Add SonarQube**
3. Fill in:
   - **Name:** `SonarQube`
   - **Server URL:** `http://sonarqube:9000`
   - **Server authentication token:** select `sonar-token` from the dropdown
4. Click **Save**

> ⚠️ **Important:** Use `http://sonarqube:9000` (not `localhost:9000`) because Jenkins and SonarQube communicate inside the Docker network by container name.

### 2.5 Set Up the Webhook for Quality Gate Callback

The Quality Gate stage in the pipeline requires SonarQube to notify Jenkins when analysis completes. Without this webhook, the pipeline will wait and time out after 5 minutes.

**How it works:**

```
Jenkins triggers SonarQube analysis
       ↓
SonarQube runs the scan
       ↓
SonarQube calls Jenkins via webhook → "analysis done, here's the result"
       ↓
Jenkins marks Quality Gate as passed ✅ or failed ❌
```

**Steps:**

1. In SonarQube, go to **Administration → Configuration → Webhooks**
2. Click **Create** and fill in:
   - **Name:** `Jenkins`
   - **URL:** `http://jenkins:8080/sonarqube-webhook/`
3. Click **Create**

> ⚠️ **Important:** Use `http://jenkins:8080` (not `localhost:8080`) so SonarQube can reach Jenkins inside the Docker network.

---

## 3. Ansible Deployment on Jenkins

A separate Docker container acts as the production server, which hosts the Spring Petclinic application.

When a developer pushes new code to the repository, Jenkins automatically triggers the pipeline, retrieves the latest code, and runs an Ansible playbook. The playbook connects to the production server container through SSH and deploys the updated application.

### 3.1 Production Server Container

The `petclinic-prod` container is already included in `docker-compose.yml` and started automatically when you ran `docker compose up -d --build`. No manual build or run is needed.

Verify it is running with:

```bash
docker ps | grep petclinic-prod
```

It exposes:
- Port `2222` → SSH (for Ansible access)
- Port `8082` → the deployed web app

### 3.2 Install Ansible Inside the Jenkins Container

Jenkins needs Ansible in order to run deployment playbooks. Since Jenkins is running inside a container, Ansible must be installed there.

```bash
docker exec -u root -it jenkins bash

# Install Ansible & sshpass in Jenkins container
apt-get update
apt-get install -y ansible sshpass
exit
```

- `docker exec -u root -it jenkins bash` opens a shell inside the Jenkins container as the root user.
- `ansible` is required to run playbooks.
- `sshpass` allows password-based SSH authentication.

### 3.3 Verify Jenkins Can Reach the Production Server

Before running the pipeline, confirm that Jenkins can connect to the production container through SSH.

First enter the Jenkins container, then test the connection:

```bash
docker exec -u root -it jenkins bash
ssh -p 2222 deployer@host.docker.internal
```

Password: `deployer`

> ⚠️ **Important:** Run this from inside the Jenkins container, not from your Mac terminal. `host.docker.internal` only resolves from within a Docker container.

Type `exit` to close the SSH session and return to the Jenkins container shell, then `exit` again to leave the container.

### 3.4 Configure the Ansible Inventory

Create an Ansible inventory file that points to the production server container.

```ini
[prod]
petclinic-prod ansible_host=petclinic-prod ansible_port=22 ansible_user=deployer ansible_password=deployer ansible_connection=ssh
```

- `ansible_host=host.docker.internal` allows the Jenkins container to reach the host machine
- `ansible_port=22` points to the mapped SSH port of the production container
- `ansible_user` and `ansible_password` are the SSH login credentials inside the production server container

### 3.5 Create the Ansible Playbook

The playbook contains the deployment steps executed by Jenkins. Responsibilities include:

- Connecting to the production container
- Copying deployment files or pulling the newest code
- Restarting the application or container
- Confirming the service is running

### 3.6 Configure the Jenkins Pipeline

The Jenkins pipeline is set up to automatically run after each commit to run the Ansible deployment playbook.

### 3.7 Verify Successful Deployment

After the pipeline finishes successfully, open the application in a browser:

```
http://localhost:8082
```

> 📝 **Note:** `localhost:8082` will not be accessible until the pipeline has completed at least one successful run including the Ansible deploy stage. If the page shows a connection error, check the pipeline status in Jenkins first.

---

## 4. Set Up Prometheus

Prometheus is already started by `docker compose up` and pre-configured to scrape Jenkins metrics via `prometheus/prometheus.yml`. No manual configuration is required.

### 4.1 Verify Prometheus is Scraping Jenkins

1. Open http://localhost:9090
2. Click **Status → Targets**
3. Confirm that the `jenkins` target shows **UP**

If the Jenkins target shows **DOWN**, make sure Jenkins is fully started (wait 60–90 seconds) and that the Prometheus metrics plugin is active.

### 4.2 Enable the Prometheus Metrics Endpoint in Jenkins

1. In Jenkins, go to **Manage Jenkins → System**
2. Scroll down to the **Prometheus** section
3. Confirm the endpoint is enabled at `/prometheus/` (this should already be active after installing the plugin)
4. Click **Save**

You can manually verify the metrics endpoint is live:

```bash
curl http://localhost:8080/prometheus/
```

You should see a long list of metrics in plain text.

---

## 5. Set Up Grafana

Grafana is already started by `docker compose up` and provisioned with a Prometheus data source via `grafana/provisioning/`.

### 5.1 Log In

Open http://localhost:3000 and log in with the default credentials:

- **Username:** `admin`
- **Password:** `admin`

### 5.2 Verify the Prometheus Data Source

1. Go to **Connections → Data sources**
2. Confirm **Prometheus** is listed and click on it
3. Scroll down and click **Save & test** — you should see `"Data source is working"`

If Prometheus is not listed:

1. Click **Add data source → Prometheus**
2. Set **Prometheus server URL** to `http://prometheus:9090`
3. Click **Save & test**

> ⚠️ **Important:** Use `http://prometheus:9090` (not `localhost:9090`) because Grafana communicates with Prometheus inside the Docker network.

### 5.3 Import the Jenkins Dashboard

1. In Grafana, go to **Dashboards → Import**
2. In the **Import via grafana.com** field, enter dashboard ID `9964` *(Jenkins: Performance and Health Overview)* and click **Load**
3. Select your Prometheus data source from the dropdown
4. Click **Import**

The dashboard will now display Jenkins build durations, queue lengths, executor usage, and other pipeline metrics in real time.

---

## 6. Dastardly (Burp Suite) Security Scan

Dastardly is an automated DAST scanner from PortSwigger (the makers of Burp Suite). It is already integrated into the Jenkinsfile and runs automatically as part of the pipeline after the SonarQube Quality Gate.

**No manual setup is required.** The pipeline handles everything:

1. Packages the application into a JAR
2. Builds a disposable runtime Docker image (`docker/petclinic-runtime.Dockerfile`)
3. Starts a temporary `petclinic-qa` container on an isolated Docker network
4. Runs the Dastardly scanner against `http://petclinic-qa:8080/`
5. Archives the scan report (`dastardly-reports/dastardly-report.xml`) and log as Jenkins artifacts

### 6.1 View the Scan Report

After a pipeline run completes:

1. Open the build in Jenkins
2. Click **Artifacts** in the left sidebar
3. Download or view `dastardly-reports/dastardly-report.xml`

> 📝 **Note:** Dastardly findings currently do not fail the pipeline (report-only mode). The exit code is captured and logged so you can review findings without blocking deployments.

---

## 7. Trigger the Full Pipeline

Once all services are configured, trigger a complete end-to-end run:

1. Make a visible code change, for example edit the welcome message in `src/main/resources/templates/welcome.html`
2. Commit and push to your branch:

```bash
git add .
git commit -m "test: trigger pipeline with welcome message change"
git push
```

3. Jenkins polls the repository approximately every minute and will automatically start a new build
4. Open http://localhost:8080 and watch the pipeline progress in **Blue Ocean**

**Expected pipeline stages:**

```
Checkout → Build and Test → SonarQube Analysis → Quality Gate
→ Package for DAST → Build QA Image → Start QA Target
→ Run Dastardly Scan → Archive Results → Package → Deploy to Prod
```

5. After the pipeline completes, verify the change is live at http://localhost:8082

---

## Service Summary

| Service    | URL                      | Default Credentials      |
|------------|--------------------------|--------------------------|
| Jenkins    | http://localhost:8080    | `admin` / `admin`        |
| SonarQube  | http://localhost:9000    | `admin` / `admin`        |
| Prometheus | http://localhost:9090    | none required            |
| Grafana    | http://localhost:3000    | `admin` / `admin`        |
| Production | http://localhost:8082    | (deployed application)   |
