/* IMPORTANT:
*
* In order to make this pipeline work, the following configuration on Jenkins is required:
* - slave with a specific label (see pipeline.agent.label below)
* - credentials plugin should be installed and have the secrets with the following names:
*   + lciadm100credentials (token to access Artifactory)
*/

def defaultBobImage = 'armdocker.rnd.ericsson.se/proj-adp-cicd-drop/bob.2.0:1.7.0-54'
def bob = new BobCommand()
        .bobImage(defaultBobImage)
        .envVars([ISO_VERSION: '${ISO_VERSION}', PRODUCT_SET: '${PRODUCT_SET}', SPRINT_TAG: '${SPRINT_TAG}'])
        .needDockerSocket(true)
        .toString()

def bobInCA = new BobCommand()
        .bobImage(defaultBobImage)
        .needDockerSocket(true)
        .envVars([
        ARM_API_TOKEN     : '${ARM_CREDENTIALS_PSW}',
        REQUIREMENTS_FILE : '${REQUIREMENTS_FILE}',
        CHART_PATH        : '${CHART_PATH}',
        GIT_REPO_URL      : '${GIT_REPO_URL}',
        HELM_INTERNAL_REPO: '${HELM_INTERNAL_REPO}',
        HELM_DROP_REPO    : '${HELM_DROP_REPO}',
        HELM_RELEASED_REPO: '${HELM_RELEASED_REPO}',
        GERRIT_USERNAME   : '${GERRIT_CREDENTIALS_USR}',
        GERRIT_PASSWORD   : '${GERRIT_CREDENTIALS_PSW}',
        CHART_NAME        : '${CHART_NAME}',
        CHART_VERSION     : '${CHART_VERSION}',
        ALLOW_DOWNGRADE   : '${ALLOW_DOWNGRADE}',
        HELM_REPO_CREDENTIALS : '${HELM_REPO_CREDENTIALS}'
])
        .toString()


def GIT_COMMITTER_NAME = 'enmadm100'
def GIT_COMMITTER_EMAIL = 'enmadm100@ericsson.com'

