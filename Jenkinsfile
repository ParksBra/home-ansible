def setup_env_vars(controller_ssh_user, controller_ssh_key_path, worker_ssh_user, worker_ssh_key_path, infisical_identity_client_id, infisical_identity_secret) {
    env.CONTROLLER_SSH_USER = controller_ssh_user
    env.CONTROLLER_SSH_KEY_PATH = controller_ssh_key_path
    
    env.WORKER_SSH_USER = worker_ssh_user
    env.WORKER_SSH_KEY_PATH = worker_ssh_key_path

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
        string(
            name: 'PYTHON_MASTER_ENVIRONMENT',
            defaultValue: '/opt/master-venv/bin/python3',
            description: 'Path to the Python interpreter for setting up the virtual environment. Used to save time for large libraries.'
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
            credentialType: 'com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey',
            description: 'SSH key for accessing the controller hosts'
        )
        credentials(
            name: 'WORKER_SSH_KEY',
            credentialType: 'com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey',
            description: 'SSH key for accessing the worker hosts'
        )
        string(
            name: 'INFISCAL_URL',
            defaultValue: 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl'
        )
        credentials(
            name: 'INFISICAL_IDENTITY',
            credentialType: 'com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl',
            description: 'Infisical service identity for universal authentication'
        )
        credentials(
            name: 'INFISCAL_PROJECT_ID',
            credentialsType: 'org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl',
            description: 'Infisical project ID, normally UUID'
        )
        choice(
            name: 'INFISCAL_ENVIRONMENT_SLUG',
            defaultValue: 'prod',
            choices: ['prod', 'dev', 'staging'],
            description: 'Infisical environment, e.g. prod, dev, staging'
        )
    }

    stages {
        stage('setup-environment') {
            steps {
                echo 'Preparing environment...'
                script {
                    sh "${params.PYTHON_MASTER_ENVIRONMENT} -m venv ${WORKSPACE}/.venv"
                    sh "${WORKSPACE}/.venv/bin/pip install --no-cache-dir --upgrade pip"
                    sh "${WORKSPACE}/.venv/bin/pip install --no-cache-dir -r requirements.txt"
                    sh "${WORKSPACE}/.venv/bin/ansible-galaxy install -r ${WORKSPACE}/roles/requirements.yml"
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
                            timeout(time: 5, unit: 'MINUTES') {
                                input(id: 'validation_failure_input', message: 'Would you like to still proceed?')
                                unstable("Proceeding despite validation failure on main branch.")
                            }
                        } else {
                            unstable("Allowing to proceed on non-main branch.")
                        }
                    }
                }
            }
        }
        stage('make-k8s-cluster') {
            steps {with
                withCredentials([sshUserPrivateKey(credentialsId: params.CONTROLLER_SSH_KEY, usernameVariable: 'controller_ssh_user', keyFileVariable: 'controller_ssh_key_path'), sshUserPrivateKey(credentialsId: params.WORKER_SSH_KEY, usernameVariable: 'worker_ssh_user', keyFileVariable: 'worker_ssh_key_path'), usernamePassword(credentialsId: params.INFISICAL_IDENTITY, usernameVariable: 'infisical_identity_client_id', passwordVariable: 'infisical_identity_secret')]) {
                    echo 'Running make_cluster Ansible playbook...'
                    setup_env_vars(controller_ssh_user, controller_ssh_key_path, worker_ssh_user, worker_ssh_key_path, infisical_identity_client_id, infisical_identity_secret)
                    script {
                        sh "${WORKSPACE}/.venv/bin/ansible-playbook '${WORKSPACE}/playbooks/make_cluster.yml' ${ansible_opts}"
                    }
                }
            }
        }
        stage('make-cluster-storage') {
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: params.CONTROLLER_SSH_KEY, usernameVariable: 'controller_ssh_user', keyFileVariable: 'controller_ssh_key_path'), sshUserPrivateKey(credentialsId: params.WORKER_SSH_KEY, usernameVariable: 'worker_ssh_user', keyFileVariable: 'worker_ssh_key_path'), usernamePassword(credentialsId: params.INFISICAL_IDENTITY, usernameVariable: 'infisical_identity_client_id', passwordVariable: 'infisical_identity_secret')]) {
                    echo 'Running setup_addons Ansible playbook on workers...'
                    setup_env_vars(controller_ssh_user, controller_ssh_key_path, worker_ssh_user, worker_ssh_key_path, infisical_identity_client_id, infisical_identity_secret)
                    script {
                        sh "${WORKSPACE}/.venv/bin/ansible-playbook '${WORKSPACE}/playbooks/make_cluster_storage.yml' ${ansible_opts}"
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
