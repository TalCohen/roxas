import os
import requests

from flask import Flask, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_pyoidc.flask_pyoidc import OIDCAuthentication
import structlog

from roxas.util.ldap import ldap_init

app = Flask(__name__)

if os.path.exists(os.path.join(os.getcwd(), "config.py")):
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.py"))
else:
    app.config.from_pyfile(os.path.join(os.getcwd(), "config.env.py"))

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Disable SSL certificate verification warning
requests.packages.urllib3.disable_warnings()

db = SQLAlchemy(app)
migrate = Migrate(app, db)
logger = structlog.get_logger()

ldap_init(app.config['LDAP_RO'],
          app.config['LDAP_URL'],
          app.config['LDAP_BIND_DN'],
          app.config['LDAP_BIND_PW'],
          app.config['LDAP_USER_OU'],
          app.config['LDAP_GROUP_OU'],
          app.config['LDAP_COMMITTEE_OU'])
auth = OIDCAuthentication(app,
                          issuer=app.config['OIDC_ISSUER'],
                          client_registration_info=app.config['OIDC_CLIENT_CONFIG'])

from roxas.blueprints.device import device_bp
from roxas.blueprints.auth import auth_bp

app.register_blueprint(device_bp)
app.register_blueprint(auth_bp)

@app.route('/logout')
@auth.oidc_logout
def logout():
    session['username'] = None
    session['uuid'] = None
    session['is_admin'] = None

    return redirect(url_for('index'), 302)
