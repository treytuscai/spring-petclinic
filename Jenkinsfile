pipeline {
    agent any

    triggers {
        pollSCM('* * * * *')  // check the Git repo for changes about every minutes
    }

    options {
        timestamps()    // Adds timestamps to the Jenkins console log.

        disableConcurrentBuilds() // Prevents two builds of this same pipeline from running at the same time
    }

    environment {
        MAVEN_OPTS = '-Djava.awt.headless=true'
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
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'target/surefire-reports/*.xml'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'target/*.jar'
        }
    }
}
