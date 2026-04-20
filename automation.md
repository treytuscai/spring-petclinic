# Pipeline Automation (JCasC + setup.sh)

The SonarQube setup tutorial describes how to configure Jenkins, SonarQube, credentials, webhooks, and the pipeline job manually through multiple browser-based steps. The `automated` branch replaces all of that with two files: a Jenkins Configuration as Code file (`casc.yaml`) that declaratively defines Jenkins state at boot, and a shell script (`setup.sh`) that orchestrates the full stack in one command.

## Files

```
spring-petclinic/
├── setup.sh                  One-command stack bootstrap
└── jenkins/
    ├── Dockerfile            Jenkins image with Docker CLI, Ansible, and plugins
    ├── casc.yaml             JCasC: Jenkins configuration
    └── plugins.txt           Plugin list installed at image build time
```

## How It Works

### casc.yaml

Jenkins Configuration as Code (JCasC) lets you define Jenkins configuration in a YAML file instead of clicking through the UI. On first boot, Jenkins reads `casc.yaml` and applies everything automatically.

The file configures four things:

1. **Admin user**: creates the `admin`/`admin` account with signups disabled
2. **SonarQube credential**: registers the analysis token (injected via the `SONAR_TOKEN` environment variable) as a Jenkins secret
3. **SonarQube server**: points Jenkins at `http://sonarqube:9000` using the registered credential
4. **Pipeline job**: creates a `spring-petclinic` pipeline job that pulls the `Jenkinsfile` from the repo and polls for changes every 2 minutes

This eliminates the manual plugin installation, credential entry, SonarQube server configuration, and Blue Ocean pipeline creation described in the setup tutorial.

### setup.sh

The script brings up the full stack in the correct order:

1. **Raises `vm.max_map_count`**: SonarQube's embedded Elasticsearch requires this kernel parameter set to at least 262144, otherwise SonarQube exits on startup
2. **Starts infrastructure**: brings up Postgres, SonarQube, Prometheus, Grafana, and the production server
3. **Waits for SonarQube**: polls the health endpoint until SonarQube reports `UP`
4. **Creates SonarQube token and webhook**: uses the SonarQube API to generate a Global Analysis Token and register the Jenkins webhook, then writes the token to `.env` so Docker Compose can pass it to Jenkins
5. **Starts Jenkins**: brings up Jenkins, which reads `casc.yaml` on boot and auto-configures itself using the token from the previous step
6. **Waits for Jenkins**: polls the login page until Jenkins is ready

After the script finishes, the pipeline job exists and is ready to run. No browser interaction is required.

### Plugin Installation

Plugins are installed at Docker image build time via `plugins.txt` and the `jenkins-plugin-cli`. This avoids the manual "Install suggested plugins" step and ensures the required plugins are always present:

- `configuration-as-code`: JCasC support
- `job-dsl`: programmatic job creation from `casc.yaml`
- `sonar`: SonarQube Scanner integration
- `prometheus`: exposes `/prometheus` metrics endpoint for Grafana
- `blueocean`: pipeline visualization UI
- `git`: Git SCM support
- `workflow-aggregator`: Pipeline plugin suite

## Prerequisites

Assumes a fresh Ubuntu VM with nothing installed. Run the following and then log out and back in for the Docker group to take effect:

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
sudo apt-get install -y git
```

## Usage

```bash
git clone https://github.com/treytuscai/spring-petclinic.git
cd spring-petclinic
git checkout feature/integration
chmod +x setup.sh
./setup.sh
```

Once complete:

| Service | URL | Credentials |
|---------|-----|-------------|
| Jenkins | http://localhost:8080 | admin / admin |
| SonarQube | http://localhost:9000 | admin / admin |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | — |
| PetClinic | http://localhost:8082 | — (available after first build) |

## Note on Dastardly (DAST Scan)

Dastardly only ships an x86 (amd64) Docker image. It works on x86 machines and through Docker Desktop on macOS. If running on a Linux VM on an ARM Mac (e.g. UTM), the VM must use the Apple Virtualization backend with Rosetta enabled. Standard QEMU emulation cannot run Dastardly's embedded Chromium browser.

Once enabled in UTM, register it inside the guest:
> ```bash
> sudo apt-get install -y binfmt-support
> sudo /usr/sbin/update-binfmts --install rosetta /mnt/rosetta/rosetta \
>    --magic "\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x3e\x00" \
>    --mask "\xff\xff\xff\xff\xff\xfe\xfe\x00\xff\xff\xff\xff\xff\xff\xff\xff\xfe\xff\xff\xff" \
>    --preserve yes --fix-binary yes
> ```
> Without this, the pipeline will skip the Dastardly stages.