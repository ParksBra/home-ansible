def setup_env_vars(ssh_user, ssh_key_path, infisical_identity_client_id, infisical_identity_secret) {
    env.SSH_USER = ssh_user
    env.SSH_KEY_PATH = ssh_key_path

    env.DEBUG = params.DEBUG

    env.INFISCAL_URL = params.INFISCAL_URL
    env.INFISCAL_PROJECT_ID = params.INFISCAL_PROJECT_ID
    env.INFISCAL_ENVIRONMENT = params.INFISCAL_ENVIRONMENT_SLUG
    env.INFISICAL_UNIVERSAL_AUTH_CLIENT_ID = infisical_identity_client_id
    env.INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET = infisical_identity_secret
    env.INFISICAL_AUTH_METHOD = 'universal_auth'

    def ansible_opts_list = []
    if (params.DEBUG.toBoolean()) {
        ansible_opts_list.add('-v')
    }
    ansible_opts = ansible_opts_list.join(' ')

}

pipeline {
    agent any
    parameters {
        booleanParam(
            name: 'DEBUG',
            defaultValue: false,
            description: 'Enable debug logging and display of secrets'
        )
        credentials(
            name: 'CONTROLLER_SSH_KEY',
            credentialType: 'SSH Username with private key',
            description: 'SSH key for accessing the controller hosts'
        )
        credentials(
            name: 'WORKER_SSH_KEY',
            credentialType: 'SSH Username with private key',
            description: 'SSH key for accessing the worker hosts'
        )
        string(
            name: 'INFISCAL_URL',
            defaultValue: 'http://localhost:80'
        )
        string(
            name: 'INFISCAL_PROJECT_ID',
            description: 'Infisical project ID, normally UUID'
        )
        string(
            name: 'INFISCAL_ENVIRONMENT_SLUG',
            defaultValue: 'prod',
            description: 'Infisical environment, e.g. prod, dev, staging'
        )
        credentials(
            name: 'INFISICAL_IDENTITY',
            credentialType: 'Username with password',
            description: 'Infisical service identity for universal authentication'
        )
    }

    stages {
        stage('setup-environment') {
            steps {
                echo 'Preparing environment...'
                script {
                    sh 'python3 -m venv .venv'
                    sh '.venv/bin/pip install --upgrade pip && .venv/bin/pip install -r requirements.txt'
                    sh '.venv/bin/ansible-galaxy install -r roles/requirements.yml'
                }
            }
        }
        stage('validate-configuration') {
            steps {
                echo 'Validating Ansible playbook syntax...'
                try {
                    script {
                        sh '.venv/bin/ansible-lint playbooks/*.yml'
                    }
                } catch (err) {
                    echo "Ansible linting validation failed: ${err}"
                    timeout(time: 2, unit: 'MINUTES')
                    {
                        input(message: "Would you like to still proceed?")
                    }
                }
            }
        }
        stage('make-k8s-controller') {
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: params.CONTROLLER_SSH_KEY, usernameVariable: 'ssh_user', keyFileVariable: 'ssh_key_path'), usernamePassword(credentialsId: params.INFISICAL_IDENTITY, usernameVariable: 'infisical_identity_client_id', passwordVariable: 'infisical_identity_secret')]) {
                    echo 'Running make_server Ansible playbook on controller...'
                    setup_env_vars(ssh_user, ssh_key_path, infisical_identity_client_id, infisical_identity_secret)
                    script {
                        sh ".venv/bin/ansible-playbook 'playbooks/make_controller.yml' -l 'k8s_controller' ${ansible_opts}"
                    }
                }
            }
        }
        stage('make-k8s-workers') {
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: params.WORKER_SSH_KEY, usernameVariable: 'ssh_user', keyFileVariable: 'ssh_key_path'), usernamePassword(credentialsId: params.INFISICAL_IDENTITY, usernameVariable: 'infisical_identity_client_id', passwordVariable: 'infisical_identity_secret')]) {
                    echo 'Running make_server Ansible playbook on workers...'
                    setup_env_vars(ssh_user, ssh_key_path, infisical_identity_client_id, infisical_identity_secret)
                    script {
                        sh ".venv/bin/ansible-playbook 'playbooks/make_worker.yml' -l 'k8s_worker' ${ansible_opts}"
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
