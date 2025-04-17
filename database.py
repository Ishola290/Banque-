import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.db_path = "data/memoires_db.sqlite"
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()
    
    def get_connection(self):
        """Retourne une connexion à la base de données."""
        return sqlite3.connect(self.db_path)
    
    def reset_db(self):
        """Réinitialise la base de données en supprimant toutes les tables."""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            # Supprimer toutes les tables existantes
            c.execute("DROP TABLE IF EXISTS favoris")
            c.execute("DROP TABLE IF EXISTS memoires")
            c.execute("DROP TABLE IF EXISTS filieres")
            c.execute("DROP TABLE IF EXISTS entites")
            c.execute("DROP TABLE IF EXISTS sessions")
            c.execute("DROP TABLE IF EXISTS logs")
            c.execute("DROP TABLE IF EXISTS utilisateurs")
            
            conn.commit()
            conn.close()
            
            # Réinitialiser la base de données
            self.init_db()
            return True, "Base de données réinitialisée avec succès."
        except Exception as e:
            return False, f"Erreur lors de la réinitialisation de la base de données : {str(e)}"
    
    def init_db(self):
        """Initialise une nouvelle base de données."""
        conn = self.get_connection()
        c = conn.cursor()
        
        # Table utilisateurs
        c.execute('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            date_naissance TEXT,
            genre TEXT,
            telephone TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Table entites
        c.execute('''
        CREATE TABLE IF NOT EXISTS entites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE
        )
        ''')
        
        # Table filieres
        c.execute('''
        CREATE TABLE IF NOT EXISTS filieres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            entite_id INTEGER NOT NULL,
            FOREIGN KEY (entite_id) REFERENCES entites (id),
            UNIQUE(nom, entite_id)
        )
        ''')
        
        # Table sessions
        c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annee_universitaire TEXT NOT NULL UNIQUE
        )
        ''')
        
        # Table memoires
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
        
        # Table favoris
        c.execute('''
        CREATE TABLE IF NOT EXISTS favoris (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            memoire_id INTEGER NOT NULL,
            date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES utilisateurs (id),
            FOREIGN KEY (memoire_id) REFERENCES memoires (id),
            UNIQUE(user_id, memoire_id)
        )
        ''')
        
        # Table logs
        c.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            user_id INTEGER,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES utilisateurs (id)
        )
        ''')
        
        # Création du compte administrateur par défaut si aucun admin n'existe
        c.execute("SELECT COUNT(*) FROM utilisateurs WHERE role='admin'")
        admin_count = c.fetchone()[0]
        
        if admin_count == 0:
            # Création d'un admin par défaut (admin@universite.com / Admin@0128)
            import hashlib
            hashed_pwd = hashlib.sha256("Admin@0128".encode()).hexdigest()
            c.execute("""
            INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role) 
            VALUES (?, ?, ?, ?, ?)
            """, ("Administrateur", "System", "admin@universite.com", hashed_pwd, "admin"))
        
        conn.commit()
        conn.close()

    def execute_query(self, query, params=None, fetch=True):
        """Exécute une requête SQL et retourne les résultats si nécessaire."""
        conn = self.get_connection()
        try:
            cur = conn.cursor()
            cur.execute(query, params or ())
            
            if fetch:
                result = cur.fetchall()
            else:
                result = None
                conn.commit()
            
            return result
        except Exception as e:
            print(f"Erreur lors de l'exécution de la requête: {e}")
            return None
        finally:
            conn.close()

    def add_log(self, action, user_id=None):
        """
        Ajoute une nouvelle entrée dans la table des logs.
        
        Args:
            action (str): Description de l'action effectuée
            user_id (int, optional): ID de l'utilisateur ayant effectué l'action
        """
        query = """
        INSERT INTO logs (action, user_id, date)
        VALUES (?, ?, ?)
        """
        self.execute_query(query, (action, user_id, datetime.now()), fetch=False)

    def get_logs(self, limit=100, user_id=None):
        """
        Récupère l'historique des logs.
        
        Args:
            limit (int): Nombre maximum d'entrées à récupérer
            user_id (int, optional): Filtrer les logs pour un utilisateur spécifique
        
        Returns:
            list: Liste des logs avec les détails de chaque action
        """
        if user_id:
            query = """
            SELECT l.*, u.nom, u.email 
            FROM logs l 
            LEFT JOIN utilisateurs u ON l.user_id = u.id 
            WHERE l.user_id = ? 
            ORDER BY l.date DESC 
            LIMIT ?
            """
            return self.execute_query(query, (user_id, limit))
        else:
            query = """
            SELECT l.*, u.nom, u.email 
            FROM logs l 
            LEFT JOIN utilisateurs u ON l.user_id = u.id 
            ORDER BY l.date DESC 
            LIMIT ?
            """
            return self.execute_query(query, (limit,))

# Instance globale du gestionnaire de base de données
db = DatabaseManager() 