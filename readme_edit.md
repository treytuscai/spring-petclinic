 ---                                                                           
  Spring PetClinic Sample Application https://github.com/spring-projects/spring-
  petclinic/actions/workflows/maven-build.ymlhttps://github.com/spring-projects/
  spring-petclinic/actions/workflows/gradle-build.yml                           
                                                                                
  Full DevSecOps Pipeline Setup
                                                                                
  This guide sets up a complete DevSecOps pipeline including:                   
  - Jenkins — CI/CD automation                                                  
  - SonarQube — static code analysis                                            
  - Dastardly (Burp Suite) — dynamic application security testing (DAST)
  - Prometheus — metrics collection from Jenkins                        
  - Grafana — dashboard visualization of pipeline metrics                       
  - Ansible — automated deployment to a production server container
                                                                                
  Overall flow:                                                                 
  git push → Jenkins detects change → Build & Test → SonarQube analysis         
  → Quality Gate check → Dastardly DAST scan → Package → Ansible deploy to prod 
                                                                                
  ---                                                                           
  Prerequisites                                                                 
                                                                                
  Before starting, make sure the following are installed on your machine:
                                                                                
  - https://www.docker.com/products/docker-desktop/ (with Compose V2)           
  - https://git-scm.com/                                                        
                                                                                
  Verify both are available:
  docker --version
  docker compose version
  git --version                                                                 
   
  ---                                                                           
  0. Clone the Repository and Start All Services
                                                
  All services (Jenkins, SonarQube, Prometheus, Grafana) are defined in
  docker-compose.yml and share a Docker network called devsecops-net so they can
   communicate by container name.
                                                                                
  0.1 Fork and Clone the Repository                                             
   
  1. Fork this repository on GitHub (click Fork in the top-right)               
  2. Clone your fork locally:
  git clone https://github.com/<your-username>/spring-petclinic.git             
  cd spring-petclinic
                                                                                
  0.2 Start All Services
                                                                                
  docker compose up -d --build

  This starts the following containers:                                         
   
  ┌────────────┬───────────────────────┬──────────────────────┐                 
  │  Service   │          URL          │       Purpose        │
  ├────────────┼───────────────────────┼──────────────────────┤                 
  │ Jenkins    │ http://localhost:8080 │ CI/CD pipeline       │
  ├────────────┼───────────────────────┼──────────────────────┤                 
  │ SonarQube  │ http://localhost:9000 │ Static code analysis │
  ├────────────┼───────────────────────┼──────────────────────┤                 
  │ Prometheus │ http://localhost:9090 │ Metrics collection   │
  ├────────────┼───────────────────────┼──────────────────────┤                 
  │ Grafana    │ http://localhost:3000 │ Metrics dashboard    │
  └────────────┴───────────────────────┴──────────────────────┘                 
   
  Wait about 60–90 seconds for all services to fully initialize before          
  proceeding.     
                                                                                
  To check that all containers are running:
  docker compose ps
                   
  All services should show running. If a service shows exited, check its logs:
  docker compose logs <service-name>                                            
   
  ---                                                                           
  1. Configure Jenkins
                                                                                
  1.1 Unlock Jenkins

  Open http://localhost:8080. Jenkins will prompt for an initial admin password.
   
  Retrieve it with:                                                             
  docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
                                                                                
  Paste the password into the browser to proceed.
                                                                                
  1.2 Install Plugins
                                                                                
  1. On the Customize Jenkins screen, click Install suggested plugins and wait  
  for it to finish
  2. Create your admin user when prompted                                       
  3. Once on the Jenkins dashboard, go to Manage Jenkins → Plugins → Available  
  plugins                                                                       
  4. Search for and install each of the following (check the box, then click    
  Install):                                                                     
    - Blue Ocean — visual pipeline UI
    - SonarQube Scanner — integration with SonarQube                            
    - Prometheus metrics — exposes Jenkins metrics for Prometheus scraping      
    - HTML Publisher — publishes Dastardly scan reports                         
  5. Click Install and wait for all to complete                                 
  6. Restart Jenkins when prompted                                              
                  
  1.3 Create the Pipeline Job                                                   
                                                                                
  1. On the Jenkins dashboard, click New Item                                   
  2. Enter a job name, for example spring-petclinic                             
  3. Select Pipeline and click OK                                               
   
  Then configure the job:                                                       
  1. In the Pipeline section, set Definition to Pipeline script from SCM
  2. Set SCM to Git                                                             
  3. In Repository URL, paste your fork URL (e.g.
  https://github.com/<your-username>/spring-petclinic.git)                      
  4. If the repo is private, click Add → Jenkins to add credentials (username + 
  personal access token)                                                       
  5. In Branches to build, enter your branch name (e.g. */feature/integration)  
  6. In Script Path, enter:
  Jenkinsfile                                                                   
  7. Click Save   
                                                                                
  ---             
  2. Set Up SonarQube                                                           
   
  2.1 Log In                                                                    
                  
  Open http://localhost:9000 and log in with the default credentials:
  - Username: admin
  - Password: admin                                                             
                   
  On first login, SonarQube will prompt you to change the default password. Set 
  a new one and save it.                                                        
   
  2.2 Generate a Token                                                          
                  
  Jenkins needs a token to authenticate with SonarQube:

  1. Click your avatar (top-right) → My Account                                 
  2. Go to the Security tab
  3. Under Generate Tokens, select Global Analysis Token, enter a name (e.g.    
  petclinic-token), and click Generate                                          
  4. Copy the token immediately — it will not be shown again                    
                                                                                
  2.3 Add the SonarQube Token to Jenkins Credentials                            
                                                                                
  1. In Jenkins, go to Manage Jenkins → Credentials → System → Global           
  credentials → Add Credentials
  2. Fill in:                                                                   
    - Kind: Secret text
    - Secret: paste your SonarQube token from Step 2.2
    - ID: sonar-token
    - Description: SonarQube Token                                              
  3. Click Create
                                                                                
  2.4 Configure the SonarQube Server in Jenkins                                 
   
  1. Go to Manage Jenkins → System                                              
  2. Scroll down to SonarQube servers and click Add SonarQube
  3. Fill in:                                                                   
    - Name: SonarQube
    - Server URL: http://sonarqube:9000                                         
    - Server authentication token: select sonar-token from the dropdown
  4. Click Save                                                                 
                  
  ▎ Important: Use http://sonarqube:9000 (not localhost:9000) because Jenkins   
  ▎ and SonarQube communicate inside the Docker network by container name.
                                                                                
  2.5 Set Up the Webhook for Quality Gate Callback                              
   
  The Quality Gate stage in the pipeline requires SonarQube to notify Jenkins   
  when analysis completes. Without this webhook, the pipeline will wait and time
   out after 5 minutes.                                                         
                  
  How it works:                                                                 
  Jenkins triggers SonarQube analysis
         ↓                                                                      
  SonarQube runs the scan
         ↓               
  SonarQube calls Jenkins via webhook → "analysis done, here's the result"      
         ↓                                                                
  Jenkins marks Quality Gate as passed ✅ or failed ❌                          
                  
  Steps:                                                                        
  1. In SonarQube, go to Administration → Configuration → Webhooks
  2. Click Create and fill in:                                                  
    - Name: Jenkins           
    - URL: http://jenkins:8080/sonarqube-webhook/                               
  3. Click Create                                                               
                 
  ▎ Important: Use http://jenkins:8080 (not localhost:8080) so SonarQube can    
  ▎ reach Jenkins inside the Docker network.                                    
                                                                                
  ---                                                                           
  3. Ansible Deployment on Jenkins
                                  
  A separate Docker container acts as the production server, which hosts the
  Spring Petclinic application.                                                 
   
  When a developer pushes new code to the repository, Jenkins automatically     
  triggers the pipeline, retrieves the latest code, and runs an Ansible
  playbook. The playbook connects to the production server container through SSH
   and deploys the updated application.

  3.1: Start the Production Server Container

  First, create and run a separate container that will act as the production    
  server.
  cd prod-server/                                                               
                  
  # Build the production server image
  docker build -t petclinic-prod-server .
                                         
  # Run the container in detached mode                                          
  # Runs a background Docker container named petclinic-prod, exposing SSH on 
  port 2222 for Ansible access and the web app on port 8082 for browser access. 
  docker run -d --name petclinic-prod -p 2222:22 -p 8082:8080                   
  petclinic-prod-server
  Explanation                                                                   
  - -p 2222:22 maps port 2222 on the host to port 22 inside the container, so
  Ansible can connect through SSH.                                              
  - -p 8082:8080 maps port 8082 on the host to port 8080 inside the container,  
  so the deployed web app can be accessed from a browser.                     
  - The container name is petclinic-prod                                        
                                        
  If the container was already created previously, it can be started again with:
  docker start petclinic-prod                                                   
                                                                                
  3.2: Install Ansible Inside the Jenkins Container                             
                                                                                
  Jenkins needs Ansible in order to run deployment playbooks. Since Jenkins is  
  running inside a container, Ansible must be installed there.                  
                                                                                
  docker exec -u root -it jenkins bash                                          
  # Install Ansible & sshpass in Jenkins container
  apt-get update                                                                
  apt-get install -y ansible sshpass
  exit                                                                          
  Explanation                                                                   
  - docker exec -u root -it jenkins bash opens a shell inside the Jenkins
  container as the root user.                                                   
  - ansible is required to run playbooks.                                       
  - sshpass allows password-based SSH authentication.
                                                                                
  3.3: Verify Jenkins Can Reach the Production Server                           
   
  Before running the pipeline, confirm that Jenkins can connect to the          
  production container through SSH.
                                                                                
  From inside the Jenkins container, test the connection:                       
  ssh -p 2222 <username>@host.docker.internal
                                                                                
  3.4: Configure the Ansible Inventory
                                                                                
  Create an Ansible inventory file that points to the production server         
  container.                                                                    
  [prod]                                                                        
  petclinic-prod ansible_host=petclinic-prod ansible_port=22
  ansible_user=deployer ansible_password=deployer ansible_connection=ssh
  Explanation                                                                   
  - ansible_host=host.docker.internal allows the Jenkins container to reach the
  host machine                                                                  
  - ansible_port=22 points to the mapped SSH port of the production container   
  - ansible_user and ansible_password are the SSH login credentials inside the
  production server container                                                   
                                                                                
  3.5: Create the Ansible Playbook
                                                                                
  The playbook contains the deployment steps executed by Jenkins.
                                                                                
  Responsibilities of the playbook include:                                     
   
  - connecting to the production container                                      
  - copying deployment files or pulling the newest code
  - restarting the application or container                                     
  - confirming the service is running
                                                                                
  3.6: Configure the Jenkins Pipeline
                                                                                
  The Jenkins pipeline is set up to automatically run after each commit to run  
  Ansible deployment playbook
                                                                                
  3.7: Verify Successful Deployment

  After the pipeline finishes successfully, open the application in a browser:  
  http://localhost:8082
  If the deployment succeeded, the updated Spring Petclinic application should  
  be visible there.
                                                                                
  ---
  4. Set Up Prometheus                                                          
                      
  Prometheus is already started by docker compose up and pre-configured to
  scrape Jenkins metrics via prometheus/prometheus.yml. No manual configuration 
  is required.
                                                                                
  4.1 Verify Prometheus is Scraping Jenkins                                     
   
  1. Open http://localhost:9090                                                 
  2. Click Status → Targets
  3. Confirm that the jenkins target shows UP
                                                                                
  If the Jenkins target shows DOWN, make sure the Prometheus metrics plugin is  
  installed in Jenkins (see Section 1.2) and that Jenkins is fully started.     
                                                                                
  4.2 Enable the Prometheus Metrics Endpoint in Jenkins                         
   
  1. In Jenkins, go to Manage Jenkins → System                                  
  2. Scroll down to Prometheus section
  3. Confirm the endpoint is enabled at /prometheus/ (this should already be
  active after installing the plugin)                                           
  4. Click Save
                                                                                
  You can manually verify the metrics endpoint is live:                         
  curl http://localhost:8080/prometheus/
  You should see a long list of metrics in plain text.                          
                                                                                
  ---
  5. Set Up Grafana                                                             
                   
  Grafana is already started by docker compose up and provisioned with a        
  Prometheus data source via grafana/provisioning/.                             
   
  5.1 Log In                                                                    
                  
  Open http://localhost:3000 and log in with the default credentials:
  - Username: admin
  - Password: admin

  5.2 Verify the Prometheus Data Source                                         
   
  1. Go to Connections → Data sources                                           
  2. Confirm Prometheus is listed and click on it
  3. Scroll down and click Save & test — you should see "Data source is working"
                                                                                
  If Prometheus is not listed:                                                  
  1. Click Add data source → Prometheus                                         
  2. Set Prometheus server URL to http://prometheus:9090
  3. Click Save & test                                  
                                                                                
  ▎ Important: Use http://prometheus:9090 (not localhost:9090) because Grafana 
  ▎ communicates with Prometheus inside the Docker network.                     
                  
  5.3 Import the Jenkins Dashboard                                              
                  
  1. In Grafana, go to Dashboards → Import                                      
  2. In the Import via grafana.com field, enter dashboard ID 9964 (Jenkins:
  Performance and Health Overview) and click Load                               
  3. Select your Prometheus data source from the dropdown
  4. Click Import                                                               
                  
  The dashboard will now display Jenkins build durations, queue lengths,        
  executor usage, and other pipeline metrics in real time.
                                                                                
  ---             
  6. Dastardly (Burp Suite) Security Scan
                                                                                
  Dastardly is an automated DAST scanner from PortSwigger (the makers of Burp
  Suite). It is already integrated into the Jenkinsfile and runs automatically  
  as part of the pipeline after the SonarQube Quality Gate.
                                                                                
  No manual setup is required. The pipeline handles everything:                 
   
  1. Packages the application into a JAR                                        
  2. Builds a disposable runtime Docker image
  (docker/petclinic-runtime.Dockerfile)                                         
  3. Starts a temporary petclinic-qa container on an isolated Docker network
  4. Runs the Dastardly scanner against http://petclinic-qa:8080/               
  5. Archives the scan report (dastardly-reports/dastardly-report.xml) and log
  as Jenkins artifacts                                                          
                  
  6.1 View the Scan Report                                                      
                  
  After a pipeline run completes:                                               
  1. Open the build in Jenkins
  2. Click Artifacts in the left sidebar                                        
  3. Download or view dastardly-reports/dastardly-report.xml
                                                                                
  ▎ Note: Dastardly findings currently do not fail the pipeline (report-only    
  ▎ mode). The exit code is captured and logged so you can review findings      
  ▎ without blocking deployments.                                               
                                                                                
  ---             
  7. Trigger the Full Pipeline
                                                                                
  Once all services are configured, trigger a complete end-to-end run:
                                                                                
  1. Make a visible code change, for example edit the welcome message in        
  src/main/resources/templates/welcome.html
  2. Commit and push to your branch:                                            
  git add .       
  git commit -m "test: trigger pipeline with welcome message change"            
  git push                                                          
  3. Jenkins polls the repository approximately every minute and will           
  automatically start a new build                                               
  4. Open http://localhost:8080 and watch the pipeline progress in Blue Ocean   
                                                                                
  Expected pipeline stages:                                                     
  Checkout → Build and Test → SonarQube Analysis → Quality Gate
  → Package for DAST → Build QA Image → Start QA Target                         
  → Run Dastardly Scan → Archive Results → Package → Deploy to Prod             
   
  5. After the pipeline completes, verify the change is live at                 
  http://localhost:8082
                                                                                
  ---             
  Service Summary
                                                                                
  ┌────────────┬───────────────────────┬────────────────────────┐     
  │  Service   │          URL          │  Default Credentials   │               
  ├────────────┼───────────────────────┼────────────────────────┤               
  │ Jenkins    │ http://localhost:8080 │ set during setup       │
  ├────────────┼───────────────────────┼────────────────────────┤               
  │ SonarQube  │ http://localhost:9000 │ admin / admin          │
  ├────────────┼───────────────────────┼────────────────────────┤               
  │ Prometheus │ http://localhost:9090 │ none required          │
  ├────────────┼───────────────────────┼────────────────────────┤               
  │ Grafana    │ http://localhost:3000 │ admin / admin          │
  ├────────────┼───────────────────────┼────────────────────────┤               
  │ Production │ http://localhost:8082 │ (deployed application) │
  └────────────┴───────────────────────┴────────────────────────┘               
                  
