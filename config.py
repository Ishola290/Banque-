import os

# Configuration PostgreSQL
DB_CONFIG = {
    "dbname": "memoires_db",
    "user": "postgres",
    "password": "votre_mot_de_passe",  # À changer
    "host": "localhost",
    "port": "5432"
}

# Configuration AWS S3
AWS_CONFIG = {
    "aws_access_key_id": "votre_access_key",  # À changer
    "aws_secret_access_key": "votre_secret_key",  # À changer
    "region_name": "eu-west-3",  # Par exemple, Europe (Paris)
    "bucket_name": "memoires-unstim"
}

# Autres configurations
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_EXTENSIONS = {'pdf'} 