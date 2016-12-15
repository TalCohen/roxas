import os

# Flask config
DEBUG = False
HOST_NAME = os.environ.get("ROXAS_HOST_NAME", 'roxas.csh.rit.edu')
SERVER_NAME = os.environ.get("ROXAS_SERVER_NAME", 'roxas.csh.rit.edu')
APP_NAME = os.environ.get("ROXAS_APP_NAME", 'roxas')
IP = os.environ.get("ROXAS_IP", '0.0.0.0')
PORT = os.environ.get("ROXAS_PORT", '8080')
SECRET_KEY = os.environ.get("ROXAS_SECRET_KEY", "")

# OpenID Connect SSO config
OIDC_ISSUER = os.environ.get("ROXAS_OIDC_ISSUER", 'https://sso.csh.rit.edu/realms/csh')
OIDC_CLIENT_CONFIG = {
    'client_id': os.environ.get("ROXAS_CLIENT_ID", 'roxas'),
    'client_secret': os.environ.get("ROXAS_CLIENT_SECRET", 'secretkey'),
    'post_logout_redirect_uris': [os.environ.get('ROXAS_OIDC_LOGOUT_REDIRECT_URI', 'https://roxas.csh.rit.edu/logout')]
}

# LDAP config
LDAP_RO = True
LDAP_URL = os.environ.get("ROXAS_LDAP_URL", 'ldaps://ldap.csh.rit.edu:636')
LDAP_BIND_DN = os.environ.get("ROXAS_LDAP_BIND_DN", 'cn=roxas,ou=Apps,dc=csh,dc=rit,dc=edu')
LDAP_BIND_PW = os.environ.get("ROXAS_LDAP_BIND_PW", '')
LDAP_USER_OU = os.environ.get("ROXAS_LDAP_USER_OU", 'ou=Users,dc=csh,dc=rit,dc=edu')
LDAP_GROUP_OU = os.environ.get("ROXAS_LDAP_GROUP_OU", 'ou=Groups,dc=csh,dc=rit,dc=edu')
LDAP_COMMITTEE_OU = os.environ.get("ROXAS_COMMITTEE_OU", 'ou=Committees,dc=csh,dc=rit,dc=edu')

# Database config
SQLALCHEMY_DATABASE_URI = os.environ.get("ROXAS_DB_URI", '')

# App config
ADMIN_USERS = os.environ.get("ROXAS_ADMIN_USERS", '').split(',')
ADMIN_GROUPS = os.environ.get("ROXAS_ADMIN_GROUPS", '').split(',')

