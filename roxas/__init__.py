from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import structlog

app = Flask(__name__)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
logger = structlog.get_logger()

from roxas.blueprints.test import test_bp

app.register_blueprint(test_bp)

@app.route('/', methods=['GET'])
def index():
    logger.info("Connected to index page.")
    return render_template('index.html')
