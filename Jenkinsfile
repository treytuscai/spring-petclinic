pipeline {
    agent any

    triggers {
        pollSCM('* * * * *')  // check the Git repo for changes about every minutes
    }

    options {
        disableConcurrentBuilds() // Prevents two builds of this same pipeline from running at the same time
    }

    environment {
        MAVEN_OPTS = '-Djava.awt.headless=true'
        DASTARDLY_IMAGE = 'public.ecr.aws/portswigger/dastardly:latest'
        DASTARDLY_DOCKER_NETWORK = 'petclinic-dast'
        DASTARDLY_TARGET_URL = 'http://petclinic-qa:8080/'
        DASTARDLY_REPORT_DIR = 'dastardly-reports'
        DASTARDLY_REPORT_FILE = 'dastardly-reports/dastardly-report.xml'
        DASTARDLY_LOG_FILE = 'dastardly-reports/dastardly.log'
        DASTARDLY_EXIT_CODE_FILE = 'dastardly-reports/dastardly.exitcode'
        DASTARDLY_CONTAINER = 'dastardly-scan'
        PETCLINIC_QA_CONTAINER = 'petclinic-qa'
        PETCLINIC_QA_IMAGE = 'spring-petclinic:dast'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm // pull the repo code into the Jenkins workspace
            }
        }

        stage('Build and Test') {
            steps {
                sh 'chmod +x mvnw'
                sh './mvnw --batch-mode clean test'
            }
        }
        stage('SonarQube Analysis') {
            steps {
                withSonarQubeEnv('SonarQube') {
                    sh '''
                    ./mvnw sonar:sonar \
                        -Dsonar.projectKey=spring-petclinic
                    '''
                }
            }
        }
        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Package for DAST') {
            steps {
                sh './mvnw --batch-mode package -DskipTests'
            }
        }

        stage('Build QA Runtime Image') {
            steps {
                sh '''
                    docker build \
                      --build-arg APP_JAR=target/spring-petclinic-4.0.0-SNAPSHOT.jar \
                      --file docker/petclinic-runtime.Dockerfile \
                      --tag "${PETCLINIC_QA_IMAGE}" \
                      .
                '''
            }
        }

        stage('Start QA Target') {
            steps {
                sh '''
                    docker rm -f "${PETCLINIC_QA_CONTAINER}" >/dev/null 2>&1 || true
                    docker network rm "${DASTARDLY_DOCKER_NETWORK}" >/dev/null 2>&1 || true

                    docker network create "${DASTARDLY_DOCKER_NETWORK}" >/dev/null
                    docker run -d \
                      --name "${PETCLINIC_QA_CONTAINER}" \
                      --network "${DASTARDLY_DOCKER_NETWORK}" \
                      "${PETCLINIC_QA_IMAGE}" >/dev/null

                    timeout_seconds=120
                    elapsed=0

                    while [ "${elapsed}" -lt "${timeout_seconds}" ]; do
                      status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${PETCLINIC_QA_CONTAINER}")

                      if [ "${status}" = "healthy" ]; then
                        exit 0
                      fi

                      if [ "${status}" = "exited" ] || [ "${status}" = "dead" ]; then
                        docker logs "${PETCLINIC_QA_CONTAINER}" || true
                        exit 1
                      fi

                      sleep 5
                      elapsed=$((elapsed + 5))
                    done

                    docker logs "${PETCLINIC_QA_CONTAINER}" || true
                    exit 1
                '''
            }
        }

        stage('Run Dastardly Scan') {
            steps {
                sh '''
                    mkdir -p "${DASTARDLY_REPORT_DIR}"
                    chmod 0777 "${DASTARDLY_REPORT_DIR}"
                    rm -f "${DASTARDLY_REPORT_FILE}" "${DASTARDLY_LOG_FILE}" "${DASTARDLY_EXIT_CODE_FILE}"
                    docker rm -f "${DASTARDLY_CONTAINER}" >/dev/null 2>&1 || true

                    set +e
                    docker run --name "${DASTARDLY_CONTAINER}" --rm \
                      --network "${DASTARDLY_DOCKER_NETWORK}" \
                      --user "1000:1000" \
                      --volumes-from "$(hostname)" \
                      --workdir /tmp \
                      -e DASTARDLY_TARGET_URL="${DASTARDLY_TARGET_URL}" \
                      -e DASTARDLY_OUTPUT_FILE="${WORKSPACE}/${DASTARDLY_REPORT_FILE}" \
                      "${DASTARDLY_IMAGE}" \
                      > "${DASTARDLY_LOG_FILE}" 2>&1
                    scan_exit=$?
                    set -e

                    printf '%s' "${scan_exit}" > "${DASTARDLY_EXIT_CODE_FILE}"

                    if [ "${scan_exit}" -ne 0 ]; then
                      echo "Dastardly exited with status ${scan_exit}. Preserving report-only rollout."
                    fi
                '''
            }
        }

        stage('Archive Dastardly Results') {
            steps {
                archiveArtifacts allowEmptyArchive: true, artifacts: 'dastardly-reports/**'
            }
        }
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'target/surefire-reports/*.xml'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'target/*.jar'
        }

        cleanup {
            sh '''
                docker rm -f "${DASTARDLY_CONTAINER}" >/dev/null 2>&1 || true
                docker rm -f "${PETCLINIC_QA_CONTAINER}" >/dev/null 2>&1 || true
                docker network rm "${DASTARDLY_DOCKER_NETWORK}" >/dev/null 2>&1 || true
            '''
        }
    }
}
