# Spring PetClinic + SonarQube + Jenkins Setup Tutorial
> **Branch:** `yen-sonarqube` | **Repo:** [treytuscai/spring-petclinic](https://github.com/treytuscai/spring-petclinic)

---

## 1. Prerequisites

Make sure the following are installed on your machine before starting:

| Tool | Notes |
|------|-------|
| Java 17+ | Required to build and run the Spring Boot app |
| Maven wrapper (included) | Pre-bundled as `./mvnw` — no install needed |
| Git | To clone the repo and checkout the branch |
| Docker Desktop | Required to run SonarQube and Jenkins as containers |
| Docker Compose | Usually bundled with Docker Desktop |

Verify each is installed:
```bash
java -version
git --version
docker --version
```

---

## 2. Clone the Repository

```bash
git clone https://github.com/treytuscai/spring-petclinic.git
cd spring-petclinic
```

---

## 3. Checkout the `yen-sonarqube` Branch

```bash
git fetch origin
git checkout yen-sonarqube
```

Confirm you're on the right branch:
```bash
git branch
# You should see: * yen-sonarqube
```

---

## 4. Start All Services with Docker

The `docker-compose.yml` defines all four services — `mysql`, `postgres`, `sonarqube`, and `jenkins`. Start them all with one command:

```bash
docker compose up -d
```

This will start:
- **MySQL** on port `3306`
- **PostgreSQL** on port `5432`
- **SonarQube** on port `9000`
- **Jenkins** on port `8080`

Check all containers are running:
```bash
docker compose ps
```

> **Note:** SonarQube takes 60–90 seconds to fully boot. Jenkins may take a minute as well on first startup.

---

## 5. Set Up SonarQube

### 5.1 Log In

Once SonarQube is running, open your browser at:
```
http://localhost:9000
```

Log in with the default credentials:
- **Username:** `admin`
- **Password:** `admin`

> On first login, SonarQube will prompt you to change the default password. Do so and keep a note of it.

### 5.2 Generate a Token

Jenkins needs a token to authenticate with SonarQube:

1. Click your **avatar** (top-right) → **My Account**
2. Go to the **Security** tab
3. Under **Generate Tokens**, select **Global Analysis Token**, enter a name (e.g., `petclinic-token`) and click **Generate**
4. **Copy the token immediately** — it won't be shown again

---

## 6. Set Up Jenkins

### 6.1 Unlock Jenkins

Open your browser at:
```
http://localhost:8080
```

Jenkins will ask for an initial admin password. Retrieve it with:
```bash
docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Paste the password into the browser to unlock Jenkins.

### 6.2 Install Plugins

1. On the **Customize Jenkins** screen, click **Install suggested plugins** and wait for it to finish
2. Create your admin user when prompted
3. Once on the Jenkins dashboard, go to **Manage Jenkins** → **Plugins** → **Available plugins**
4. Search for **Blue Ocean** and check the box
5. Click **Install** and wait for it to complete

### 6.3 Add SonarQube Token to Jenkins Credentials

1. Go to **Manage Jenkins** → **Credentials** → **System** → **Global credentials** → **Add Credentials**
2. Fill in:
   - **Kind:** Secret text
   - **Secret:** your SonarQube token from Step 5.2
   - **ID:** `sonar-token`
   - **Description:** SonarQube Token
3. Click **Create**

### 6.4 Configure SonarQube Server in Jenkins

1. Go to **Manage Jenkins** → **System**
2. Scroll down to **SonarQube servers** and click **Add SonarQube**
3. Fill in:
   - **Name:** `SonarQube`
   - **Server URL:** `http://sonarqube:9000`
   - **Server authentication token:** select `sonar-token` from the dropdown
4. Click **Save**

> **Important:** Use `http://sonarqube:9000` (not `localhost:9000`) because Jenkins and SonarQube are both inside Docker and communicate via the Docker network.

### 6.5 Create the Pipeline in Blue Ocean

1. Click **Open Blue Ocean** in the left Jenkins sidebar
2. Click **New Pipeline**
3. Select **Git** as the source
4. Enter the repository URL:
   ```
   https://github.com/treytuscai/spring-petclinic.git
   ```
5. Select the `yen-sonarqube` branch
6. Click **Create Pipeline**

Blue Ocean will detect the `Jenkinsfile` already in the branch and run the pipeline automatically.

---

## 7. Pipeline Overview

The `Jenkinsfile` in the `yen-sonarqube` branch defines four stages:

| Stage | What it does |
|-------|-------------|
| **Checkout** | Pulls the latest code from the branch |
| **Build and Test** | Compiles the project and runs all tests |
| **SonarQube Analysis** | Sends results to SonarQube |
| **Quality Gate** | Waits up to 5 minutes for SonarQube verdict; fails pipeline if it does not pass |

---

## 8. Run the Analysis Manually (Optional)

If you want to trigger SonarQube analysis directly without Jenkins, run from the project root:

```bash
./mvnw clean verify sonar:sonar \
  -Dsonar.projectKey=spring-petclinic \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=<YOUR_TOKEN> \
  -Dtest='!PostgresIntegrationTests' \
  -DfailIfNoTests=false
```

Replace `<YOUR_TOKEN>` with the token from Step 5.2.

> **Note:** `PostgresIntegrationTests` is excluded because it tries to spin up its own postgres container, which conflicts with the already-running postgres container.

---

## 9. View the SonarQube Results

1. Go to `http://localhost:9000`
2. Click **Projects** in the top navigation
3. Select **spring-petclinic**
4. Explore the dashboard for bugs, vulnerabilities, and code smells

---

## 10. Troubleshooting

### SonarQube not accessible at `localhost:9000`

Check what containers are running:
```bash
docker compose ps
```

If sonarqube has exited, check the logs:
```bash
docker compose logs sonarqube
```

If the logs contain `max virtual memory areas vm.max_map_count [...] is too low`, run:
```bash
docker run --rm --privileged alpine sysctl -w vm.max_map_count=262144
docker compose down
docker compose up -d
```

If SonarQube is slow to start, it needs at least **4GB of RAM**:
Docker Desktop → Settings → Resources → Memory → set to **4GB or more** → Apply & Restart.

### Jenkins not accessible at `localhost:8080`
- Check the container: `docker compose ps`
- View logs: `docker compose logs jenkins`

### Jenkins pipeline can't reach SonarQube
- Make sure you used `http://sonarqube:9000` (not `localhost`) in the Jenkins SonarQube server config

### Build fails with authentication error
- Double-check the SonarQube token was copied correctly (no extra spaces)
- Make sure SonarQube is fully started before triggering the pipeline

### Port conflict (9000 or 8080 already in use)
- Stop the conflicting process, or edit `docker-compose.yml` to map a different host port

---

## 11. Quick Reference

```bash
# 1. Clone and switch to branch
git clone https://github.com/treytuscai/spring-petclinic.git
cd spring-petclinic && git checkout yen-sonarqube

# 2. Start everything
docker compose up -d

# 3. SonarQube → http://localhost:9000 (admin / admin) — generate token
# 4. Jenkins   → http://localhost:8080 — unlock, install Blue Ocean, add token, create pipeline

# 5. (Optional) Run analysis manually
./mvnw clean verify sonar:sonar \
  -Dsonar.projectKey=spring-petclinic \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=<YOUR_TOKEN> \
  -Dtest='!PostgresIntegrationTests' \
  -DfailIfNoTests=false

# 6. View results → http://localhost:9000
# 7. View pipeline → http://localhost:8080 → Open Blue Ocean
```
