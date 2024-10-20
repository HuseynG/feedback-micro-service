pipeline {
    agent any

    stages {
        stage('Verify Docker') {
            steps {
                // Check if Docker is accessible from the host machine
                sh 'docker --version'
            }
        }

        stage('List Docker Containers') {
            steps {
                // List running Docker containers to ensure access to host Docker
                sh 'docker ps'
            }
        }
    }
}
