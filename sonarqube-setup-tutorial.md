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

### 5.3 Set Up Webhook for Jenkins

The **Quality Gate** stage in the pipeline requires SonarQube to call back Jenkins when the analysis is complete. Without this webhook, Jenkins will wait and time out after 5 minutes.

**Why it's needed:**
```
Jenkins triggers SonarQube analysis
       ↓
SonarQube runs the analysis
       ↓
SonarQube calls back Jenkins via webhook → "analysis done, here's the result"
       ↓
Jenkins marks Quality Gate as passed or failed ✅
```

**Steps:**
1. Go to `http://localhost:9000`
2. Click **Administration** → **Configuration** → **Webhooks**
3. Click **Create** and fill in:
   - **Name:** `Jenkins`
   - **URL:** `http://jenkins:8080/sonarqube-webhook/`
4. Click **Create**

> **Important:** Use `http://jenkins:8080` (not `localhost`) because SonarQube needs to reach Jenkins via the Docker network.

---

## 6. Set Up Jenkins

> **Note:** In newer Jenkins versions, **Manage Jenkins** is accessed via the **gear icon** (⚙️) in the top right toolbar, or go directly to `http://localhost:8080/manage`.

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
4. Search for **Blue Ocean**, check the box
5. Search for **SonarQube Scanner**, check the box
6. Click **Install** and wait for both to complete
7. Restart Jenkins when prompted

> **Note:** The **SonarQube Scanner** plugin is required for the **SonarQube servers** section to appear in Jenkins System settings. Without it, you won't be able to configure the SonarQube server in Step 6.4.

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

### 6.5 Set Up SonarQube Webhook

The **Quality Gate** stage requires SonarQube to call back Jenkins when analysis is complete. Without this, Jenkins will time out after 5 minutes.

1. Go to `http://localhost:9000`
2. Click **Administration** → **Configuration** → **Webhooks**
3. Click **Create** and fill in:
   - **Name:** `Jenkins`
   - **URL:** `http://jenkins:8080/sonarqube-webhook/`
4. Click **Create**

> **Important:** Use `http://jenkins:8080` (not `localhost`) because SonarQube reaches Jenkins via the Docker network.

---

### 6.6 Create the Pipeline in Blue Ocean

Open Blue Ocean by going directly to:
```
http://localhost:8080/blue
```

> **Note:** In newer versions of Jenkins, Blue Ocean does not appear in the sidebar. Access it directly via the URL above.

1. Click **New Pipeline**
2. Select **Git** as the source
3. Enter the repository URL:
   ```
   https://github.com/treytuscai/spring-petclinic.git
   ```
4. Select the `yen-sonarqube` branch
5. Click **Create Pipeline**

Blue Ocean will detect the `Jenkinsfile` already in the branch and run the pipeline automatically.

---

## 7. Pipeline Overview

The `Jenkinsfile` in the `yen-sonarqube` branch defines four stages:

| Stage | What it does |
|-------|-------------|
| **Checkout** | Pulls the latest code from the branch |
| **Build and Test** | Compiles the project and runs all tests |
| **SonarQube Analysis** | Sends results to SonarQube |
| **Quality Gate** | Waits for SonarQube verdict via webhook; fails pipeline if it does not pass |

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

### Quality Gate times out after 5 minutes
- The SonarQube webhook is not set up. Follow Step 5.3 to add the webhook.
- Make sure the webhook URL is `http://jenkins:8080/sonarqube-webhook/` (not `localhost`)

### Jenkins pipeline SonarQube Analysis fails with "Not authorized"
- The SonarQube token is missing or not linked to the Jenkins SonarQube server config
- Go to **Manage Jenkins** → **System** → **SonarQube servers** and verify the token is selected
- If the token is expired, generate a new one in SonarQube and update the Jenkins credential

### Jenkins pipeline can't reach SonarQube
- Make sure you used `http://sonarqube:9000` (not `localhost`) in the Jenkins SonarQube server config

### Can't find "Manage Jenkins"
- Click the **gear icon** (⚙️) in the top right, or go to `http://localhost:8080/manage`

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

# 3. SonarQube → http://localhost:9000 (admin / admin)
#    - Change password
#    - Generate Global Analysis Token
#    - Add webhook: Administration → Configuration → Webhooks
#      URL: http://jenkins:8080/sonarqube-webhook/

# 4. Jenkins → http://localhost:8080
#    - Unlock with: docker compose exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
#    - Install plugins: Blue Ocean + SonarQube Scanner
#    - Add sonar-token credential
#    - Configure SonarQube server (http://sonarqube:9000)
#    - Create pipeline at http://localhost:8080/blue

# 5. (Optional) Run analysis manually
./mvnw clean verify sonar:sonar \
  -Dsonar.projectKey=spring-petclinic \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=<YOUR_TOKEN> \
  -Dtest='!PostgresIntegrationTests' \
  -DfailIfNoTests=false

# 6. View results → http://localhost:9000
# 7. View pipeline → http://localhost:8080/blue
```
