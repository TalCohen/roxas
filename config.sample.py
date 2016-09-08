# Flask config
DEBUG = True
HOST_NAME = 'localhost'
APP_NAME = 'roxas'
IP = '0.0.0.0'
PORT = 5000

# Database config
SQLALCHEMY_DATABASE_URI = 'sqlite:///{}'.format(os.path.join(os.getcwd(), "data.db"))
