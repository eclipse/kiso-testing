pipeline
{
    agent
    {
        kubernetes
        {
            containerTemplate
            {
                name 'kiso-build-env'
                image 'eclipse/kiso-build-env:v0.1.0'
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
                sh 'poetry install'
            }
        }
        stage('Format check')
        {
            steps
            {
                script
                {
                    sh "poetry run black --diff . > ${env.WORKSPACE}/black.patch"

                    final def patch = readFile("${env.WORKSPACE}/black.patch")

                    if (patch != "") {
                        echo patch
                        error("Changes in commit do not follow black rules. Consider applying black.patch.")
                    } else {
                        sh "rm ${env.WORKSPACE}/black.patch"
                    }
                }
            }
        }
        stage('Run unittests')
        {
            options
            {
                timeout(time: 10, unit: 'MINUTES')
            }
            steps
            {
                sh 'poetry run pytest --junitxml=reports/testReport.xml'
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
        stage('Run Zephyr test')
        {
            steps
            {
                sh '''mkdir zephyr-project
                    cd zephyr-project
                    west init .
                    west update
                    west zephyr-export
                    export PATH=$PATH:`pwd`/zephyr/scripts/
                    cd ..
                    poetry run pip3 install colorama ply pyelftools west
                    poetry run pykiso -c examples/zephyr.yaml --log-level DEBUG
                '''
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
        stage('Release')
        {
            when
            {
                buildingTag()
            }
            parallel
            {
                stage('Release package')
                {
                    steps
                    {
                        script
                        {
                            withCredentials([string(
                                credentialsId: 'pypi-bot-token',
                                variable: 'token')])
                                {
                                    sh "poetry publish \
                                            --no-interaction \
                                            --build \
                                            --username __token__\
                                            --password ${token}"
                                }
                        }
                    }
                }
            } // parallel
        } // Release
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
