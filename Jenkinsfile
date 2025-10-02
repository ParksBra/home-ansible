def setup_env_vars(controller_ssh_user='', controller_ssh_key_path='', worker_ssh_user='', worker_ssh_key_path='') {
    env.CONTROLLER_SSH_USER = controller_ssh_user
    env.CONTROLLER_SSH_KEY_PATH = controller_ssh_key_path
    env.WORKER_SSH_USER = worker_ssh_user
    env.WORKER_SSH_KEY_PATH = worker_ssh_key_path
    env.INFISCAL_API_URL = params.INFISCAL_API_URL
    env.INFISCAL_API_KEY = params.INFISCAL_API_KEY
    env.INFISCAL_WORKSPACE_ID = params.INFISCAL_WORKSPACE_ID
    env.INFISCAL_ENVIRONMENT = params.INFISCAL_ENVIRONMENT
    env.GIT_BRANCH = params.BRANCH
    env.DEBUG = params.DEBUG
}

pipeline {
    agent any
    parameters {
        gitParameter(
            type: 'BRANCH',
            name: 'BRANCH',
            description: 'Choose a branch to checkout',
            branchFilter: 'origin/(.*)',
            defaultValue: 'main',
            selectedValue: 'DEFAULT',
            sortMode: 'DESCENDING_SMART'
        )
        string(
            name: 'CONTROLLER_SSH_KEY',
            defaultValue: 'ansible-ssh-key',
            description: 'Name of stored SSH key secret file for accessing the target servers'
        )
        string(
            name: 'WORKER_SSH_KEY',
            defaultValue: 'ansible-ssh-key',
            description: 'Name of stored SSH key secret file for accessing the target servers'
        )
        string(
            name: 'INFISCAL_API_URL',
            defaultValue: 'http://localhost/api/v3'
        )
        password(
            name: 'INFISCAL_API_KEY',
            defaultValue: 'password',
            description: 'Infisical key for accessing secret values'
        )
        string(
            name: 'INFISCAL_PROJECT_ID',
            defaultValue: '',
            description: 'Infisical project ID, normally UUID'
        )
        string(
            name: 'INFISCAL_ENVIRONMENT',
            defaultValue: 'prod',
            description: 'Infisical environment, e.g. prod, dev, staging'
        )
        booleanParam(
            name: 'DEBUG',
            defaultValue: false,
            description: 'Enable debug logging and display of secrets'
        )
    }
    triggers {
        // pollSCM('* * * * *')
    }

    stages {
        stage('setup-environment') {
            steps {
                echo 'Preparing environment...'
                setup_env_vars()
                script {
                    sh 'python3 -m venv .venv'
                    sh '.venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt'
                }
            }
        }
        stage('make-controller') {
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: params.CONTROLLER_SSH_KEY, usernameVariable: 'controller_ssh_user', keyFileVariable: 'controller_ssh_key_path')]) {
                    echo 'Running make_server Ansible playbook on controller...'
                    setup_env_vars(controller_ssh_user=controller_ssh_user, controller_ssh_key_path=controller_ssh_key_path)
                    script {
                        sh ".venv/bin/ansible-playbook 'playbooks/make_controller.yml' -l 'k8s-controller'"
                    }
                }
            }
        }
        stage('make-workers') {
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: params.WORKER_SSH_KEY, usernameVariable: 'worker_ssh_user', keyFileVariable: 'worker_ssh_key_path')]) {
                    echo 'Running make_server Ansible playbook on workers...'
                    setup_env_vars(worker_ssh_user=worker_ssh_user, worker_ssh_key_path=worker_ssh_key_path)
                    script {
                        sh ".venv/bin/ansible-playbook 'playbooks/make_worker.yml' -l 'k8s-worker'"
                    }
                }
            }
        }
    }
    // Post work actions
    post {
        success {
            echo "${params.STACK_NAME} ${BUILD_TAG} Completed Successfully"
        }
        always {
            sh(script: "rm -rf ${env.TF_DIR}/")
        }
    }
}
