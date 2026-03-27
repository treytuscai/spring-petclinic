FROM ubuntu:24.04

RUN apt-get update && apt-get install -y \
    openssh-server \
    openjdk-17-jre \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash deployer && \
    echo 'deployer:deployer' | chpasswd && \
    mkdir -p /home/deployer/.ssh /var/run/sshd /opt/petclinic && \
    chown -R deployer:deployer /home/deployer /opt/petclinic

EXPOSE 22 8080

CMD ["/usr/sbin/sshd", "-D"]