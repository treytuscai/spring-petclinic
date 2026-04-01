pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    parameters {
        booleanParam(name: 'RUN_SONARQUBE', defaultValue: false, description: 'Run SonarQube analysis if SONAR_TOKEN is configured.')
        booleanParam(name: 'RUN_BURP_REVIEW', defaultValue: true, description: 'Run the Burp Community manual review gate.')
        booleanParam(name: 'RUN_DEPLOY', defaultValue: false, description: 'Run the Ansible deploy stage if ansible assets exist.')
    }

    environment {
        MAVEN_OPTS = '-Djava.awt.headless=true'
        COMPOSE_PROFILES = 'devsecops,qa'
        QA_TARGET_URL = 'http://petclinic-qa:8080/'
        BURP_UI_URL = 'http://localhost:6080/vnc.html'
        BURP_SHARED_DIR = '/burp-artifacts'
        BURP_WORKSPACE_DIR = 'burp-artifacts'
        SONAR_HOST_URL = 'http://sonarqube:9000'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Test') {
            steps {
                sh 'chmod +x mvnw scripts/wait-for-url.sh'
                sh './mvnw --batch-mode clean test'
            }
        }

        stage('Package') {
            steps {
                sh './mvnw --batch-mode package -DskipTests'
            }
        }

        stage('SonarQube Analysis') {
            when {
                expression { return params.RUN_SONARQUBE }
            }
            steps {
                sh '''
                    if [ -z "${SONAR_TOKEN:-}" ]; then
                      echo "SONAR_TOKEN is required when RUN_SONARQUBE=true."
                      exit 1
                    fi

                    ./mvnw --batch-mode sonar:sonar \
                      -DskipTests \
                      -Dsonar.projectKey=spring-petclinic \
                      -Dsonar.host.url=${SONAR_HOST_URL} \
                      -Dsonar.token=${SONAR_TOKEN}
                '''
            }
        }

        stage('Start QA Target') {
            steps {
                sh '''
                    docker compose --profile qa up -d postgres
                    docker compose --profile qa build petclinic-qa
                    docker compose --profile qa up -d petclinic-qa
                    ./scripts/wait-for-url.sh "${QA_TARGET_URL}" 90
                '''
            }
        }

        stage('Start Burp Community Desktop') {
            when {
                expression { return params.RUN_BURP_REVIEW }
            }
            steps {
                sh 'docker compose --profile devsecops up -d burp'
            }
        }

        stage('Burp Community Review') {
            when {
                expression { return params.RUN_BURP_REVIEW }
            }
            steps {
                input message: """Complete the Burp Community review before continuing.

QA target: ${env.QA_TARGET_URL}
Burp UI: ${env.BURP_UI_URL}
Shared artifact directory inside Burp: /workspace/burp-artifacts
Required evidence files: summary.html and notes.md

Resume this pipeline only after the Burp evidence bundle has been saved.""", ok: 'Burp Review Complete'
            }
        }

        stage('Collect and Validate Burp Evidence') {
            when {
                expression { return params.RUN_BURP_REVIEW }
            }
            steps {
                sh '''
                    rm -rf "${BURP_WORKSPACE_DIR}"
                    mkdir -p "${BURP_WORKSPACE_DIR}"
                    cp -R "${BURP_SHARED_DIR}/." "${BURP_WORKSPACE_DIR}/"

                    test -f "${BURP_WORKSPACE_DIR}/summary.html"

                    if [ ! -f "${BURP_WORKSPACE_DIR}/notes.md" ] && [ ! -f "${BURP_WORKSPACE_DIR}/notes.txt" ]; then
                      echo "Missing Burp notes file."
                      exit 1
                    fi
                '''
            }
        }

        stage('Publish Burp Evidence') {
            when {
                expression { return params.RUN_BURP_REVIEW }
            }
            steps {
                archiveArtifacts allowEmptyArchive: false, artifacts: 'burp-artifacts/**'
                publishHTML(target: [
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'burp-artifacts',
                    reportFiles: 'summary.html',
                    reportName: 'Burp Community Evidence'
                ])
            }
        }

        stage('Deploy to Production') {
            when {
                allOf {
                    expression { return params.RUN_DEPLOY }
                    expression { return fileExists('ansible/deploy.yml') && fileExists('ansible/inventory.ini') }
                }
            }
            steps {
                sh 'ANSIBLE_HOST_KEY_CHECKING=False ansible-playbook -i ansible/inventory.ini ansible/deploy.yml'
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'target/surefire-reports/*.xml'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'target/*.jar'
        }

        cleanup {
            sh 'docker compose --profile qa rm -sf petclinic-qa >/dev/null 2>&1 || true'
        }
    }
}
