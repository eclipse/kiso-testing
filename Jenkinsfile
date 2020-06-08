pipeline
{
    agent
    {
        kubernetes
        {
            containerTemplate
            {
                name 'kiso-build-env'
                image 'eclipse/kiso-build-env:v0.0.5'
                alwaysPullImage 'true'
                ttyEnabled true
                resourceRequestCpu '2'
                resourceLimitCpu '2'
                resourceRequestMemory '8Gi'
                resourceLimitMemory '8Gi'
            }
        }
    }

    stages
    {
        stage('Setup Env')
        {
            steps
            {
                script
                {
                    echo "Build Pipenv"
                    sh 'pipenv --python 3'
                    sh 'pipenv install --dev'
                }
            }
        }
        stage('Format check')
        {
            steps
            {
                script
                {
                    echo "Run different format checks: TODO"
                }
            }
        }
        stage('Run unittests')
        {
            steps
            {
                script
                {
                    echo "Run all the unittests"
                    sh 'pipenv run invoke unittest'
                    // TODO: call coverage report + save it
                }
            }
        }
        stage('Run virtual-test')
        {
            steps
            {
                script
                {
                    echo "Run a virtual communication: TODO"
                }
            }
        }
        stage('Generate documentation')
        {
            steps
            {
                script
                {
                    echo "Generate documentation"
                    sh 'pipenv run invoke docs'
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
                stage('Release documentation')
                {
                    steps
                    {
                        script
                        {
                            echo "Release documentation on readthedocs.org: TODO"
                        }
                    }
                }
                stage('Release package')
                {
                    steps
                    {
                        script
                        {
                            echo "Release package on PyPI.org: TODO"
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
            archiveArtifacts (
                artifacts: 'TBD',
                fingerprint: true
            )
            junit (
                allowEmptyResults: true,
                testResults: 'TBD'
            )
        }
        success
        {
            archiveArtifacts (
                artifacts: 'builddir-debug/docs/doxygen/**, builddir-unittests/*_cov/**, docs/website/public/**/*',
                fingerprint: true
            )
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
