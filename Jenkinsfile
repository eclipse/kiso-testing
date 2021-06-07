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
                // Clean workspace
                cleanWs()
                // checkout repo
                checkoutCode()
                // Use pipenv
                sh 'pipenv install --dev'
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
                sh 'pipenv run pytest --junitxml=reports/testReport.xml --ignore tests/test_cc_pcan_can.py'
            }
        }
        stage('Run virtual-test')
        {
            steps
            {
                // Run dummy yaml file
                sh 'pipenv run pykiso -c examples/dummy.yaml --junit'
            }
        }
        stage('Generate documentation')
        {
            steps {
                script {
                    sh "pipenv run invoke docs"
                        publishHTML([
                            allowMissing: false,
                            alwaysLinkToLastBuild: false,
                            keepAll: true,
                            reportDir: 'docs/_build',
                            reportFiles: 'index.html',
                            reportName: 'pykiso documentation',
                            ])
                    zip zipFile: 'pykiso_documentation.zip', archive: true, glob:'docs/_build/**/*.*'
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
                            echo "Release documentation on pypi.org: TODO"
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
            junit 'reports/*.xml'
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
