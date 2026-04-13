# Spring PetClinic + SonarQube Setup Tutorial
> **Branch:** `yen-sonarqube` | **Repo:** [treytuscai/spring-petclinic](https://github.com/treytuscai/spring-petclinic)

---

## 1. Prerequisites

Make sure the following are installed on your machine before starting:

| Tool | Notes |
|------|-------|
| Java 17+ | Required to build and run the Spring Boot app |
| Maven 3.6+ | Used for building and running tests |
| Git | To clone the repo and checkout the branch |
| Docker Desktop | Required to run SonarQube as a container |
| Docker Compose | Usually bundled with Docker Desktop |

Verify each is installed:
```bash
java -version
mvn -version
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

## 4. Start SonarQube with Docker

From the project root, start the SonarQube container:
```bash
docker compose up -d
```

Wait about 30–60 seconds, then open your browser at:
```
http://localhost:9000
```

Log in with the default credentials:
- **Username:** `admin`
- **Password:** `admin`

> **Note:** On first login, SonarQube will prompt you to change the default password. Do so and keep a note of it.

---

## 5. Generate a SonarQube Token

The Maven build needs a token to authenticate with SonarQube:

1. Click your **avatar** (top-right) → **My Account**
2. Go to the **Security** tab
3. Under **Generate Tokens**, select **Global Analysis Token** enter a name (e.g., `petclinic-token`) and click **Generate**
4. **Copy the token immediately** — it won't be shown again

---

## 6. Run the Maven Build & SonarQube Analysis

From the project root, run:
```bash
mvn clean verify sonar:sonar \
  -Dsonar.projectKey=spring-petclinic \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=<YOUR_TOKEN>
```

Replace `<YOUR_TOKEN>` with the token from Step 5.

> This compiles the project, runs all tests, and sends results to SonarQube. First run may take 2–5 minutes.

---

## 7. View the Analysis Results

1. Go to `http://localhost:9000`
2. Click **Projects** in the top navigation
3. Select **spring-petclinic**
4. Explore the dashboard for bugs, vulnerabilities, and code smells

---

## 8. Troubleshooting

### SonarQube not accessible at `localhost:9000`
- Make sure Docker is running and containers started cleanly
- Check container status: `docker compose ps`
- View startup logs: `docker compose logs sonarqube`
- SonarQube needs at least **2GB of free RAM** — check Docker resource settings

### Build fails with authentication error
- Double-check the token was copied correctly (no extra spaces)
- Make sure SonarQube is fully started before running Maven

### `mvn` command not found
- Ensure Maven is on your `PATH`
- Alternatively, use the Maven wrapper: `./mvnw` instead of `mvn`

### Port 9000 already in use
- Stop the conflicting process, or edit `docker-compose.yml` to use a different host port (e.g., `9001:9000`) and update `-Dsonar.host.url=http://localhost:9001`

---

## 9. Quick Reference

```bash
# 1. Clone and switch to branch
git clone https://github.com/treytuscai/spring-petclinic.git
cd spring-petclinic && git checkout yen-sonarqube

# 2. Start SonarQube
docker compose up -d

# 3. Open browser → http://localhost:9000 (admin / admin)

# 4. Run analysis
mvn clean verify sonar:sonar \
  -Dsonar.projectKey=spring-petclinic \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.login=<YOUR_TOKEN>

# 5. View results at http://localhost:9000
```
