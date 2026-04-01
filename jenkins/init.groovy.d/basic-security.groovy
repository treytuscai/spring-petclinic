import hudson.model.User
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.security.HudsonPrivateSecurityRealm
import jenkins.model.Jenkins
import org.jenkinsci.plugins.prometheus.config.PrometheusConfiguration

def instance = Jenkins.get()

def adminUser = System.getenv("JENKINS_ADMIN_USER") ?: "admin"
def adminPassword = System.getenv("JENKINS_ADMIN_PASSWORD") ?: "admin123"
def metricsUser = System.getenv("JENKINS_METRICS_USER") ?: "prometheus"
def metricsPassword = System.getenv("JENKINS_METRICS_PASSWORD") ?: "prometheus123"

def hudsonRealm = new HudsonPrivateSecurityRealm(false)
if (User.getById(adminUser, false) == null) {
    hudsonRealm.createAccount(adminUser, adminPassword)
}
if (User.getById(metricsUser, false) == null) {
    hudsonRealm.createAccount(metricsUser, metricsPassword)
}

instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

def prometheusConfig = PrometheusConfiguration.get()
prometheusConfig.setUseAuthenticatedEndpoint(true)
prometheusConfig.save()

instance.save()
