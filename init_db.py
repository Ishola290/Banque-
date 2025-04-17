import sqlite3
import os
import hashlib

def init_db():
    # Assurez-vous que le dossier data existe
    os.makedirs('data', exist_ok=True)
    
    # Connexion à la base de données
    conn = sqlite3.connect('data/memoires_db.sqlite')
    c = conn.cursor()
    
    # Création des tables
    c.execute('''
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        mot_de_passe TEXT NOT NULL,
        role TEXT NOT NULL,
        date_naissance TEXT,
        genre TEXT,
        telephone TEXT
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS entites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL UNIQUE
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS filieres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        entite_id INTEGER NOT NULL,
        FOREIGN KEY (entite_id) REFERENCES entites (id),
        UNIQUE(nom, entite_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        annee_universitaire TEXT NOT NULL UNIQUE
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS memoires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        auteurs TEXT NOT NULL,
        encadreur TEXT NOT NULL,
        resume TEXT,
        fichier_url TEXT NOT NULL,
        tags TEXT,
        filiere_id INTEGER NOT NULL,
        session_id INTEGER NOT NULL,
        version TEXT,
        date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (filiere_id) REFERENCES filieres (id),
        FOREIGN KEY (session_id) REFERENCES sessions (id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        user_id INTEGER,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES utilisateurs (id)
    )
    ''')
    
    # Ajout de quelques données de test
    c.execute("INSERT OR IGNORE INTO entites (nom) VALUES ('UNSTIM')")
    c.execute("INSERT OR IGNORE INTO filieres (nom, entite_id) VALUES ('Informatique', 1)")
    c.execute("INSERT OR IGNORE INTO sessions (annee_universitaire) VALUES ('2023-2024')")
    
    # Ajout d'un utilisateur administrateur de test
    admin_password = hashlib.sha256('Admin@0128'.encode()).hexdigest()
    c.execute("""
    INSERT OR IGNORE INTO utilisateurs (nom, email, mot_de_passe, role)
    VALUES (?, ?, ?, ?)
    """, ('Administrateur', 'admin@universite.com', admin_password, 'admin'))
    
    # Ajout d'un utilisateur normal de test
    user_password = hashlib.sha256('user123'.encode()).hexdigest()
    c.execute("""
    INSERT OR IGNORE INTO utilisateurs (nom, email, mot_de_passe, role)
    VALUES (?, ?, ?, ?)
    """, ('Utilisateur Test', 'user@unstim.bj', user_password, 'user'))
    
    # Ajout d'un log initial
    c.execute("""
    INSERT INTO logs (action) VALUES ('Initialisation de la base de données')
    """)
    
    # Validation des changements
    conn.commit()
    conn.close()
    
    print("Base de données initialisée avec succès!")
    print("Utilisateurs créés :")
    print("Admin - Email: admin@universite.com, Mot de passe: Admin@0128")
    print("User  - Email: user@unstim.bj, Mot de passe: user123")

if __name__ == "__main__":
    init_db() 