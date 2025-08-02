SECRET_KEY = 'your-secret-key'
DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '54.165.207.248']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mysql1',
        'USER': 'bharati_user',
        'PASSWORD': 'Database@123',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

