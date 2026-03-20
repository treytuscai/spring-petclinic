pipeline {
    agent any

    triggers {
        pollSCM('H/1 * * * *')  // check the Git repo for changes about every 5 minutes
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
    }

    post {
        always {
            junit allowEmptyResults: true, testResults: 'target/surefire-reports/*.xml'
            archiveArtifacts allowEmptyArchive: true, artifacts: 'target/*.jar'
        }
    }
}
