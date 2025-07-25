import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
# BASE_DIR es la carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Clave secreta para producción (NO la subas nunca a repositorios)
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'reemplaza-esto-por-una-clave-segura')

# Debug: en producción debe ser False
DEBUG = True

# Hosts permitidos
ALLOWED_HOSTS = ['seguros.safeyourcargo.com','localhost', '127.0.0.1', '64.227.29.217']

# Aplicaciones instaladas
INSTALLED_APPS = [
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Agrega aquí tus apps personalizadas    
    'core',
    'anymail',
]
CSRF_TRUSTED_ORIGINS = ['https://seguros.safeyourcargo.com']
# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URLs principales
ROOT_URLCONF = 'safeyourcargo.urls'

# Plantillas
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# WSGI
WSGI_APPLICATION = 'safeyourcargo.wsgi.application'

# Configuración de la base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'defaultdb',
        'USER': 'doadmin',
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': 'db-postgresql-nyc1-56016-do-user-22829142-0.m.db.ondigitalocean.com',
        'PORT': '25060',
        'OPTIONS': {
            'sslmode': 'require',  # ⚠️ Es muy importante para la conexión segura
        },
    }
}

# Validadores de contraseña
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Zona horaria y lenguaje
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_L10N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True
# Archivos estáticos
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')



# Archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Configuración por defecto del campo de clave primaria
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'core.Usuario'


BCCH_USER = os.getenv("BCCH_USER")
BCCH_PASS = os.getenv("BCCH_PASS")


# Backend de correo electrónico usando Anymail para Mailgun
EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"

# Configuración específica de Anymail para Mailgun
ANYMAIL = {
    "MAILGUN_API_KEY": os.environ.get('MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": os.environ.get('MAILGUN_DOMAIN'), # Tu dominio de Mailgun, ej. 'mg.safeyourcargo.com'
}

# Configuración del remitente por defecto para todos los correos de Django
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@safeyourcargo.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
print(f"DEBUG: DEFAULT_FROM_EMAIL cargado: {DEFAULT_FROM_EMAIL}") # <--- AGREGAR ESTA LÍNEA TEMPORAL

NSURE_API_HOME = 'https://igi.nsure.net/api/v1'
NSURE_API_KEY = 'PqrED4vo2UI8I8TlPTgOKmCo0C1OuSUzbgbpIBHQwgnA2343xbtwqjhmGZ2bckvp'
NSURE_USERNAME = 'jaimevalpo2020@gmail.com'
NSURE_PASSWORD = 'Pollito2012'

LOGIN_URL = 'login' 
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'