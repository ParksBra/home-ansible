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

    env.K8S_FORCE_RESET = params.FORCE_K8S_CLUSTER_RESET.toString()

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
        booleanParam(
            name: 'SKIP_VALIDATION',
            defaultValue: false,
            description: 'Skip validation steps'
        )
        booleanParam(
            name: 'FORCE_K8S_CLUSTER_RESET',
            defaultValue: false,
            description: 'Force reset of the Kubernetes cluster'
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
                    sh "python3 -m venv ${WORKSPACE}/.venv"
                    sh "${WORKSPACE}/.venv/bin/pip install --no-cache-dir --upgrade pip"
                    sh "${WORKSPACE}/.venv/bin/pip install --no-cache-dir -r requirements.txt"
                    sh "${WORKSPACE}/.venv/bin/ansible-galaxy install -r ${WORKSPACE}/roles/requirements.yml --no-cache"
                }
            }
        }
        stage('validate-configuration') {
            when {
                expression { return !params.SKIP_VALIDATION.toBoolean() }
            }
            steps {
                echo 'Validating Ansible playbook syntax...'
                
                    script {
                        try {
                            sh "${WORKSPACE}/.venv/bin/ansible-lint ${WORKSPACE}/playbooks/*.yml"
                        } catch (err) {
                        echo "Ansible linting validation failed: ${err}"
                        if (env.BRANCH_NAME == 'main') {
                            timeout(time: 5, unit: 'MINUTES')
                            {
                                def validation_failure_input = input(message: "Would you like to still proceed?")
                                if (validation_failure_input != 'Proceed') {
                                    error("Build aborted due to validation failure.")
                                } else {
                                    unstable("Proceeding despite validation failure on main branch.")
                                }
                            }
                        } else {
                            unstable("Allowing to proceed on non-main branch.")
                        }
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
                        sh "${WORKSPACE}/.venv/bin/ansible-playbook '${WORKSPACE}/playbooks/make_controller.yml' -l 'k8s_controller' ${ansible_opts}"
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
                        sh "${WORKSPACE}/.venv/bin/ansible-playbook '${WORKSPACE}/playbooks/make_worker.yml' -l 'k8s_worker' ${ansible_opts}"
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
