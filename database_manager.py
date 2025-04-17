import sqlite3
import os
import boto3
import json
import time
import threading
import atexit
from datetime import datetime
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.is_production = os.getenv('PRODUCTION', 'false').lower() == 'true'
        self.lock = threading.Lock()
        self.last_backup = time.time()
        self.backup_interval = 300  # 5 minutes
        
        if self.is_production:
            # AWS Configuration for production
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('AWS_REGION')
            )
            self.bucket_name = os.getenv('AWS_BUCKET_NAME')
            self.db_key = 'memoires_db.sqlite'
            
            # Créer un dossier temporaire pour la base de données
            self.temp_dir = '/tmp/memoires_db'
            os.makedirs(self.temp_dir, exist_ok=True)
            self.db_path = os.path.join(self.temp_dir, 'memoires_db.sqlite')
            
            # Restaurer la base de données au démarrage
            self._restore_from_s3()
            
            # Enregistrer la sauvegarde à la fermeture
            atexit.register(self._backup_to_s3)
        else:
            # Local configuration for development
            os.makedirs("data", exist_ok=True)
            self.db_path = "data/memoires_db.sqlite"

    def _restore_from_s3(self):
        """Restaure la base de données depuis S3 avec gestion des erreurs."""
        try:
            print("Restauration de la base de données depuis S3...")
            self.s3.download_file(self.bucket_name, self.db_key, self.db_path)
            print("Base de données restaurée avec succès")
        except Exception as e:
            print(f"Erreur lors de la restauration depuis S3: {e}")
            print("Création d'une nouvelle base de données...")
            self.init_db()

    def _backup_to_s3(self):
        """Sauvegarde la base de données vers S3 avec vérification d'intégrité."""
        if not self.is_production:
            return

        try:
            print("Sauvegarde de la base de données vers S3...")
            
            # Créer une copie temporaire pour la sauvegarde
            backup_path = f"{self.db_path}.backup"
            with self.lock:
                with open(self.db_path, 'rb') as src, open(backup_path, 'wb') as dst:
                    dst.write(src.read())
            
            # Upload vers S3
            self.s3.upload_file(backup_path, self.bucket_name, self.db_key)
            
            # Nettoyer
            os.remove(backup_path)
            self.last_backup = time.time()
            print("Sauvegarde terminée avec succès")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde vers S3: {e}")

    def get_connection(self):
        """Obtient une connexion à la base de données avec verrouillage."""
        with self.lock:
            conn = sqlite3.connect(self.db_path, timeout=20)
            conn.row_factory = sqlite3.Row
            return conn

    def check_backup_needed(self):
        """Vérifie si une sauvegarde est nécessaire et l'effectue si besoin."""
        if self.is_production and time.time() - self.last_backup > self.backup_interval:
            self._backup_to_s3()

    def execute_query(self, query, params=None, commit=False):
        """Exécute une requête avec gestion des erreurs et sauvegarde automatique."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if commit:
                conn.commit()
                self.check_backup_needed()
            
            return cursor.fetchall() if not commit else None
            
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"Erreur SQL: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_many(self, query, params_list):
        """Exécute plusieurs requêtes dans une transaction."""
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            conn.commit()
            self.check_backup_needed()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"Erreur SQL: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def init_db(self):
        """Initialise le schéma de la base de données."""
        queries = [
            '''CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY,
                nom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                mot_de_passe TEXT NOT NULL,
                date_naissance DATE,
                genre TEXT,
                role TEXT NOT NULL DEFAULT 'visiteur'
            )''',
            '''CREATE TABLE IF NOT EXISTS entites (
                id INTEGER PRIMARY KEY,
                nom TEXT NOT NULL UNIQUE
            )''',
            '''CREATE TABLE IF NOT EXISTS filieres (
                id INTEGER PRIMARY KEY,
                nom TEXT NOT NULL,
                entite_id INTEGER,
                FOREIGN KEY (entite_id) REFERENCES entites(id),
                UNIQUE(nom, entite_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY,
                annee TEXT NOT NULL UNIQUE
            )''',
            '''CREATE TABLE IF NOT EXISTS memoires (
                id INTEGER PRIMARY KEY,
                titre TEXT NOT NULL,
                auteurs TEXT NOT NULL,
                encadreur TEXT NOT NULL,
                resume TEXT,
                mots_cles TEXT,
                filiere_id INTEGER,
                session_id INTEGER,
                fichier_path TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (filiere_id) REFERENCES filieres(id),
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )''',
            '''CREATE TABLE IF NOT EXISTS favoris (
                id INTEGER PRIMARY KEY,
                utilisateur_id INTEGER,
                memoire_id INTEGER,
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
                FOREIGN KEY (memoire_id) REFERENCES memoires(id),
                UNIQUE(utilisateur_id, memoire_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY,
                utilisateur_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
            )'''
        ]
        
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            for query in queries:
                cursor.execute(query)
            conn.commit()
            if self.is_production:
                self._backup_to_s3()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            print(f"Erreur lors de l'initialisation de la base de données: {e}")
            raise
        finally:
            if conn:
                conn.close()

# Instance globale du gestionnaire
db_manager = DatabaseManager() 