#!/usr/bin/env bash
set -e

echo "==> raising vm.max_map_count for SonarQube"
docker run --rm --privileged alpine sysctl -w vm.max_map_count=262144

echo "==> starting infrastructure (everything except jenkins)"
docker compose up -d --build postgres sonarqube prometheus grafana petclinic-prod

echo "==> waiting for sonarqube"
until curl -sf http://localhost:9000/api/system/status | grep -q '"status":"UP"'; do sleep 5; done

echo "==> creating sonarqube token and webhook"
TOKEN=$(curl -su admin:admin -X POST \
  "http://localhost:9000/api/user_tokens/generate?name=jenkins&type=GLOBAL_ANALYSIS_TOKEN" \
  | grep -oP '"token":"\K[^"]+')
echo "SONAR_TOKEN=$TOKEN" > .env

curl -su admin:admin -X POST "http://localhost:9000/api/webhooks/create" \
  --data-urlencode "name=Jenkins" \
  --data-urlencode "url=http://jenkins:8080/sonarqube-webhook/" > /dev/null

echo "==> starting jenkins (JCasC configures sonarqube + credentials + pipeline job on boot)"
docker compose up -d --build jenkins

echo "==> waiting for jenkins"
until curl -sf http://localhost:8080/login > /dev/null; do sleep 5; done

echo ""
echo "Done."
echo "  Jenkins     http://localhost:8080    (admin / admin)"
echo "  SonarQube   http://localhost:9000    (admin / admin)"
echo "  Grafana     http://localhost:3000    (admin / admin)"
echo "  Prometheus  http://localhost:9090"
echo "  PetClinic   http://localhost:8082    (after first build)"
echo ""
echo "Pipeline job 'spring-petclinic' is created. Click Build Now or push a commit."