FROM eclipse-temurin:21-jre

ARG APP_JAR=target/spring-petclinic-4.0.0-SNAPSHOT.jar

WORKDIR /app
COPY ${APP_JAR} app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "/app/app.jar"]
