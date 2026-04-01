ARG JENKINS_VERSION=2.554-jdk21
FROM jenkins/jenkins:${JENKINS_VERSION}

ARG BLUEOCEAN_VERSION=1.27.25
ARG DOCKER_WORKFLOW_VERSION=634.vedc7242b_eda_7
ARG HTMLPUBLISHER_VERSION=427
ARG PROMETHEUS_PLUGIN_VERSION=852.v317db_5d17a_b_0
ARG SONAR_PLUGIN_VERSION=2.18.2

USER root
RUN apt-get update && apt-get install -y lsb-release ca-certificates curl gnupg python3 ansible && \
    install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc && \
    chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y docker-ce-cli docker-compose-plugin && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
COPY --chown=jenkins:jenkins init.groovy.d/basic-security.groovy /usr/share/jenkins/ref/init.groovy.d/basic-security.groovy

USER jenkins
RUN chmod 0644 /usr/share/jenkins/ref/plugins.txt /usr/share/jenkins/ref/init.groovy.d/basic-security.groovy && \
    jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
