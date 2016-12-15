# Flask config
DEBUG = True
HOST_NAME = 'localhost'
SERVER_NAME = 'localhost:5000'
APP_NAME = 'roxas'
IP = '0.0.0.0'
PORT = 5000
SECRET_KEY = "thisisnotsecure"

# OpenID Connect SSO config
OIDC_ISSUER = 'https://sso.csh.rit.edu/realms/csh'
OIDC_CLIENT_CONFIG = {
    'client_id': 'gravity',
    'client_secret': 'secretkey',
    'post_logout_redirect_uris': ['localhost/logout']
}

# LDAP config
LDAP_RO = True
LDAP_URL = 'ldaps://ldap.csh.rit.edu:636'
LDAP_BIND_DN = 'cn=conditional,ou=Apps,dc=csh,dc=rit,dc=edu'
LDAP_BIND_PW = ''
LDAP_USER_OU = 'ou=Users,dc=csh,dc=rit,dc=edu'
LDAP_GROUP_OU = 'ou=Groups,dc=csh,dc=rit,dc=edu'
LDAP_COMMITTEE_OU = 'ou=Committees,dc=csh,dc=rit,dc=edu'

# Database config
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(os.getcwd(), "data.db"))

# App config
ADMIN_USERS = ['1337man', '3cool5me']
ADMIN_GROUPS = ['rtp']
