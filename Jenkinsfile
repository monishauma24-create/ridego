pipeline {
    agent any

    environment {
        // CHANGE THIS: Replace 'ubuntu' with the actual username of the account 
        // where you ran 'minikube start' on your server.
        MINIKUBE_HOME = '/home/ubuntu'
        KUBECONFIG    = '/home/ubuntu/.kube/config'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Backend Image') {
            steps {
                sh 'docker build -t backend-docker:latest ./backend'
            }
        }

        stage('Build Frontend Image') {
            steps {
                sh 'docker build -t frontend-docker:latest ./frontend'
            }
        }

        stage('Load Images into Minikube') {
            steps {
                // Jenkins can now find the cluster thanks to MINIKUBE_HOME
                sh 'minikube image load backend-docker:latest'
                sh 'minikube image load frontend-docker:latest'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                // You can apply the entire directory at once to keep it clean
                sh 'kubectl apply -f k8s/'
            }
        }

        stage('Verify Deployment') {
            steps {
                sh 'kubectl get pods'
                sh 'kubectl get services'
            }
        }
    }
}
