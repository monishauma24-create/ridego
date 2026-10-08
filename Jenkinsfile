pipeline {
    agent any

    environment {
        // Tells Minikube and kubectl to use Jenkins' own workspace directory,
        // which completely avoids "permission denied" errors in /home/ubuntu.
        MINIKUBE_HOME = "${WORKSPACE}/.minikube"
        KUBECONFIG    = "${WORKSPACE}/.kube/config"
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
                // Starts Minikube within the isolated Jenkins environment block
                sh 'minikube start --driver=docker'
                
                // Loads the newly built local Docker images into Minikube's registry
                sh 'minikube image load backend-docker:latest'
                sh 'minikube image load frontend-docker:latest'
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                // Applies all configuration YAML manifests inside your k8s folder
                sh 'kubectl apply -f k8s/'
            }
        }

        stage('Verify Deployment') {
            steps {
                // Displays status overview to verify successful rollout
                sh 'kubectl get pods'
                sh 'kubectl get services'
            }
        }
    }
}
