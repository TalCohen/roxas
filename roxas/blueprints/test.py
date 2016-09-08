import structlog
from datetime import datetime

from flask import Blueprint, request, render_template

from roxas.models.models import Test
from roxas import db

logger = structlog.get_logger()

test_bp = Blueprint('test_bp', __name__)

@test_bp.route('/test')
def display():
    logger.info("Displaying test page.")
    test = Test.query.first()
    if test is None:
        test = Test('Sora')
        db.session.add(test)
        db.session.commit()
        logger.info("Created test.")
    else:
        test.datetime_created = datetime.now()
        db.session.commit()
        logger.info("Updated test.")

    template_args = {}
    template_args['header'] = 'Test'
    template_args['body'] = "This is a test page"
    template_args['name'] = test.name
    template_args['created'] = test.datetime_created
    print(request.headers)
    print(request.headers.get('REMOTE_USER'))
    return render_template('test.html', **template_args)

@test_bp.route('/test/post', methods=['POST'])
def testpost():
    print(request.form)
    print(request.form.get("test"))
    return "ok"
