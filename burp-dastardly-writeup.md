# Dastardly Jenkins Integration Documentation

## Overview

This document covers the tracked part of the DevSecOps project that I worked on: automated dynamic security testing with Dastardly inside the Jenkins pipeline.

The goal of this setup is to make DAST part of CI/CD. Jenkins builds the application, starts a temporary QA container, runs Dastardly against that live target, and archives the resulting scan artifacts.

## What These Tools Do

### Dastardly

Dastardly is a web security testing tool from PortSwigger that is designed to run automatically in CI/CD pipelines. It performs dynamic application security testing against a live application.

In our setup, Dastardly is run after the application is packaged and started in a temporary QA container. Jenkins then launches the Dastardly container, points it to the application URL, and archives the generated report files.

An important detail is that this project does not define custom Dastardly rules or a separate scan policy file. Dastardly is using its built-in checks, and the pipeline mainly configures:

- which target URL to scan
- where the output report should be written
- how the temporary scan environment should be started

So in this case, the scan itself is automatic once the application is reachable.

## Dastardly in the Jenkins Pipeline

### Files Used

The main files involved in the Dastardly setup are:

- `Jenkinsfile`
- `docker/petclinic-runtime.Dockerfile`
- `docker-compose.yml`
- `jenkins/Dockerfile`
- `jenkins/plugins.txt`
- `jenkins/casc.yaml`
- `setup.sh`

### How the Automated Scan Works

The Dastardly flow in the pipeline is:

1. Jenkins checks out the latest code.
2. The application is built and tested.
3. SonarQube analysis and the quality gate run first.
4. Jenkins packages the application JAR for DAST.
5. Jenkins builds a temporary runtime image for the application.
6. Jenkins starts the application in a disposable container called `petclinic-qa`.
7. Jenkins runs the Dastardly container against `http://petclinic-qa:8080/`.
8. The generated report and log files are archived as Jenkins artifacts.

This design keeps the scan isolated from the production deployment. Dastardly scans a temporary QA target instead of scanning the actual production container.

### Step-by-Step Instructions

### 1. Start the infrastructure

The project uses Docker Compose for the core services:

```bash
docker compose up -d --build postgres sonarqube prometheus grafana petclinic-prod jenkins
```

This starts the services needed for the DevSecOps workflow, including Jenkins.

If the environment is being started from a fresh VM, the repo also includes an automation helper:

```bash
./setup.sh
```

This script starts the main infrastructure, waits for SonarQube, creates the Sonar token, and then starts Jenkins with the preconfigured job setup.

### 2. Make sure Jenkins has Docker CLI access

The Jenkins container must be able to run Docker commands because the pipeline builds and runs temporary containers for the DAST stage.

This is handled in two places:

- `docker-compose.yml` mounts `/var/run/docker.sock`
- `jenkins/Dockerfile` installs `docker-ce-cli`

That combination allows Jenkins to execute commands such as:

```bash
docker build
docker run
docker network create
docker rm
```

### 3. Trigger the Jenkins pipeline

Once Jenkins is up, run the `spring-petclinic` pipeline job or push a commit so the job starts automatically.

### 4. Package the application for scanning

Inside the pipeline, Jenkins runs:

```bash
./mvnw --batch-mode package -DskipTests
```

This prepares the application JAR that will be placed in the temporary runtime image.

### 5. Build the QA runtime image

Jenkins builds a temporary image using:

```bash
docker build \
  --build-arg APP_JAR=target/spring-petclinic-4.0.0-SNAPSHOT.jar \
  --file docker/petclinic-runtime.Dockerfile \
  --tag spring-petclinic:dast \
  .
```

The purpose of this image is simple: run the PetClinic app in a clean container that Dastardly can scan.

### 6. Start the QA target container

The pipeline creates an isolated Docker network and starts the target application container:

```bash
docker network create petclinic-dast
docker run -d --name petclinic-qa --network petclinic-dast spring-petclinic:dast
```

The pipeline then waits until the container is healthy before starting the scan.

### 7. Run the Dastardly scan

Jenkins launches Dastardly with environment variables for the target URL and output report path:

```bash
docker run --name dastardly-scan --rm \
  --network petclinic-dast \
  -e DASTARDLY_TARGET_URL=http://petclinic-qa:8080/ \
  -e DASTARDLY_OUTPUT_FILE=$WORKSPACE/dastardly-reports/dastardly-report.xml \
  public.ecr.aws/portswigger/dastardly:latest
```

This is the core of the automated DAST stage.

### 8. Archive the output files

After the scan finishes, Jenkins archives:

- `dastardly-reports/dastardly-report.xml`
- `dastardly-reports/dastardly.log`
- `dastardly-reports/dastardly.exitcode`

This makes the scan results available even after the build completes.

## Is Dastardly Automatic or Does It Need Manual Rules?

For this project, Dastardly is mostly automatic.

There is no separate custom rules file or custom policy file in the repository. The pipeline does not define special security rules for Dastardly. Instead, Jenkins just provides the target application and launches the Dastardly container.

That means:

- Dastardly uses its built-in checks
- the project configures the environment around the scan
- the scan can run automatically in CI/CD without manual interaction

However, the scan is still limited by what Dastardly can reach and understand on its own. In this setup:

- there is no login automation
- there are no custom authenticated sessions
- there are no custom headers, macros, or application-specific scan scripts

So this setup is best described as an automated baseline DAST scan for the running application.

## Current Pipeline Behavior

Right now, the Dastardly stage is set up as report-only.

This means:

- Jenkins still runs the scan
- reports are still collected
- the pipeline does not stop just because Dastardly found issues

This was a practical choice for the current stage of the project because it allows the team to review findings without blocking the entire pipeline.

## Provisioning Scripts and Configuration Files

The following scripts and configuration files are the main deliverables for this part of the project.

### Dastardly and Jenkins Integration

- `Jenkinsfile`
  Defines the pipeline stages for packaging the app, starting the QA container, running Dastardly, and archiving the scan results.

- `docker/petclinic-runtime.Dockerfile`
  Builds the lightweight runtime image that is scanned by Dastardly.

- `docker-compose.yml`
  Starts Jenkins and the related services needed by the DevSecOps environment.

- `jenkins/Dockerfile`
  Builds the custom Jenkins image with Docker CLI, Ansible, and other tools required by the pipeline.

- `jenkins/plugins.txt`
  Lists Jenkins plugins installed into the custom image.

- `jenkins/casc.yaml`
  Provides Jenkins Configuration as Code so the Jenkins server and pipeline job can be created automatically.

- `setup.sh`
  Automates the initial environment startup for the main DevSecOps stack from a fresh machine.

## Final Notes

From my part of the project, the most important idea is that Dastardly is now integrated into the tracked CI/CD workflow instead of being a separate manual step.

If this project is extended in the future, the next improvement would be to make the DAST setup more advanced by adding authenticated scanning, better reporting, and possibly fail conditions for serious findings. For the current project, though, the existing setup gives a clear and working example of automated dynamic security testing in Jenkins.
