pipeline
{
    agent
    {
        kubernetes
        {
            containerTemplate
            {
                name 'kiso-build-env'
                image 'eclipse/kiso-build-env:v0.2.1'
                alwaysPullImage 'true'
                ttyEnabled true
                resourceRequestCpu '2'
                resourceLimitCpu '2'
                resourceRequestMemory '2Gi'
                resourceLimitMemory '4Gi'
            }
        }
    }
    options
    {
        timeout(time: 2, unit: 'HOURS')
    }
    stages
    {
        stage('Setup Env')
        {
            steps
            {
                // Clean workspace
                cleanWs()
                checkout scm
                // TODO remove once new docker image is available
                sh 'python3 -m pip install poetry'
                sh 'poetry install --all-extras'
            }
        }
        stage('Format check')
        {
            steps
            {
                script
                {
                    sh(label: 'Run ruff', script: '''#!/bin/bash
                                set -exuo pipefail
                                poetry run ruff format . &&
                                git diff > ruff_format.patch
                                ''')

                    final def patch = readFile("${env.WORKSPACE}/ruff_format.patch")

                    if (patch != "") {
                        echo patch
                        error("Changes in commit do not follow format rules. Consider applying ruff_format.patch.")
                    } else {
                        sh "rm ${env.WORKSPACE}/ruff_format.patch"
                    }
                }
            }
        }
        stage('Run unittests with tox')
        {
            options
            {
                timeout(time: 20, unit: 'MINUTES')
            }
            steps
            {
                sh 'poetry run tox -v run'
            }
        }
        stage('Run virtual-test')
        {
            steps
            {
                // Run dummy yaml file
                sh 'poetry run pykiso -c examples/dummy.yaml --junit'
            }
        }
        stage('Generate documentation')
        {
            steps {
                script {
                    sh "poetry run invoke docs"
                }
            }
        }
    } // stages

    post // Called at very end of the script to notify developer and github about the result of the build
    {
        always
        {
            junit 'reports/*.xml'
        }
        success
        {
            cleanWs()
        }
        unstable
        {
            notifyFailed()
        }
        failure
        {
            notifyFailed()
        }
        aborted
        {
            notifyAbort()
        }
    }
} // pipeline


def notifyFailed()
{
    emailext (subject: "Job '${env.JOB_NAME}' (${env.BUILD_NUMBER}) is failing",
                body: "Oups, something went wrong with ${env.BUILD_URL}... We are looking forward for your fix!",
                recipientProviders: [[$class: 'CulpritsRecipientProvider'],
                                    [$class: 'DevelopersRecipientProvider'],
                                    [$class: 'RequesterRecipientProvider']])
}

def notifyAbort()
{
    emailext (subject: "Job '${env.JOB_NAME}' (${env.BUILD_NUMBER}) was aborted",
                body: "Oups, something went wrong with ${env.BUILD_URL}... We are looking forward for your fix!",
                recipientProviders: [[$class: 'CulpritsRecipientProvider'],
                                    [$class: 'DevelopersRecipientProvider'],
                                    [$class: 'RequesterRecipientProvider']])
}
