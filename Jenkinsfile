
pipeline {
    agent any

    stages {
        stage('clone') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/monishauma24-create/ridego.git'
            }
        }

        stage('Build frontend') {
            steps {
                sh '''
                cd frontend
                docker build -t monisha243/frontend:latest .
                '''
            }
        }

        stage('Build backend') {
            steps {
                sh '''
                cd backend
                docker build -t monisha243/backend:latest .
                '''
            }
        }

        stage('Docker push') {
            steps {
                sh '''
                docker push monisha243/frontend:latest
                docker push monisha243/backend:latest
                '''
            }
        }

        stage('Deploy kubernetes') {
            steps {
                sh '''
                kubectl apply -f k8s/
                '''
            }
        }
    }
}
