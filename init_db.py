import sqlite3
import os

def init_db():
    # Assurez-vous que le dossier data existe
    os.makedirs('data', exist_ok=True)
    
    # Connexion à la base de données
    conn = sqlite3.connect('data/memoires_db.sqlite')
    c = conn.cursor()
    
    # Création des tables
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
        fichier_pdf TEXT NOT NULL,
        tags TEXT,
        filiere_id INTEGER NOT NULL,
        session_id INTEGER NOT NULL,
        version TEXT,
        date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (filiere_id) REFERENCES filieres (id),
        FOREIGN KEY (session_id) REFERENCES sessions (id)
    )
    ''')
    
    # Ajout de quelques données de test
    c.execute("INSERT OR IGNORE INTO entites (nom) VALUES ('UNSTIM')")
    c.execute("INSERT OR IGNORE INTO filieres (nom, entite_id) VALUES ('Informatique', 1)")
    c.execute("INSERT OR IGNORE INTO sessions (annee_universitaire) VALUES ('2023-2024')")
    
    # Validation des changements
    conn.commit()
    conn.close()
    
    print("Base de données initialisée avec succès!")

if __name__ == "__main__":
    init_db() 