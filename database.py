import psycopg2
import psycopg2.extras
from config import DB_CONFIG
import pandas as pd
import sqlite3
import os
import boto3
from botocore.exceptions import ClientError
import shutil
from datetime import datetime
import atexit

def get_connection():
    """Établit une connexion à la base de données PostgreSQL."""
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"]
        )
        return conn
    except Exception as e:
        print(f"Erreur de connexion à PostgreSQL: {e}")
        return None

def init_db():
    """Initialise la base de données avec les tables nécessaires."""
    conn = get_connection()
    if conn is None:
        return
    
    cur = conn.cursor()
    
    # Création des tables avec les mêmes structures que SQLite
    # mais optimisées pour PostgreSQL
    
    # Table utilisateurs
    cur.execute('''
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id SERIAL PRIMARY KEY,
        nom VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        mot_de_passe VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        date_naissance DATE,
        genre VARCHAR(50),
        telephone VARCHAR(50)
    )
    ''')
    
    # Table entites
    cur.execute('''
    CREATE TABLE IF NOT EXISTS entites (
        id SERIAL PRIMARY KEY,
        nom VARCHAR(255) NOT NULL UNIQUE
    )
    ''')
    
    # Table filieres
    cur.execute('''
    CREATE TABLE IF NOT EXISTS filieres (
        id SERIAL PRIMARY KEY,
        nom VARCHAR(255) NOT NULL,
        entite_id INTEGER NOT NULL REFERENCES entites(id),
        UNIQUE(nom, entite_id)
    )
    ''')
    
    # Table sessions
    cur.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id SERIAL PRIMARY KEY,
        annee_universitaire VARCHAR(50) NOT NULL UNIQUE
    )
    ''')
    
    # Table memoires
    cur.execute('''
    CREATE TABLE IF NOT EXISTS memoires (
        id SERIAL PRIMARY KEY,
        titre TEXT NOT NULL,
        auteurs VARCHAR(255) NOT NULL,
        encadreur VARCHAR(255) NOT NULL,
        resume TEXT,
        fichier_url TEXT NOT NULL,
        tags TEXT,
        filiere_id INTEGER NOT NULL REFERENCES filieres(id),
        session_id INTEGER NOT NULL REFERENCES sessions(id),
        version VARCHAR(50),
        date_ajout TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table favoris
    cur.execute('''
    CREATE TABLE IF NOT EXISTS favoris (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES utilisateurs(id),
        memoire_id INTEGER NOT NULL REFERENCES memoires(id),
        UNIQUE(user_id, memoire_id)
    )
    ''')
    
    # Table logs
    cur.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        action TEXT NOT NULL,
        user_id INTEGER REFERENCES utilisateurs(id),
        date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    cur.close()
    conn.close()

def execute_query(query, params=None, fetch=True):
    """Exécute une requête SQL et retourne les résultats si nécessaire."""
    conn = get_connection()
    if conn is None:
        return None
    
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(query, params)
        
        if fetch:
            result = cur.fetchall()
        else:
            result = None
            conn.commit()
        
        cur.close()
        return result
    except Exception as e:
        print(f"Erreur lors de l'exécution de la requête: {e}")
        return None
    finally:
        conn.close()

def query_to_dataframe(query, params=None):
    """Exécute une requête SQL et retourne les résultats sous forme de DataFrame."""
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()
    
    try:
        return pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"Erreur lors de la conversion en DataFrame: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

class DatabaseManager:
    def __init__(self):
        self.db_path = "data/memoires_db.sqlite"
        self.is_production = os.getenv('PRODUCTION', 'false').lower() == 'true'
        
        if self.is_production:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION')
            )
            self.bucket_name = os.getenv('AWS_BUCKET_NAME')
            self.s3_key = 'database/memoires_db.sqlite'
            
            # S'assurer que le dossier data existe
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Restaurer la base de données depuis S3
            self.restore_from_s3()
            
            # Enregistrer la sauvegarde à la fermeture
            atexit.register(self.backup_to_s3)
    
    def get_connection(self):
        """Retourne une connexion à la base de données."""
        return sqlite3.connect(self.db_path)
    
    def restore_from_s3(self):
        """Restaure la base de données depuis S3."""
        if not self.is_production:
            return
            
        try:
            print("Restauration de la base de données depuis S3...")
            self.s3_client.download_file(
                self.bucket_name,
                self.s3_key,
                self.db_path
            )
            print("Base de données restaurée avec succès")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                print("Aucune base de données trouvée sur S3, création d'une nouvelle base")
                self.init_db()
            else:
                raise
    
    def backup_to_s3(self):
        """Sauvegarde la base de données vers S3."""
        if not self.is_production:
            return
            
        try:
            print("Sauvegarde de la base de données vers S3...")
            
            # Créer une copie temporaire pour éviter les problèmes de verrouillage
            temp_path = f"{self.db_path}.backup"
            shutil.copy2(self.db_path, temp_path)
            
            # Uploader la copie
            self.s3_client.upload_file(
                temp_path,
                self.bucket_name,
                self.s3_key
            )
            
            # Supprimer la copie temporaire
            os.remove(temp_path)
            
            print("Base de données sauvegardée avec succès")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {str(e)}")
    
    def init_db(self):
        """Initialise une nouvelle base de données."""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Créer les tables nécessaires
        c.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            role TEXT NOT NULL,
            date_naissance TEXT,
            genre TEXT,
            telephone TEXT
        )
        ''')
        
        # Ajouter les autres tables...
        
        conn.commit()
        conn.close()

# Instance globale du gestionnaire de base de données
db = DatabaseManager() 