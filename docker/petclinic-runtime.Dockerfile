FROM eclipse-temurin:21-jre-jammy

ARG APP_JAR=target/spring-petclinic-4.0.0-SNAPSHOT.jar

RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ${APP_JAR} app.jar

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=12 CMD curl -fsS http://127.0.0.1:8080/actuator/health > /dev/null || curl -fsS http://127.0.0.1:8080/ > /dev/null || exit 1

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