pipeline {
    agent {
        label 'Cloud-Native'
    }
    parameters {
        string(name: 'SPRINT_TAG', description: 'Tag for GIT tagging the repository after build')
    }
    environment {
        GERRIT_CREDENTIALS = credentials('cenmbuild_gerrit_api_token')
        ARM_CREDENTIALS = credentials('cenmbuild_ARM_token')
        CHART_PATH = "chart/eric-enmsg-fmx-integration"
        REPO = "OSS/ENM-Parent/SQ-Gate/com.ericsson.oss.containerisation/eric-enmsg-fmx-integration"
        GIT_REPO_URL = "${GERRIT_CENTRAL_HTTP}/a/${REPO}"
        HELM_INTERNAL_REPO = "https://arm.epk.ericsson.se/artifactory/proj-enm-dev-internal-helm/"
        HELM_DROP_REPO = "https://arm.epk.ericsson.se/artifactory/proj-enm-dev-internal-helm/"
        HELM_RELEASED_REPO = "https://arm.epk.ericsson.se/artifactory/proj-enm-dev-internal-helm/"
    }
    stages {
        stage('Clean workspace') {
            steps {
                deleteDir()
            }
        }
        stage('Inject Credential Files') {
            steps {
                withCredentials([file(credentialsId: 'lciadm100-docker-auth', variable: 'dockerConfig')]) {
                    sh "install -m 600 ${dockerConfig} ${HOME}/.docker/config.json"
                }
            }
        }
        stage('Checkout Cloud-Native Git Repository') {
            steps {
                git branch: 'master',
                        url: '${GERRIT_MIRROR}/OSS/ENM-Parent/SQ-Gate/com.ericsson.oss.containerisation/eric-enmsg-fmx-integration'
                sh '''
                 git remote set-url origin --push ${GERRIT_CENTRAL}/${REPO}
                   '''
            }
        }
        stage('Init') {
             steps {
                script {
                  hasProductSet = false
                  hasSingleChartUpdate = false
                  hasRequirementsFile = false

                  if (env.REQUIREMENTS_FILE && (env.CHART_VERSION||env.CHART_NAME)){
                      currentBuild.result = "ABORTED"
                      error("Invalid entry: Cannot define Requirements File and Chart")
                  }
                  if ( ( env.CHART_NAME || env.CHART_VERSION ) && ! ( env.CHART_NAME && env.CHART_VERSION ) ) {
                     currentBuild.result = "ABORTED"
                     error("Invalid entry: Chart must have Version and Name")
                  }
                  if (env.REQUIREMENTS_FILE && ! (env.PRODUCT_SET)){
                      currentBuild.result = "ABORTED"
                      error("Invalid entry: Missing PRODUCT_SET variable")
                  }
                  if (env.REQUIREMENTS_FILE){
                      manager.addShortText("Triggered From Central Build", "black", "SteelBlue", "1px", "green")
                      hasRequirementsFile = true
                  } else if (env.CHART_NAME && env.CHART_VERSION){
                      def messageString = "Independent Service Update: "+env.CHART_NAME+":"+ env.CHART_VERSION
                      manager.addShortText(messageString, "black", "LightSeaGreen", "1px", "green")
                      hasSingleChartUpdate = true
                  }
                  if (env.PRODUCT_SET){
                     currentBuild.displayName = "PRODUCT SET ON: ${PRODUCT_SET}"
                     hasProductSet = true
                  }
                }
            }
        }
        stage('Lint Helm') {
            steps {
                sh "${bob} lint-only-helm"
            }
        }
        stage('Update versions in values.yaml file') {
            when {
                expression { hasRequirementsFile == true }
            }
            steps {
                echo sh(script: 'env', returnStdout: true)
                step([$class: 'CopyArtifact', projectName: 'sync-build-trigger', filter: "*"]);
                sh "${bob} swap-latest-versions-with-numbers"
                sh '''
                    if git status | grep 'values.yaml' > /dev/null; then
                        git commit -m "NO JIRA - Updating Values.yaml files with version"
                        git push origin HEAD:master
                    fi
                '''
                //wait for gerrit sync
                checkGerritSync()
            }
        }

        stage('Publish Helm Chart') {
            steps {
                script {
                    if (hasSingleChartUpdate){
                      withCredentials([file(credentialsId: 'cenm_repo_credentials', variable: 'HELM_REPO_CREDENTIALS')]){
                      	sh "chmod -R 777 ${WORKSPACE}@tmp"
                        sh "${bobInCA} publish"
                        }
                    } else {
                      withCredentials([file(credentialsId: 'cenm_repo_credentials', variable: 'HELM_REPO_CREDENTIALS')]){
                    sh "chmod -R 777 ${WORKSPACE}@tmp"
                    sh "${bobInCA} publishwithreq"
                    }
                    }
                    archiveArtifacts 'artifact.properties'
                }
            }
        }

        stage('Update Version prefix') {
            steps {
                script {
                    //temp until VERSION_PREFIX is deprecated in pointfix
                    sh '''
                            git pull origin master
                            . ./artifact.properties
                            echo ${INT_CHART_VERSION} | sed 's/-.*$//' >VERSION_PREFIX
                            if git status | grep 'VERSION_PREFIX' > /dev/null; then
                                git add VERSION_PREFIX
                                git commit -m "Version prefix update"
                                echo "VERSION PREFIX UPDATE"
                            git push origin HEAD:master
                            fi
                        '''
                    //wait for gerrit sync
                    checkGerritSync()
                }
            }
        }
        stage('Update Requirements.yaml file') {
            steps {
                script {
                    sh '''
                            . ./artifact.properties
                            curl "${REQUIREMENTS_FILE}" -o requirements.yaml
                            echo '- name: eric-enmsg-fmx-integration' >> requirements.yaml
                            echo '  repository: https://arm.epk.ericsson.se/artifactory/proj-enm-dev-internal-helm/' >> requirements.yaml
                            echo '  version: '${INT_CHART_VERSION} >> requirements.yaml
                            curl -u \${ARM_CREDENTIALS} -X PUT -T requirements.yaml ${REQUIREMENTS_FILE}
                       '''
                }
            }
        }
    }
    post {
        success {
            script {
                sh '''
                            set +x
                            #ADD tag Cloud-Native to Repository
                            . ./artifact.properties
                            git tag --annotate --message "Tagging Version" --force ${INT_CHART_VERSION}
                            git push --force origin ${INT_CHART_VERSION}
                        '''
                        if (hasProductSet){
                            sh '''
                                git tag --annotate --message "Tagging latest in sprint" --force $SPRINT_TAG HEAD
                                git push --force origin $SPRINT_TAG
                                git tag --annotate --message "Tagging latest in sprint with ISO version" --force ${SPRINT_TAG}_iso_${ISO_VERSION} HEAD
                                git push --force origin ${SPRINT_TAG}_iso_${ISO_VERSION}
                                git tag --annotate --message "Tagging latest in sprint with Product Set version" --force ps_${PRODUCT_SET} HEAD
                                git push --force origin ps_${PRODUCT_SET}
                            '''
                        }

            }
        }
        failure {
            mail to: 'EricssonHyderabad.ENMMisty@tcs.com,EricssonHyderabad.ENMDewdrops@tcs.com',
                    subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                    body: "Failure on ${env.BUILD_URL}"
                    sh "tar -zcf .bob/tmp_repo.tgz .bob/tmp_repo"
                    archiveArtifacts '.bob/tmp_repo.tgz'
        }
    }
}

