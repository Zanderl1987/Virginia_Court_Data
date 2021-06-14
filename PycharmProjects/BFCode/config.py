# Server
#DEBUG = True
SECRET_KEY = '6b0960beb776ba8136b835571d6280b9'

# Database
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://cdtmaster:CGMcdt1234@cdt-cgm-db-cloned-cluster.ctebkj2v7lnh.us-east-1.rds.amazonaws.com/wbs_testDB'
SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

# Email
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = 'swebbased@gmail.com'
MAIL_PASSWORD = 'contactForm'
MAIL_DEFAULT_SENDER = 'swebbased@gmail.com'