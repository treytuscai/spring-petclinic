import hudson.model.User
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.security.HudsonPrivateSecurityRealm
import jenkins.model.Jenkins

def instance = Jenkins.get()

def adminUser = System.getenv("JENKINS_ADMIN_USER") ?: "admin"
def adminPassword = System.getenv("JENKINS_ADMIN_PASSWORD") ?: "admin123"

def hudsonRealm = new HudsonPrivateSecurityRealm(false)
if (User.getById(adminUser, false) == null) {
    hudsonRealm.createAccount(adminUser, adminPassword)
}

instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

instance.save()
