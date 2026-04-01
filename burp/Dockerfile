FROM ubuntu:24.04

ARG BURP_VERSION=2026.2.3

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    ca-certificates \
    net-tools \
    novnc \
    openbox \
    python3 \
    supervisor \
    websockify \
    x11vnc \
    xvfb \
    openjdk-21-jre \
    xterm \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/burp /workspace/burp-artifacts

ENV BURP_VERSION=${BURP_VERSION}
WORKDIR /opt/burp

COPY bin/start-burp-desktop.sh /usr/local/bin/start-burp-desktop.sh

RUN chmod +x /usr/local/bin/start-burp-desktop.sh

EXPOSE 5901 6080

ENTRYPOINT ["/usr/local/bin/start-burp-desktop.sh"]
