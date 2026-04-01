# Burp Community Container Notes

This directory contains the Burp Community desktop container used by the Jenkins manual security gate.

## Download the Burp JAR

Download the latest `Burp Suite Community Edition` JAR from the official PortSwigger release page and place it at:

```bash
burp/downloads/burpsuite_community.jar
```

Guide reference:

- Burp releases: <https://portswigger.net/burp/releases>

This repository does not vendor the Burp binary.

## Start the container stack

```bash
docker compose --profile devsecops up -d --build burp
```

Then open:

```text
http://localhost:6080/vnc.html
```

Artifacts saved to `/workspace/burp-artifacts` in the Burp desktop are shared back to Jenkins through the `burp_artifacts` volume.