def checkGerritSync() {
    sh '''
                RETRY=6
                SLEEP=10

                # check if branch was passed as arg, else use Jenkins working branch
                [ -n "$1" ] && branch=$1 || branch=${GIT_BRANCH##*/}

                # get the commit ID's on GC master and mirror
                echo "INFO: Checking commit ID's for '$branch' branch on Gerrit Central."
                gcr=$(git ls-remote -h ${GERRIT_CENTRAL}/${REPO} ${branch} | awk '{print $1}')
                gmr=$(git ls-remote -h ${GERRIT_MIRROR}/${REPO} ${branch} | awk '{print $1}')
                echo "INFO: central: ${gcr}"
                echo "INFO: mirror:  ${gmr}"

                # compare master and mirror
                if [[ "${gcr}" != "${gmr}" ]]; then
                echo "INFO: Gerrit central and mirror are out of sync."
                echo "INFO: Waiting a maximum of $((RETRY*SLEEP)) seconds for sync."

                retry=0
                # retry a number of times
                while (( retry < RETRY )); do
                    echo "INFO: Attempting retry #$((retry+1)) of $RETRY in $SLEEP seconds."
                    sleep $SLEEP

                    gcr=$(git ls-remote -h ${gcu} ${branch} | awk '{print $1}')
                    gmr=$(git ls-remote -h ${gmu} ${branch} | awk '{print $1}')
                    echo "INFO: central: $gcr, mirror: $gmr"

                    # compare master and mirror, again
                    if [ "${gcr}" = "${gmr}" ]; then
                        echo "INFO: fetching latest changes on branch $branch."
                        git fetch
                        break
                    fi

                    ((retry++))
                done
                fi

                # if still out of sync, fail the job
                [ "${gcr}" != "${gmr}" ] && echo "ERROR: Gerrit central and mirror out of sync." && exit 1
                # Check we're on the correct (synced) revision
                [ "${GIT_COMMIT}" != "${gmr}" ] && echo -e "*** WARNING: Not using latest revision.\nFetching upstream changes again from $gmu. ***" && git fetch
                echo "INFO: Branch in sync between Gerrit central and mirror."
            '''
}

// More about @Builder: http://mrhaki.blogspot.com/2014/05/groovy-goodness-use-builder-ast.html
import groovy.transform.builder.Builder
import groovy.transform.builder.SimpleStrategy

@Builder(builderStrategy = SimpleStrategy, prefix = '')
class BobCommand {
    def bobImage = 'bob.2.0:latest'
    def envVars = [:]
    def needDockerSocket = false

    String toString() {
        def env = envVars
                .collect({ entry -> "-e ${entry.key}=\"${entry.value}\"" })
                .join(' ')

        def cmd = """\
                    |docker run
                    |--init
                    |--rm
                    |--workdir \${PWD}
                    |--user \$(id -u):\$(id -g)
                    |-v \${PWD}:\${PWD}
                    |-v /etc/group:/etc/group:ro
                    |-v /etc/passwd:/etc/passwd:ro
                    |-v \${HOME}/.m2:\${HOME}/.m2
                    |-v \${HOME}/.docker:\${HOME}/.docker
                    |\$(if [ -n "\$HELM_REPO_CREDENTIALS" ]; then echo -v \$HELM_REPO_CREDENTIALS:\$HELM_REPO_CREDENTIALS;fi)
                    |${needDockerSocket ? '-v /var/run/docker.sock:/var/run/docker.sock' : ''}
                    |${env}
                    |\$(for group in \$(id -G); do printf ' --group-add %s' "\$group"; done)
                    |--group-add \$(stat -c '%g' /var/run/docker.sock)
                    |${bobImage}
                    |"""
        return cmd
                .stripMargin()           // remove indentation
                .replace('\n', ' ')      // join lines
                .replaceAll(/[ ]+/, ' ') // replace multiple spaces by one
    }
}
