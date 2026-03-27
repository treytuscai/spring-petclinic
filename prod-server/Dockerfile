FROM ubuntu:24.04

# Install SSH so Jenkins/Ansible can connect, Java to run the app, and sudo for admin tasks.
RUN apt-get update && apt-get install -y \
    openssh-server \
    openjdk-17-jre \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create the deployer user and prepare directories for SSH and the PetClinic app.
RUN useradd -m -s /bin/bash deployer && \
    echo 'deployer:deployer' | chpasswd && \
    mkdir -p /home/deployer/.ssh /var/run/sshd /opt/petclinic && \
    chown -R deployer:deployer /home/deployer /opt/petclinic

# Expose SSH and application ports.
EXPOSE 22 8080

# Keep the container running by starting the SSH server in the foreground.
CMD ["/usr/sbin/sshd", "-D"]
