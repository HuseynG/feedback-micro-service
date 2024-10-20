pipeline {
    agent any

    environment {
        DOCKER_COMPOSE_PATH = 'docker-compose.yml'  // Update with the correct path
    }

    stages {
        stage('Verify Docker') {
            steps {
                // Check if Docker is installed on the host machine
                sh 'docker --version'
                sh 'docker-compose --version'
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
                    sh 'docker-compose --version'
                    
                    // Navigate to the correct directory and run Docker Compose
                    dir('feedback-micro-service') {
                        // Stop any existing containers
                        sh "docker-compose -f ${DOCKER_COMPOSE_PATH} down"
                        // Pull the latest images
                        sh "docker-compose -f ${DOCKER_COMPOSE_PATH} pull"
                        // Start the containers in detached mode
                        sh "docker-compose -f ${DOCKER_COMPOSE_PATH} up --build -d"
                    }
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
