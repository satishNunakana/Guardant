// USE THE CORRECT LIBRARY TO BUILD FROM. FOR A TAGGED VERSION TO BE BUILD USE THE CORRESPONDING VERSION of shared library.
library "common-code@${'master'}" _

pipeline {
    agent { label 'build_machine' }

    environment {
        REGISTRY = globals.get_docker_internal_artifactory_repository()
        PRODUCTION_REGISTRY = globals.get_docker_production_artifactory_repository()
        GIT_BRANCH = utility.get_git_branch_edited(env.BRANCH_NAME)
        IMAGE_NAME = "${REGISTRY}/csas:${GIT_BRANCH}_${env.BUILD_NUMBER}"
        FINAL_IMAGE = "${REGISTRY}/csas:${GIT_BRANCH}_latest"
        NUM_OLD_BUILDS = globals.get_num_oldbuild()
    }

    options {
        buildDiscarder(logRotator(numToKeepStr:env.NUM_OLD_BUILDS))
    }

    stages {
        stage('CheckNode') {
            steps {
                isUnix()
            }
        }
    	stage('Build') {
            steps {
                script {
                    utility.login_docker_internal_artifactory_repository()
                    sh """
                        echo v`git describe --all|awk -F/ '{print \$NF}'`-`git rev-list --count HEAD`-`git log -1 --oneline | cut -d' ' -f1` > VERSION.txt
                    """
                    withCredentials(
                        [usernamePassword(
                                credentialsId: 'artifactory_serviceuser',
                                passwordVariable: 'REPO_PASSWORD',
                                usernameVariable: 'REPO_USERNAME')]) {
                                    sh '''
                                        docker build --build-arg ARTIFACTORY_USERNAME=${REPO_USERNAME} --build-arg ARTIFACTORY_PASSWORD=${REPO_PASSWORD} -t ${IMAGE_NAME} .
                                    '''
                                }
                }
            }
        }
        stage('Unit Tests') {
            steps {
                script {
                    sh """
                        echo 'tests need improvements'
                    """
                }
            }
        }
        stage('Push') {
            steps {
                script {
                    utility.login_docker_internal_artifactory_repository()
                    sh """
                        docker push ${IMAGE_NAME}
                        docker tag ${IMAGE_NAME} ${FINAL_IMAGE}
                        docker push ${FINAL_IMAGE}
                    """
                }
            }
        }
        stage ('Push Production Container') {
            when {
                expression { return ((env.BRANCH_NAME ==~ /.*-RLS\d*/) || env.BRANCH_NAME ==~ /.*-RC\d+/) }
            }
            steps {
                script {
                    utility.login_docker_internal_artifactory_repository()
                    sh (
                        """
                        docker tag ${IMAGE_NAME} ${PRODUCTION_REGISTRY}/csas:${GIT_BRANCH}
                        docker push ${PRODUCTION_REGISTRY}/csas:${GIT_BRANCH}
                        """
                    )
                }
            }
        }
    }
    post {

        success {
            sendNotifications 'SUCCESS'
        }
        failure {
            sendNotifications 'FAILED'
            emailext (
                    subject: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
                    body: """<p>FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</p>
                        <p>Check console output at "<a href="${env.BUILD_URL}">${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>"</p>""",
                    recipientProviders: [[$class: 'CulpritsRecipientProvider']]
            )
        }
    }
}
