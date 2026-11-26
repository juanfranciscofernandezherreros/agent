# Corpus: configuración Django.
DEBUG = True  # expect: SEC-DEBUG
SECRET_KEY = "django-insecure-9a8b7c6d5e4f3g2h1i0j"  # expect: SEC-SECRET
ALLOWED_HOSTS = ["api.example.com"]
CORS_ALLOW_ALL_ORIGINS = True  # expect: SEC-CORS
