import os
import streamlit as st
from backup_manager import BackupManager
from local_storage import storage
from datetime import datetime
import sqlite3

def setup_directories():
    """Crée tous les dossiers nécessaires."""
    directories = [
        "data",
        "data/files",
        "data/backups",
        "data/temp"
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Dossier créé/vérifié : {directory}")

def check_database():
    """Vérifie et initialise la base de données."""
    db_path = "data/memoires_db.sqlite"
    if not os.path.exists(db_path):
        print("! Base de données non trouvée, création en cours...")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Création des tables nécessaires
        c.execute('''CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            role TEXT NOT NULL,
            date_naissance TEXT,
            genre TEXT,
            telephone TEXT
        )''')
        
        # Autres tables...
        conn.commit()
        conn.close()
        print("✓ Base de données initialisée")
    else:
        print("✓ Base de données existante trouvée")

def create_initial_backup():
    """Crée une sauvegarde initiale."""
    backup_mgr = BackupManager()
    if backup_mgr.create_backup():
        print("✓ Sauvegarde initiale créée")
    else:
        print("! Erreur lors de la création de la sauvegarde initiale")

def check_storage():
    """Vérifie le système de stockage local."""
    try:
        test_file = "test.txt"
        test_content = b"Test storage system"
        
        # Test de sauvegarde
        success, path = storage.save_file(test_content, test_file)
        if not success:
            raise Exception("Échec de la sauvegarde")
            
        # Test de lecture
        content = storage.get_file(path)
        if content != test_content:
            raise Exception("Échec de la lecture")
            
        # Test de suppression
        if not storage.delete_file(path):
            raise Exception("Échec de la suppression")
            
        print("✓ Système de stockage local fonctionnel")
    except Exception as e:
        print(f"! Erreur du système de stockage : {str(e)}")

def initialize_app():
    """Initialise l'application complète."""
    print("\n=== Démarrage de l'application ===")
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Création des dossiers
    print("\n>> Vérification des dossiers")
    setup_directories()
    
    # 2. Vérification de la base de données
    print("\n>> Vérification de la base de données")
    check_database()
    
    # 3. Vérification du stockage
    print("\n>> Test du système de stockage")
    check_storage()
    
    # 4. Création d'une sauvegarde initiale
    print("\n>> Création d'une sauvegarde initiale")
    create_initial_backup()
    
    print("\n=== Initialisation terminée ===")
    return True

if __name__ == "__main__":
    initialize_app() 