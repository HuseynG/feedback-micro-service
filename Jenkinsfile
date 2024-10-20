pipeline {
    agent any

    environment {
        DOCKER_COMPOSE_PATH = 'docker-compose.yml'  // Update with the correct path
    }

    stages {
        stage('Verify Docker') {
            steps {
                // Check if Docker is installed
                sh 'docker --version'
            }
        }

        stage('Checkout') {
            steps {
                script {
                    // Use Jenkins credentials to inject the GitHub PAT
                    withCredentials([string(credentialsId: 'GITHUB_TOKEN', variable: 'GITHUB_PAT')]) {
                        // Clone the repository using the token stored in GITHUB_PAT
                        sh "git clone https://$GITHUB_PAT@github.com/jobassist-micro-services/feedback-micro-service.git"
                    }
                }
            }
        }

        stage('Build and Run Docker Compose') {
            steps {
                script {
                    // Ensure Docker is running
                    sh 'docker --version'
                    // Run Docker Compose to pull latest images and start the containers
                    sh "docker-compose -f ${DOCKER_COMPOSE_PATH} down"  // Stop any existing containers
                    sh "docker-compose -f ${DOCKER_COMPOSE_PATH} pull"  // Pull the latest images
                    sh "docker-compose -f ${DOCKER_COMPOSE_PATH} up --build -d"  // Start the containers in detached mode
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline complete.'
        }
    }
}
