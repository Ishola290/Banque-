import streamlit as st
import sqlite3
import pandas as pd
import os
import hashlib
import uuid
import base64
from datetime import datetime
from io import BytesIO
import time
from storage import FileStorage
from database import db

# Configuration du thème global
st.markdown("""
    <style>
        /* Variables globales */
        :root {
            --primary-color: #2E86AB;
            --secondary-color: #247297;
            --background-color: #F0F2F6;
            --text-color: #333333;
            --card-background: #FFFFFF;
            --border-radius: 10px;
            --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            --transition: all 0.3s ease;
        }

        /* Style général */
        .stApp {
            background-color: var(--background-color);
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }

        /* En-tête et texte */
        h1, h2, h3, h4, h5, h6 {
            color: var(--primary-color) !important;
            font-weight: 600 !important;
            letter-spacing: -0.5px;
        }

        /* Conteneurs et cartes */
        .element-container {
            background-color: var(--card-background);
            border-radius: var(--border-radius);
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: var(--box-shadow);
            transition: var(--transition);
        }

        .element-container:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }

        /* Boutons */
        .stButton > button {
            background-color: var(--primary-color) !important;
            color: white !important;
            border: none !important;
            border-radius: var(--border-radius) !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 500 !important;
            transition: var(--transition) !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            width: 100%;
        }

        .stButton > button:hover {
            background-color: var(--secondary-color) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }

        /* Inputs et sélecteurs */
        .stTextInput > div > div, .stSelectbox > div > div {
            background-color: var(--card-background);
            border-radius: var(--border-radius);
            border: 1px solid #E0E0E0;
            padding: 0.5rem;
            transition: var(--transition);
        }

        .stTextInput > div > div:focus-within, .stSelectbox > div > div:focus-within {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(46, 134, 171, 0.2);
        }

        /* Tables et DataFrames */
        .dataframe {
            background-color: var(--card-background);
            border-radius: var(--border-radius);
            overflow: hidden;
            border: none !important;
            box-shadow: var(--box-shadow);
        }

        .dataframe th {
            background-color: var(--primary-color) !important;
            color: white !important;
            padding: 1rem !important;
            font-weight: 500;
        }

        .dataframe td {
            padding: 0.8rem !important;
            border-bottom: 1px solid #E0E0E0;
            transition: var(--transition);
        }

        .dataframe tr:hover td {
            background-color: rgba(46, 134, 171, 0.05);
        }

        /* Sidebar */
        .css-1d391kg, [data-testid="stSidebar"] {
            background-color: var(--card-background);
            border-right: 1px solid #E0E0E0;
        }

        /* Métriques */
        .stMetric {
            background-color: var(--card-background);
            padding: 1.5rem;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
            transition: var(--transition);
        }

        .stMetric:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }

        .stMetric label {
            color: var(--primary-color);
            font-weight: 600;
            font-size: 1.1em;
        }

        /* Expanders */
        .streamlit-expander {
            border: none !important;
            background-color: var(--card-background) !important;
            border-radius: var(--border-radius) !important;
            box-shadow: var(--box-shadow);
            margin: 0.5rem 0;
        }

        .streamlit-expander > div:first-child {
            border-radius: var(--border-radius) var(--border-radius) 0 0 !important;
            background-color: var(--primary-color) !important;
            color: white !important;
            padding: 1rem !important;
        }

        /* Messages d'info, succès, erreur */
        .stAlert {
            border-radius: var(--border-radius) !important;
            padding: 1rem !important;
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .element-container {
                padding: 1rem;
            }
            
            .stButton > button {
                padding: 0.5rem 1rem !important;
            }
            
            .dataframe th, .dataframe td {
                padding: 0.6rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Créer les dossiers nécessaires s'ils n'existent pas
os.makedirs("data", exist_ok=True)
os.makedirs("data/memoires", exist_ok=True)

# Chemin de la base de données
DB_PATH = "data/memoires_db.sqlite"

# Initialiser le stockage de fichiers
storage = FileStorage()

# Fonction pour initialiser la base de données
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Créer la table utilisateurs si elle n'existe pas
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
    
    # Création de la table entites
    c.execute('''
    CREATE TABLE IF NOT EXISTS entites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Création de la table filieres
    c.execute('''
    CREATE TABLE IF NOT EXISTS filieres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        entite_id INTEGER NOT NULL,
        FOREIGN KEY (entite_id) REFERENCES entites (id),
        UNIQUE(nom, entite_id)
    )
    ''')
    
    # Création de la table sessions
    c.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        annee_universitaire TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Création de la table memoires
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
    
    # Création de la table favoris
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
    
    conn.commit()
    conn.close()

# Fonction pour ajouter un log
def add_log(action, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO logs (action, user_id, date) VALUES (?, ?, ?)", 
             (action, user_id, date_now))
    conn.commit()
    conn.close()

# Fonction pour vérifier l'authentification
def check_auth(email, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Hash du mot de passe avec la même méthode que lors de l'inscription
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
        
        # Vérification de l'utilisateur
        c.execute("""
            SELECT id, nom || ' ' || prenom as nom_complet, role 
            FROM utilisateurs 
            WHERE email=? AND mot_de_passe=?
        """, (email, hashed_pwd))
        
        user = c.fetchone()
        
        # Journalisation de la tentative de connexion
        success = user is not None
        add_log(f"Tentative de connexion {'réussie' if success else 'échouée'} pour {email}")
        
        return user
    except Exception as e:
        print(f"Erreur lors de l'authentification : {e}")
        return None
    finally:
        conn.close()

# Fonction pour ajouter une entité
def add_entity(nom):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO entites (nom) VALUES (?)", (nom,))
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result

# Fonction pour récupérer toutes les entités
def get_all_entities():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM entites ORDER BY nom", conn)
    conn.close()
    return df

# Fonction pour supprimer une entité
def delete_entity(entity_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Vérifier si l'entité est utilisée dans une filière
    c.execute("SELECT COUNT(*) FROM filieres WHERE entite_id=?", (entity_id,))
    count = c.fetchone()[0]
    if count > 0:
        conn.close()
        return False, "Cette entité est associée à des filières et ne peut pas être supprimée."
    
    # Supprimer l'entité
    c.execute("DELETE FROM entites WHERE id=?", (entity_id,))
    conn.commit()
    conn.close()
    return True, "Entité supprimée avec succès."

# Fonction pour ajouter une filière
def add_filiere(nom, entite_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO filieres (nom, entite_id) VALUES (?, ?)", (nom, entite_id))
        conn.commit()
        result = True, "Filière ajoutée avec succès."
    except sqlite3.IntegrityError:
        result = False, "Cette filière existe déjà pour cette entité."
    conn.close()
    return result

# Fonction pour récupérer toutes les filières
def get_all_filieres():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT f.id, f.nom, e.nom as entite_nom, f.entite_id 
    FROM filieres f 
    JOIN entites e ON f.entite_id = e.id 
    ORDER BY e.nom, f.nom
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Fonction pour supprimer une filière
def delete_filiere(filiere_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Vérifier si la filière est utilisée dans un mémoire
    c.execute("SELECT COUNT(*) FROM memoires WHERE filiere_id=?", (filiere_id,))
    count = c.fetchone()[0]
    if count > 0:
        conn.close()
        return False, "Cette filière est associée à des mémoires et ne peut pas être supprimée."
    
    # Supprimer la filière
    c.execute("DELETE FROM filieres WHERE id=?", (filiere_id,))
    conn.commit()
    conn.close()
    return True, "Filière supprimée avec succès."

# Fonction pour ajouter une session
def add_session(annee):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO sessions (annee_universitaire) VALUES (?)", (annee,))
        conn.commit()
        result = True, "Session ajoutée avec succès."
    except sqlite3.IntegrityError:
        result = False, "Cette session existe déjà."
    conn.close()
    return result

# Fonction pour récupérer toutes les sessions
def get_all_sessions():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM sessions ORDER BY annee_universitaire DESC", conn)
    conn.close()
    return df

# Fonction pour supprimer une session
def delete_session(session_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Vérifier si la session est utilisée dans un mémoire
    c.execute("SELECT COUNT(*) FROM memoires WHERE session_id=?", (session_id,))
    count = c.fetchone()[0]
    if count > 0:
        conn.close()
        return False, "Cette session est associée à des mémoires et ne peut pas être supprimée."
    
    # Supprimer la session
    c.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
    return True, "Session supprimée avec succès."

# Fonction pour sauvegarder un fichier PDF
def save_pdf(uploaded_file, filename):
    if uploaded_file is not None:
        success, file_path = storage.save_file(uploaded_file, filename)
        return success, file_path
    return False, None

# Fonction pour sauvegarder le contenu d'un PDF dans la base de données
def save_pdf_content(memoire_id, pdf_content):
    """Sauvegarde le contenu du PDF dans la base de données."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Supprimer l'ancien contenu s'il existe
        c.execute("DELETE FROM pdf_content WHERE memoire_id = ?", (memoire_id,))
        
        # Insérer le nouveau contenu
        for page in pdf_content:
            c.execute("""
            INSERT INTO pdf_content (memoire_id, page_num, content)
            VALUES (?, ?, ?)
            """, (memoire_id, page['page_num'], page['text']))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du contenu: {str(e)}")
        return False
    finally:
        conn.close()

# Fonction pour ajouter un mémoire
def add_memoire(titre, auteurs, encadreur, resume, fichier_url, tags, filiere_id, session_id, version):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insérer le mémoire
        c.execute("""
        INSERT INTO memoires 
        (titre, auteurs, encadreur, resume, fichier_url, tags, filiere_id, session_id, version, date_ajout) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (titre, auteurs, encadreur, resume, fichier_url, tags, filiere_id, session_id, version, date_now))
        
        conn.commit()
        result = True, "Mémoire ajouté avec succès."
    except Exception as e:
        result = False, f"Erreur lors de l'ajout du mémoire: {str(e)}"
    conn.close()
    return result

# Fonction pour récupérer tous les mémoires
def get_all_memoires():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT m.id, m.titre, m.auteurs, m.encadreur, m.resume, m.fichier_url, m.tags, 
           f.nom as filiere_nom, s.annee_universitaire, m.version, m.date_ajout,
           e.nom as entite_nom
    FROM memoires m
    JOIN filieres f ON m.filiere_id = f.id
    JOIN sessions s ON m.session_id = s.id
    JOIN entites e ON f.entite_id = e.id
    ORDER BY m.date_ajout DESC
    """
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        print(f"Erreur lors de la récupération des mémoires : {e}")
        return pd.DataFrame()  # Retourne un DataFrame vide en cas d'erreur
    finally:
        conn.close()

# Fonction pour supprimer un mémoire
def delete_memoire(memoire_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Vérifier si le mémoire existe
        c.execute("SELECT id, fichier_url FROM memoires WHERE id = ?", (memoire_id,))
        result = c.fetchone()
        
        if result is None:
            conn.close()
            return False, f"Mémoire avec ID {memoire_id} non trouvé dans la base de données."
        
        file_path = result[1]
        
        # Supprimer d'abord les références dans la table favoris
        c.execute("DELETE FROM favoris WHERE memoire_id = ?", (memoire_id,))
        
        # Supprimer le mémoire de la base de données
        c.execute("DELETE FROM memoires WHERE id = ?", (memoire_id,))
        
        # Supprimer le fichier PDF si nécessaire
        if file_path and file_path.startswith("local://"):
            try:
                storage.delete_file(file_path)
            except Exception as e:
                print(f"Avertissement: Erreur lors de la suppression du fichier: {e}")
                # On continue même si la suppression du fichier échoue
        
        conn.commit()
        return True, "Mémoire supprimé avec succès."
        
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de la suppression: {str(e)}"
    finally:
        conn.close()

# Fonction pour rechercher des mémoires
def search_memoires(query, entity=None, filiere=None, session=None):
    conn = sqlite3.connect(DB_PATH)
    
    conditions = []
    params = []
    
    # Construire la condition de recherche texte
    if query:
        text_search = """
        (m.titre LIKE ? OR m.auteurs LIKE ? OR m.encadreur LIKE ? OR m.resume LIKE ? OR m.tags LIKE ?)
        """
        for _ in range(5):
            params.append(f"%{query}%")
        conditions.append(text_search)
    
    # Ajouter les filtres supplémentaires
    if entity:
        conditions.append("e.id = ?")
        params.append(entity)
    
    if filiere:
        conditions.append("f.id = ?")
        params.append(filiere)
    
    if session:
        conditions.append("s.id = ?")
        params.append(session)
    
    # Construire la requête SQL
    sql = """
    SELECT m.id, m.titre, m.auteurs, m.encadreur, m.resume, m.fichier_url, m.tags, 
           f.nom as filiere_nom, s.annee_universitaire, m.version, m.date_ajout,
           e.nom as entite_nom
    FROM memoires m
    JOIN filieres f ON m.filiere_id = f.id
    JOIN sessions s ON m.session_id = s.id
    JOIN entites e ON f.entite_id = e.id
    """
    
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    
    sql += " ORDER BY m.date_ajout DESC"
    
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

# Fonction pour obtenir les filieres d'une entité
def get_filieres_by_entity(entity_id):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, nom FROM filieres WHERE entite_id=? ORDER BY nom", conn, params=(entity_id,))
    conn.close()
    return df

# Fonction pour obtenir le détail d'un mémoire
def get_memoire_details(memoire_id):
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT m.id, m.titre, m.auteurs, m.encadreur, m.resume, m.fichier_url, m.tags, 
           f.nom as filiere_nom, s.annee_universitaire, m.version, m.date_ajout,
           e.nom as entite_nom, f.id as filiere_id, s.id as session_id
    FROM memoires m
    JOIN filieres f ON m.filiere_id = f.id
    JOIN sessions s ON m.session_id = s.id
    JOIN entites e ON f.entite_id = e.id
    WHERE m.id = ?
    """
    df = pd.read_sql_query(query, conn, params=(memoire_id,))
    conn.close()
    if len(df) > 0:
        return df.iloc[0]
    return None

# Fonction pour mettre à jour un mémoire
def update_memoire(memoire_id, titre, auteurs, encadreur, resume, fichier_url, tags, filiere_id, session_id, version):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        if fichier_url:  # Nouveau fichier PDF
            c.execute("""
            UPDATE memoires 
            SET titre=?, auteurs=?, encadreur=?, resume=?, fichier_url=?, tags=?, filiere_id=?, session_id=?, version=?
            WHERE id=?
            """, (titre, auteurs, encadreur, resume, fichier_url, tags, filiere_id, session_id, version, memoire_id))
        else:  # Pas de nouveau fichier PDF
            c.execute("""
            UPDATE memoires 
            SET titre=?, auteurs=?, encadreur=?, resume=?, tags=?, filiere_id=?, session_id=?, version=?
            WHERE id=?
            """, (titre, auteurs, encadreur, resume, tags, filiere_id, session_id, version, memoire_id))
        
        conn.commit()
        result = True, "Mémoire mis à jour avec succès."
    except Exception as e:
        result = False, f"Erreur lors de la mise à jour du mémoire: {str(e)}"
    conn.close()
    return result

# Fonction pour obtenir les statistiques
def get_statistics():
    conn = sqlite3.connect(DB_PATH)
    stats = {}
    
    # Nombre total de mémoires
    stats['total_memoires'] = pd.read_sql_query("SELECT COUNT(*) as count FROM memoires", conn).iloc[0]['count']
    
    # Nombre de mémoires par entité
    stats['memoires_par_entite'] = pd.read_sql_query("""
    SELECT e.nom, COUNT(*) as count 
    FROM memoires m
    JOIN filieres f ON m.filiere_id = f.id
    JOIN entites e ON f.entite_id = e.id
    GROUP BY e.nom
    ORDER BY count DESC
    """, conn)
    
    # Nombre de mémoires par année
    stats['memoires_par_annee'] = pd.read_sql_query("""
    SELECT s.annee_universitaire, COUNT(*) as count 
    FROM memoires m
    JOIN sessions s ON m.session_id = s.id
    GROUP BY s.annee_universitaire
    ORDER BY s.annee_universitaire DESC
    """, conn)
    
    # Nombre de mémoires par filière
    stats['memoires_par_filiere'] = pd.read_sql_query("""
    SELECT f.nom, COUNT(*) as count 
    FROM memoires m
    JOIN filieres f ON m.filiere_id = f.id
    GROUP BY f.nom
    ORDER BY count DESC
    LIMIT 10
    """, conn)
    
    conn.close()
    return stats

# Fonction pour afficher un PDF intégré
def display_pdf(file_path):
    """Affiche un PDF dans l'interface."""
    try:
        if file_path.startswith("local://"):
            # Récupérer le contenu du fichier depuis le stockage local
            pdf_content = storage.get_file(file_path)
            if pdf_content:
                # Créer un conteneur pour le PDF
                pdf_container = st.empty()
                
                # Encoder le contenu en base64
                b64 = base64.b64encode(pdf_content).decode('utf-8')
                
                # Créer l'iframe avec le PDF
                pdf_display = f'''
                    <iframe
                        src="data:application/pdf;base64,{b64}"
                        width="100%"
                        height="800px"
                        type="application/pdf"
                        frameborder="0"
                        style="border: 1px solid #ccc; border-radius: 5px;"
                    >
                    </iframe>
                '''
                
                # Afficher le PDF
                pdf_container.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.error("Impossible de récupérer le fichier PDF. Veuillez vérifier que le fichier existe.")
        else:
            st.error("Format de fichier non supporté. Le chemin doit commencer par 'local://'")
    except Exception as e:
        st.error(f"Erreur lors de l'affichage du PDF: {str(e)}")

# Fonction pour créer un lien de téléchargement
def get_download_link(file_path, label):
    """Crée un lien de téléchargement pour un fichier PDF."""
    try:
        if file_path.startswith("local://"):
            # Récupérer le contenu du fichier depuis le stockage local
            file_content = storage.get_file(file_path)
            if file_content:
                # Extraire le nom du fichier original
                filename = os.path.basename(file_path.replace("local://", ""))
                # Utiliser le composant de téléchargement natif de Streamlit
                return st.download_button(
                    label=label,
                    data=file_content,
                    file_name=filename,
                    mime="application/pdf"
                )
            else:
                st.error("Impossible de récupérer le fichier PDF")
                return None
        return None
    except Exception as e:
        st.error(f"Erreur lors de la création du lien de téléchargement: {str(e)}")
        return None

# Fonction pour inscrire un visiteur
def register_visitor(nom, prenom, email, password, date_naissance, genre, telephone):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # Vérifier si l'email existe déjà
        c.execute("SELECT id FROM utilisateurs WHERE email=?", (email,))
        if c.fetchone():
            conn.close()
            return False, "Cet email est déjà utilisé."
        
        # Hash du mot de passe
        hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
        
        # Insertion du nouveau visiteur
        c.execute('''
        INSERT INTO utilisateurs 
        (nom, prenom, email, mot_de_passe, role, date_naissance, genre, telephone) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nom, prenom, email, hashed_pwd, "visitor", date_naissance, genre, telephone))
        
        conn.commit()
        conn.close()
        return True, "Inscription réussie !"
    except Exception as e:
        conn.close()
        return False, f"Erreur lors de l'inscription: {str(e)}"

# Fonction pour vérifier si un email existe
def check_email_exists(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id FROM utilisateurs WHERE email=?", (email,))
    result = c.fetchone()
    conn.close()
    return result is not None

# Fonction pour mettre à jour le mot de passe
def update_password(email, new_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Vérifier si l'utilisateur est un administrateur
    c.execute("SELECT role FROM utilisateurs WHERE email=?", (email,))
    user_role = c.fetchone()
    
    if user_role and user_role[0] == 'admin':
        conn.close()
        return False, "La réinitialisation du mot de passe n'est pas autorisée pour les comptes administrateurs."
    
    hashed_pwd = hashlib.sha256(new_password.encode()).hexdigest()
    try:
        c.execute("UPDATE utilisateurs SET mot_de_passe=? WHERE email=?", (hashed_pwd, email))
        conn.commit()
        conn.close()
        return True, "Mot de passe mis à jour avec succès."
    except Exception as e:
        conn.close()
        return False, f"Erreur lors de la mise à jour du mot de passe: {str(e)}"

# Fonction pour rechercher dans le contenu des PDFs
def search_in_pdf_content(query):
    """Recherche dans le contenu des PDFs."""
    if not query:
        return pd.DataFrame()
        
    conn = sqlite3.connect(DB_PATH)
    search_query = f"%{query}%"
    
    try:
        sql = """
        SELECT DISTINCT m.id, m.titre, m.auteurs, m.encadreur, m.resume, m.fichier_url, 
               m.tags, f.nom as filiere_nom, s.annee_universitaire, m.version, 
               m.date_ajout, e.nom as entite_nom,
               pc.page_num,
               pc.content as full_content,
               substr(pc.content, max(0, instr(lower(pc.content), lower(?)) - 100), 200) as context
        FROM memoires m
        JOIN filieres f ON m.filiere_id = f.id
        JOIN sessions s ON m.session_id = s.id
        JOIN entites e ON f.entite_id = e.id
        JOIN pdf_content pc ON m.id = pc.memoire_id
        WHERE lower(pc.content) LIKE lower(?)
        ORDER BY m.date_ajout DESC
        """
        
        df = pd.read_sql_query(sql, conn, params=(query, search_query))
        
        if not df.empty:
            # Améliorer l'affichage du contexte
            def highlight_context(row):
                text = row['full_content']
                query_lower = query.lower()
                start_idx = text.lower().find(query_lower)
                if start_idx != -1:
                    start = max(0, start_idx - 100)
                    end = min(len(text), start_idx + len(query) + 100)
                    context = text[start:end]
                    # Mettre en évidence le terme recherché
                    context = context.replace(query, f"**{query}**")
                    return f"...{context}..."
                return row['context']
            
            df['context'] = df.apply(highlight_context, axis=1)
            df = df.drop('full_content', axis=1)
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la recherche dans le contenu PDF : {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

def bulk_import_memoires(metadata_file, pdf_folder):
    """
    Importe en masse des mémoires à partir d'un fichier Excel/CSV et d'un dossier de PDFs.
    
    Le fichier Excel/CSV doit contenir les colonnes suivantes:
    - titre
    - auteurs
    - encadreur
    - resume
    - tags
    - filiere_nom (nom exact de la filière)
    - annee_universitaire (doit exister dans la base)
    - version (optionnel)
    - nom_fichier (nom du fichier PDF dans le dossier)
    """
    try:
        # Lecture du fichier de métadonnées
        if metadata_file.name.endswith('.csv'):
            df = pd.read_csv(metadata_file)
        else:
            df = pd.read_excel(metadata_file)
        
        # Connexion à la base de données
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Récupération des mappings filières et sessions
        filieres_df = pd.read_sql("SELECT id, nom FROM filieres", conn)
        filieres_map = dict(zip(filieres_df['nom'], filieres_df['id']))
        
        sessions_df = pd.read_sql("SELECT id, annee_universitaire FROM sessions", conn)
        sessions_map = dict(zip(sessions_df['annee_universitaire'], sessions_df['id']))
        
        # Compteurs pour le rapport
        success_count = 0
        error_count = 0
        errors = []
        
        # Traitement de chaque ligne
        for idx, row in df.iterrows():
            try:
                # Vérification des champs obligatoires
                if pd.isna(row['titre']) or pd.isna(row['auteurs']) or pd.isna(row['encadreur']) or \
                   pd.isna(row['resume']) or pd.isna(row['filiere_nom']) or \
                   pd.isna(row['annee_universitaire']) or pd.isna(row['nom_fichier']):
                    raise ValueError(f"Ligne {idx+2}: Champs obligatoires manquants")
                
                # Vérification de l'existence de la filière
                if row['filiere_nom'] not in filieres_map:
                    raise ValueError(f"Ligne {idx+2}: Filière '{row['filiere_nom']}' non trouvée")
                
                # Vérification de l'existence de la session
                if row['annee_universitaire'] not in sessions_map:
                    raise ValueError(f"Ligne {idx+2}: Année universitaire '{row['annee_universitaire']}' non trouvée")
                
                # Vérification et traitement du fichier PDF
                pdf_path = os.path.join(pdf_folder, row['nom_fichier'])
                if not os.path.exists(pdf_path):
                    raise ValueError(f"Ligne {idx+2}: Fichier PDF '{row['nom_fichier']}' non trouvé")
                
                # Copie et enregistrement du PDF
                with open(pdf_path, 'rb') as pdf_file:
                    new_filename = f"{uuid.uuid4()}.pdf"
                    success, stored_path = storage.save_file(pdf_file, new_filename)
                    
                    if not success:
                        raise ValueError(f"Ligne {idx+2}: Erreur lors de l'enregistrement du PDF")
                
                # Insertion dans la base de données
                date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("""
                INSERT INTO memoires 
                (titre, auteurs, encadreur, resume, fichier_url, tags, filiere_id, session_id, version, date_ajout)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['titre'],
                    row['auteurs'],
                    row['encadreur'],
                    row['resume'],
                    stored_path,
                    row.get('tags', ''),
                    filieres_map[row['filiere_nom']],
                    sessions_map[row['annee_universitaire']],
                    row.get('version', ''),
                    date_now
                ))
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(str(e))
                continue
        
        conn.commit()
        conn.close()
        
        return True, {
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }
        
    except Exception as e:
        return False, str(e)

def bulk_import_structure_and_memoires(structure_file, metadata_file, pdf_folder):
    """
    Importe la structure complète (entités, filières, sessions) et les mémoires.
    
    Le fichier structure_file (Excel/CSV) doit contenir 3 feuilles/fichiers :
    - entites: nom
    - filieres: nom, entite_nom
    - sessions: annee_universitaire
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # 1. Import des entités
        if structure_file.name.endswith('.csv'):
            entites_df = pd.read_csv(structure_file)
        else:
            entites_df = pd.read_excel(structure_file, sheet_name='entites')
        
        entites_map = {}  # Pour stocker les IDs des entités créées
        for _, row in entites_df.iterrows():
            try:
                c.execute("INSERT INTO entites (nom) VALUES (?)", (row['nom'],))
                entites_map[row['nom']] = c.lastrowid
            except sqlite3.IntegrityError:
                # Si l'entité existe déjà, récupérer son ID
                c.execute("SELECT id FROM entites WHERE nom=?", (row['nom'],))
                entites_map[row['nom']] = c.fetchone()[0]
        
        # 2. Import des filières
        if structure_file.name.endswith('.csv'):
            filieres_df = pd.read_csv(structure_file)
        else:
            filieres_df = pd.read_excel(structure_file, sheet_name='filieres')
        
        filieres_map = {}  # Pour stocker les IDs des filières créées
        for _, row in filieres_df.iterrows():
            try:
                entite_id = entites_map[row['entite_nom']]
                c.execute("INSERT INTO filieres (nom, entite_id) VALUES (?, ?)", 
                         (row['nom'], entite_id))
                filieres_map[row['nom']] = c.lastrowid
            except sqlite3.IntegrityError:
                # Si la filière existe déjà, récupérer son ID
                c.execute("SELECT id FROM filieres WHERE nom=? AND entite_id=?", 
                         (row['nom'], entite_id))
                filieres_map[row['nom']] = c.fetchone()[0]
        
        # 3. Import des sessions
        if structure_file.name.endswith('.csv'):
            sessions_df = pd.read_csv(structure_file)
        else:
            sessions_df = pd.read_excel(structure_file, sheet_name='sessions')
        
        sessions_map = {}  # Pour stocker les IDs des sessions créées
        for _, row in sessions_df.iterrows():
            try:
                c.execute("INSERT INTO sessions (annee_universitaire) VALUES (?)", 
                         (row['annee_universitaire'],))
                sessions_map[row['annee_universitaire']] = c.lastrowid
            except sqlite3.IntegrityError:
                # Si la session existe déjà, récupérer son ID
                c.execute("SELECT id FROM sessions WHERE annee_universitaire=?", 
                         (row['annee_universitaire'],))
                sessions_map[row['annee_universitaire']] = c.fetchone()[0]
        
        conn.commit()
        
        # 4. Import des mémoires
        if metadata_file.name.endswith('.csv'):
            memoires_df = pd.read_csv(metadata_file)
        else:
            memoires_df = pd.read_excel(metadata_file)
        
        success_count = 0
        error_count = 0
        errors = []
        
        for idx, row in memoires_df.iterrows():
            try:
                # Vérification des champs obligatoires
                if pd.isna(row['titre']) or pd.isna(row['auteurs']) or \
                   pd.isna(row['encadreur']) or pd.isna(row['resume']) or \
                   pd.isna(row['filiere_nom']) or pd.isna(row['annee_universitaire']) or \
                   pd.isna(row['nom_fichier']):
                    raise ValueError(f"Ligne {idx+2}: Champs obligatoires manquants")
                
                # Vérification du fichier PDF
                pdf_path = os.path.join(pdf_folder, row['nom_fichier'])
                if not os.path.exists(pdf_path):
                    raise ValueError(f"Ligne {idx+2}: Fichier PDF '{row['nom_fichier']}' non trouvé")
                
                # Copie et enregistrement du PDF
                with open(pdf_path, 'rb') as pdf_file:
                    new_filename = f"{uuid.uuid4()}.pdf"
                    success, stored_path = storage.save_file(pdf_file, new_filename)
                    
                    if not success:
                        raise ValueError(f"Ligne {idx+2}: Erreur lors de l'enregistrement du PDF")
                
                # Insertion du mémoire
                date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                c.execute("""
                INSERT INTO memoires 
                (titre, auteurs, encadreur, resume, fichier_url, tags, filiere_id, session_id, version, date_ajout)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['titre'],
                    row['auteurs'],
                    row['encadreur'],
                    row['resume'],
                    stored_path,
                    row.get('tags', ''),
                    filieres_map[row['filiere_nom']],
                    sessions_map[row['annee_universitaire']],
                    row.get('version', ''),
                    date_now
                ))
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(str(e))
                continue
        
        conn.commit()
        conn.close()
        
        return True, {
            'entites_count': len(entites_map),
            'filieres_count': len(filieres_map),
            'sessions_count': len(sessions_map),
            'memoires_success': success_count,
            'memoires_error': error_count,
            'errors': errors
        }
        
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return False, str(e)

# Initialiser la base de données
init_db()

# Session state pour l'authentification
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.user_role = None

# Interface utilisateur
def main():
    # Sidebar pour la navigation (toujours visible)
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; color: #262730; padding: 1rem;'>
                <h1 style='font-size: 1.5em; font-weight: bold; margin-bottom: 1rem;'>🎓 Mémoires Universitaires (UNSTIM)</h1>
                <h2 style='font-size: 1.2em; margin-bottom: 0.5rem;'>Auteurs</h2>
                <p style='font-size: 1em; margin-bottom: 0.3rem;'>B. Zamane SOULEMANE</p>
                <p style='font-size: 1em; margin-bottom: 1rem;'>A. Elisé LOKOSSOU</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Affichage conditionnel en fonction de l'authentification
    if not st.session_state.logged_in:
        show_login_page()
    else:
        # Menu pour l'administrateur ou l'utilisateur normal
        with st.sidebar:
            if st.session_state.user_role == "admin":
                menu = st.radio("Navigation", 
                    ["Accueil", "Recherche", "Statistiques", "Gestion des Entités", 
                    "Gestion des Filières", "Gestion des Sessions", "Gestion des Mémoires", "Journal d'activité"])
            else:
                menu = st.radio("Navigation", ["Accueil", "Recherche", "Statistiques"])
            
            # Affichage du nom d'utilisateur connecté
            st.write(f"👤 Connecté en tant que : **{st.session_state.user_name}**")
            if st.button("Déconnexion"):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.user_name = None
                st.session_state.user_role = None
                st.rerun()
        
        # Création d'un conteneur principal pour le contenu
        main_container = st.container()
        
        with main_container:
            # Navigation vers les différentes pages
            if menu == "Accueil":
                show_home_page()
            elif menu == "Recherche":
                show_search_page()
            elif menu == "Statistiques":
                show_statistics_page()
            elif menu == "Gestion des Entités" and st.session_state.user_role == "admin":
                show_entities_management()
            elif menu == "Gestion des Filières" and st.session_state.user_role == "admin":
                show_filieres_management()
            elif menu == "Gestion des Sessions" and st.session_state.user_role == "admin":
                show_sessions_management()
            elif menu == "Gestion des Mémoires" and st.session_state.user_role == "admin":
                show_memoires_management()
            elif menu == "Journal d'activité" and st.session_state.user_role == "admin":
                show_logs()

def show_login_page():
    # Initialisation des variables de session si elles n'existent pas
    if 'show_reset' not in st.session_state:
        st.session_state.show_reset = False
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    
    st.title("📚 Banque des Mémoires de l'UNSTIM")
    
    # Créer une mise en page centrée
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Carte de connexion
        st.markdown("""
        <div style="padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        """, unsafe_allow_html=True)
        
        # Champs de connexion
        email = st.text_input("", placeholder="Email ou numéro de téléphone", key="login_email")
        password = st.text_input("", placeholder="Mot de passe", type="password", key="login_password")
        
        # Bouton de connexion
        login_pressed = st.button("Se connecter", key="login", use_container_width=True)
        
        # Lien mot de passe oublié
        forgot_password = st.button("Mot de passe oublié ?", type="secondary", key="forgot_password", use_container_width=False)
        
        # Ligne de séparation
        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        
        # Bouton Créer un nouveau compte
        create_account = st.button("Créer un nouveau compte", key="create_account", use_container_width=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Traitement de la connexion
        if login_pressed:
            if email and password:
                user = check_auth(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user[0]
                    st.session_state.user_name = user[1]
                    st.session_state.user_role = user[2]
                    
                    if email == "admin@universite.com" and user[2] == "admin":
                        add_log(f"Connexion réussie (admin)", user[0])
                    else:
                        add_log(f"Connexion réussie (visiteur)", user[0])
                    
                    st.success("Connexion réussie !")
                    time.sleep(1)
                    return True
                else:
                    st.error("Email ou mot de passe incorrect.")
                    add_log(f"Tentative de connexion échouée avec l'email: {email}")
            else:
                st.warning("Veuillez remplir tous les champs.")
        
        # Traitement du mot de passe oublié
        if forgot_password:
            st.session_state.show_reset = True
            st.rerun()
        
        # Redirection vers la page d'inscription
        if create_account:
            st.session_state.show_register = True
            st.rerun()
    
    # Afficher le formulaire approprié selon l'état
    if 'show_register' in st.session_state and st.session_state.show_register:
        show_register_page()
        return False
    elif 'show_reset' in st.session_state and st.session_state.show_reset:
        show_reset_password_page()
        return False
    
    return False

def show_register_page():
    # Créer une mise en page centrée pour l'inscription
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        <h2 style='text-align: center; margin-bottom: 20px;'>Inscription</h2>
        <p style='text-align: center;'>C'est gratuit et ça le restera toujours.</p>
        """, unsafe_allow_html=True)
        
        # Nom et prénom sur la même ligne
        nom_col, prenom_col = st.columns(2)
        with nom_col:
            nom = st.text_input("", placeholder="Nom", key="register_nom")
        with prenom_col:
            prenom = st.text_input("", placeholder="Prénom", key="register_prenom")
        
        # Email et téléphone
        email = st.text_input("", placeholder="Email", key="register_email")
        telephone = st.text_input("", placeholder="Numéro de mobile", key="register_telephone")
        
        # Mot de passe
        password = st.text_input("", placeholder="Nouveau mot de passe", type="password", key="register_password")
        password_confirm = st.text_input("", placeholder="Confirmer mot de passe", type="password", key="register_password_confirm")
        
        # Date de naissance
        st.write("Date de naissance")
        date_col1, date_col2, date_col3 = st.columns(3)
        with date_col1:
            jour = st.selectbox("Jour", range(1, 32), key="register_jour")
        with date_col2:
            mois = st.selectbox("Mois", ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", 
                                       "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"], 
                              key="register_mois")
        with date_col3:
            annee = st.selectbox("Année", range(2024, 1900, -1), key="register_annee")
        
        # Genre
        st.write("Genre")
        genre = st.radio("", ["Homme", "Femme", "Personnalisé"], horizontal=True, key="register_genre")
        
        # Conditions d'utilisation
        st.markdown("""
        <p style='font-size: 12px; color: #777; text-align: center;'>
        En cliquant sur S'inscrire, vous acceptez nos Conditions générales. 
        Découvrez comment nous recueillons, utilisons et partageons vos données 
        en lisant notre Politique d'utilisation des données.
        </p>
        """, unsafe_allow_html=True)
        
        # Boutons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Retour", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()
        with col2:
            register_pressed = st.button("S'inscrire", use_container_width=True, key="register")
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if register_pressed:
            if nom and prenom and email and password and password_confirm and telephone:
                if password != password_confirm:
                    st.error("Les mots de passe ne correspondent pas.")
                else:
                    # Formatage de la date
                    mois_num = {"Janvier": 1, "Février": 2, "Mars": 3, "Avril": 4, "Mai": 5, "Juin": 6,
                              "Juillet": 7, "Août": 8, "Septembre": 9, "Octobre": 10, "Novembre": 11, "Décembre": 12}
                    date_naissance = f"{annee}-{mois_num[mois]:02d}-{jour:02d}"
                    
                    success, message = register_visitor(nom, prenom, email, password, date_naissance, genre, telephone)
                    if success:
                        st.success(message)
                        add_log(f"Nouvelle inscription visiteur: {email}")
                        st.session_state.show_register = False
                    else:
                        st.error(message)
            else:
                st.warning("Veuillez remplir tous les champs obligatoires.")

def show_reset_password_page():
    # Créer une mise en page centrée
    col1, col2, col3 = st.columns([1, 2, 1])
    
    # Initialisation des variables de session si elles n'existent pas
    if 'reset_step' not in st.session_state:
        st.session_state.reset_step = 1
    if 'temp_email' not in st.session_state:
        st.session_state.temp_email = ""
    
    with col2:
        st.markdown("""
        <div style="padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);">
        <h2 style='text-align: center; margin-bottom: 20px;'>Réinitialisation du mot de passe</h2>
        """, unsafe_allow_html=True)
        
        if st.session_state.reset_step == 1:
            # Étape 1 : Saisie de l'email
            st.write("Veuillez entrer votre adresse email pour réinitialiser votre mot de passe.")
            email = st.text_input("", placeholder="Votre adresse email", key="reset_email")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Retour", use_container_width=True):
                    st.session_state.show_reset = False
                    st.rerun()
            with col2:
                if st.button("Continuer", use_container_width=True):
                    if email:
                        if check_email_exists(email):
                            st.session_state.temp_email = email
                            st.session_state.reset_step = 2
                            st.rerun()
                        else:
                            st.error("Cette adresse email n'existe pas dans notre système.")
                    else:
                        st.warning("Veuillez entrer votre adresse email.")
        
        elif st.session_state.reset_step == 2:
            # Étape 2 : Nouveau mot de passe
            st.write(f"Créez un nouveau mot de passe pour {st.session_state.temp_email}")
            
            new_password = st.text_input("", placeholder="Nouveau mot de passe", type="password", key="new_password")
            confirm_password = st.text_input("", placeholder="Confirmer le mot de passe", type="password", key="confirm_password")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Retour", use_container_width=True):
                    st.session_state.reset_step = 1
                    st.rerun()
            with col2:
                if st.button("Réinitialiser", use_container_width=True):
                    if new_password and confirm_password:
                        if new_password == confirm_password:
                            success, message = update_password(st.session_state.temp_email, new_password)
                            if success:
                                st.success(message)
                                add_log(f"Réinitialisation du mot de passe pour: {st.session_state.temp_email}")
                                # Réinitialiser les variables de session
                                st.session_state.reset_step = 1
                                st.session_state.temp_email = ""
                                st.session_state.show_reset = False
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.error("Les mots de passe ne correspondent pas.")
                    else:
                        st.warning("Veuillez remplir tous les champs.")
        
        st.markdown("</div>", unsafe_allow_html=True)

def show_page_title(title, icon=""):
    """Fonction utilitaire pour afficher un titre de page de manière cohérente"""
    st.markdown(f"""
        <h1 style='color: rgb(49, 51, 63); font-size: 2rem; font-weight: 700;'>{icon} {title}</h1>
    """, unsafe_allow_html=True)

def show_subtitle(text):
    """Fonction utilitaire pour afficher un sous-titre"""
    st.markdown(f'<h2 class="subtitle-text">{text}</h2>', unsafe_allow_html=True)

def show_home_page():
    st.header("📚 Plateforme de Gestion des Mémoires Universitaires")
    st.write("Bienvenue sur la plateforme centrale des mémoires de soutenance de l'université.")
    
    st.subheader("Derniers mémoires ajoutés")
    latest_memoires = get_all_memoires().head(5)
    
    if len(latest_memoires) == 0:
        st.info("Aucun mémoire n'a encore été ajouté.")
    else:
        for _, memoire in latest_memoires.iterrows():
            with st.expander(f"{memoire['titre']} - {memoire['auteurs']} ({memoire['annee_universitaire']})"):
                st.write(f"**Encadreur:** {memoire['encadreur']}")
                st.write(f"**Filière:** {memoire['filiere_nom']} - {memoire['entite_nom']}")
                st.write(f"**Résumé:** {memoire['resume'][:200]}..." if len(memoire['resume']) > 200 else f"**Résumé:** {memoire['resume']}")
                st.markdown(f"**Mots-clés:** {memoire['tags']}")
                
                # Lien vers la page de recherche pour voir les détails
                st.markdown(f"[🔍 Voir les détails dans la page Recherche](/Recherche?memoire_id={memoire['id']})", unsafe_allow_html=True)
    
    # Guide d'utilisation rapide
    st.subheader("Guide d'utilisation")
    st.write("""
    - Utilisez l'onglet **Recherche** pour trouver des mémoires par mots-clés, entité, filière ou année.
    - Consultez les **Statistiques** pour avoir une vue d'ensemble des mémoires disponibles.
    - Les administrateurs peuvent gérer les entités, filières, sessions et mémoires.
    """)

def show_memoire_details(memoire_id):
    memoire = get_memoire_details(memoire_id)
    
    if memoire is None:
        st.error("Ce mémoire n'existe pas ou a été supprimé.")
        if 'selected_memoire' in st.session_state:
            del st.session_state.selected_memoire
        st.rerun()
        return
    
    st.title(memoire['titre'])
    
    # Afficher les détails du document
    st.subheader("Détails du document")
    st.write(f"**Auteur(s):** {memoire['auteurs']}")
    st.write(f"**Encadreur:** {memoire['encadreur']}")
    st.write(f"**Filière:** {memoire['filiere_nom']} - {memoire['entite_nom']}")
    st.write(f"**Année universitaire:** {memoire['annee_universitaire']}")
    if memoire['version']:
        st.write(f"**Version:** {memoire['version']}")
    st.write(f"**Date d'ajout:** {memoire['date_ajout']}")
    
    st.subheader("Résumé")
    st.write(memoire['resume'])
    
    st.subheader("Mots-clés")
    st.write(memoire['tags'])
    
    # Afficher les actions
    st.subheader("Actions")
    if memoire['fichier_url'].startswith("local://"):
        action_col1, action_col2 = st.columns(2)
        with action_col1:
            st.markdown(get_download_link(memoire['fichier_url'], "📥 Télécharger le PDF"), unsafe_allow_html=True)
        with action_col2:
            if st.button("📄 Consulter en ligne"):
                display_pdf(memoire['fichier_url'])

def show_search_page():
    st.header("🔍 Recherche de Mémoires")
    st.markdown("---")
    container = st.container()
    with container:
        # Formulaire de recherche
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input("Rechercher un mémoire", placeholder="Titre, auteur, mots-clés...")
        
        with col2:
            search_button = st.button("🔍 Rechercher")
        
        # Filtres avancés
        with st.expander("Filtres avancés"):
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            # Filtre par entité
            entities = get_all_entities()
            entity_options = [("", "Toutes les entités")] + [(str(row['id']), row['nom']) for _, row in entities.iterrows()]
            with filter_col1:
                selected_entity = st.selectbox("Entité", 
                                              options=[id for id, _ in entity_options],
                                              format_func=lambda x: next((name for id, name in entity_options if id == x), ""),
                                              key="search_entity")
            
            # Filtre par filière (dynamique en fonction de l'entité)
            with filter_col2:
                if selected_entity:
                    filieres = get_filieres_by_entity(selected_entity)
                    filiere_options = [("", "Toutes les filières")] + [(str(row['id']), row['nom']) for _, row in filieres.iterrows()]
                    selected_filiere = st.selectbox("Filière", 
                                                   options=[id for id, _ in filiere_options],
                                                   format_func=lambda x: next((name for id, name in filiere_options if id == x), ""),
                                                   key="search_filiere")
                else:
                    selected_filiere = None
                    st.selectbox("Filière", ["Sélectionnez d'abord une entité"], disabled=True)
            
            # Filtre par année
            with filter_col3:
                sessions = get_all_sessions()
                session_options = [("", "Toutes les années")] + [(str(row['id']), row['annee_universitaire']) for _, row in sessions.iterrows()]
                selected_session = st.selectbox("Année universitaire", 
                                               options=[id for id, _ in session_options],
                                               format_func=lambda x: next((name for id, name in session_options if id == x), ""),
                                               key="search_session")
        
        # Exécution de la recherche
        if search_button or search_query:
            results = search_memoires(search_query, 
                                    selected_entity if selected_entity else None,
                                    selected_filiere if selected_filiere else None,
                                    selected_session if selected_session else None)
            
            st.subheader(f"Résultats ({len(results)} mémoires trouvés)")
            
            if len(results) == 0:
                st.info("Aucun mémoire ne correspond à votre recherche.")
            else:
                # Utiliser des conteneurs séparés pour chaque mémoire
                for idx, memoire in results.iterrows():
                    memoire_container = st.container()
                    
                    with memoire_container:
                        with st.expander(f"{memoire['titre']} - {memoire['auteurs']} ({memoire['annee_universitaire']})"):
                            st.write(f"**Encadreur:** {memoire['encadreur']}")
                            st.write(f"**Filière:** {memoire['filiere_nom']} - {memoire['entite_nom']}")
                            st.write(f"**Résumé:** {memoire['resume'][:200]}..." if len(memoire['resume']) > 200 else f"**Résumé:** {memoire['resume']}")
                            st.markdown(f"**Mots-clés:** {memoire['tags']}")
                            
                            # Créer des colonnes pour les actions
                            action_cols = st.columns([1, 1])
                            
                            # Colonne pour le téléchargement
                            with action_cols[0]:
                                if memoire['fichier_url'].startswith("local://"):
                                    file_content = storage.get_file(memoire['fichier_url'])
                                    if file_content:
                                        filename = os.path.basename(memoire['fichier_url'].replace("local://", ""))
                                        st.download_button(
                                            "📥 Télécharger le PDF",
                                            data=file_content,
                                            file_name=filename,
                                            mime="application/pdf",
                                            key=f"download_{memoire['id']}"
                                        )
                            
                            # Colonne pour la consultation
                            with action_cols[1]:
                                if st.button("📄 Consulter en ligne", key=f"view_{memoire['id']}", use_container_width=True):
                                    st.session_state[f"show_pdf_{memoire['id']}"] = True
                            
                            # Afficher le PDF si demandé
                            if st.session_state.get(f"show_pdf_{memoire['id']}", False):
                                display_pdf(memoire['fichier_url'])

def show_statistics_page():
    st.header("📊 Statistiques")
    st.markdown("---")
    container = st.container()
    with container:
        stats = get_statistics()
        
        st.subheader("Vue d'ensemble")
        st.info(f"Total des mémoires disponibles : {stats['total_memoires']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Mémoires par entité")
            if not stats['memoires_par_entite'].empty:
                st.bar_chart(stats['memoires_par_entite'].set_index('nom'))
            else:
                st.info("Aucune donnée disponible")
            
            st.subheader("Mémoires par filière (Top 10)")
            if not stats['memoires_par_filiere'].empty:
                st.bar_chart(stats['memoires_par_filiere'].set_index('nom'))
            else:
                st.info("Aucune donnée disponible")
        
        with col2:
            st.subheader("Mémoires par année universitaire")
            if not stats['memoires_par_annee'].empty:
                # Inverser l'ordre pour avoir les années les plus récentes à droite
                chart_data = stats['memoires_par_annee'].sort_values('annee_universitaire')
                st.bar_chart(chart_data.set_index('annee_universitaire'))
            else:
                st.info("Aucune donnée disponible")

def show_entities_management():
    st.header("🏢 Gestion des Entités")
    st.markdown("---")
    container = st.container()
    with container:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Ajouter une entité")
            
            entity_name = st.text_input("Nom de l'entité", key="entity_name")
            
            if st.button("Ajouter l'entité"):
                if entity_name:
                    if add_entity(entity_name):
                        add_log(f"Ajout de l'entité: {entity_name}", st.session_state.user_id)
                        st.success(f"L'entité '{entity_name}' a été ajoutée avec succès.")
                        #st.session_state.entity_name = ""
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"L'entité '{entity_name}' existe déjà.")
                else:
                    st.warning("Veuillez saisir un nom d'entité.")
        
        with col2:
            st.subheader("Liste des entités")
            
            entities = get_all_entities()
            
            if entities.empty:
                st.info("Aucune entité n'a été ajoutée.")
            else:
                for _, entity in entities.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(entity['nom'])
                    with col2:
                        if st.button("Supprimer", key=f"delete_entity_{entity['id']}"):
                            success, message = delete_entity(entity['id'])
                            if success:
                                add_log(f"Suppression de l'entité: {entity['nom']}", st.session_state.user_id)
                                st.success(message)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(message)

def show_filieres_management():
    st.header("🎓 Gestion des Filières")
    st.markdown("---")
    container = st.container()
    with container:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Ajouter une filière")
            
            # Sélection de l'entité parente
            entities = get_all_entities()
            if entities.empty:
                st.warning("Vous devez d'abord ajouter des entités.")
                if st.button("Aller à la gestion des entités"):
                    show_entities_management()
                    return
            else:
                entity_options = [(row['id'], row['nom']) for _, row in entities.iterrows()]
                selected_entity = st.selectbox("Entité parente", 
                                              options=[id for id, _ in entity_options],
                                              format_func=lambda x: next((name for id, name in entity_options if id == x), ""),
                                              key="parent_entity")
                
                # Nom de la filière
                filiere_name = st.text_input("Nom de la filière", key="filiere_name")
                
                if st.button("Ajouter la filière"):
                    if filiere_name:
                        success, message = add_filiere(filiere_name, selected_entity)
                        if success:
                            add_log(f"Ajout de la filière: {filiere_name} dans l'entité ID {selected_entity}", st.session_state.user_id)
                            st.success(message)
                            #st.session_state.filiere_name = ""
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Veuillez saisir un nom de filière.")
        
        with col2:
            st.subheader("Liste des filières")
            
            filieres = get_all_filieres()
            
            if filieres.empty:
                st.info("Aucune filière n'a été ajoutée.")
            else:
                # Grouper par entité
                entities_unique = filieres['entite_nom'].unique()
                
                for entity in entities_unique:
                    st.write(f"**{entity}**")
                    entity_filieres = filieres[filieres['entite_nom'] == entity]
                    
                    for _, filiere in entity_filieres.iterrows():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(filiere['nom'])
                        with col2:
                            if st.button("Supprimer", key=f"delete_filiere_{filiere['id']}"):
                                success, message = delete_filiere(filiere['id'])
                                if success:
                                    add_log(f"Suppression de la filière: {filiere['nom']}", st.session_state.user_id)
                                    st.success(message)
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(message)
                    st.write("---")

def show_sessions_management():
    st.header("📅 Gestion des Sessions")
    st.markdown("---")
    container = st.container()
    with container:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Ajouter une session")
            
            session_name = st.text_input("Année universitaire (ex: 2024-2025)", key="session_name")
            
            if st.button("Ajouter la session"):
                if session_name:
                    success, message = add_session(session_name)
                    if success:
                        add_log(f"Ajout de la session: {session_name}", st.session_state.user_id)
                        st.success(message)
                        #st.session_state.session_name = ""
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Veuillez saisir une année universitaire.")
        
        with col2:
            st.subheader("Liste des sessions")
            
            sessions = get_all_sessions()
            
            if sessions.empty:
                st.info("Aucune session n'a été ajoutée.")
            else:
                for _, session in sessions.iterrows():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(session['annee_universitaire'])
                    with col2:
                        if st.button("Supprimer", key=f"delete_session_{session['id']}"):
                            success, message = delete_session(session['id'])
                            if success:
                                add_log(f"Suppression de la session: {session['annee_universitaire']}", st.session_state.user_id)
                                st.success(message)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(message)

def show_memoires_management():
    st.header("📚 Gestion des Mémoires")
    st.markdown("---")
    container = st.container()
    with container:
        # Si en mode édition d'un mémoire
        if 'edit_memoire' in st.session_state:
            memoire_id = st.session_state.edit_memoire
            memoire = get_memoire_details(memoire_id)
            
            if memoire is None:
                st.error("Ce mémoire n'existe pas ou a été supprimé.")
                del st.session_state.edit_memoire
                st.rerun()
            else:
                st.subheader(f"Modifier le mémoire : {memoire['titre']}")
                
                # Formulaire de modification
                with st.form(key="edit_memoire_form"):
                    titre = st.text_input("Titre", value=memoire['titre'])
                    auteurs = st.text_input("Auteur(s)", value=memoire['auteurs'])
                    encadreur = st.text_input("Encadreur", value=memoire['encadreur'])
                    resume = st.text_area("Résumé", value=memoire['resume'], height=150)
                    tags = st.text_input("Mots-clés", value=memoire['tags'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Sélection de l'entité et filière
                        entities = get_all_entities()
                        entity_options = [(row['id'], row['nom']) for _, row in entities.iterrows()]
                        
                        # Trouver l'entité actuelle
                        current_entity = next((ent[0] for ent in entity_options if ent[1] == memoire['entite_nom']), None)
                        
                        selected_entity = st.selectbox(
                            "Entité",
                            options=[id for id, _ in entity_options],
                            format_func=lambda x: next((name for id, name in entity_options if id == x), ""),
                            key="edit_entity",
                            index=entity_options.index((current_entity, memoire['entite_nom'])) if current_entity else 0
                        )
                        
                        # Filières de l'entité sélectionnée
                        filieres = get_filieres_by_entity(selected_entity)
                        filiere_options = [(row['id'], row['nom']) for _, row in filieres.iterrows()]
                        
                        # Trouver la filière actuelle
                        current_filiere = memoire['filiere_id']
                        filiere_index = next((i for i, (id, _) in enumerate(filiere_options) if id == current_filiere), 0)
                        
                        selected_filiere = st.selectbox(
                            "Filière",
                            options=[id for id, _ in filiere_options],
                            format_func=lambda x: next((name for id, name in filiere_options if id == x), ""),
                            key="edit_filiere",
                            index=filiere_index
                        )
                    
                    with col2:
                        # Sélection de la session
                        sessions = get_all_sessions()
                        session_options = [(row['id'], row['annee_universitaire']) for _, row in sessions.iterrows()]
                        
                        # Trouver la session actuelle
                        current_session = memoire['session_id']
                        session_index = next((i for i, (id, _) in enumerate(session_options) if id == current_session), 0)
                        
                        selected_session = st.selectbox(
                            "Année universitaire",
                            options=[id for id, _ in session_options],
                            format_func=lambda x: next((name for id, name in session_options if id == x), ""),
                            key="edit_session",
                            index=session_index
                        )
                        
                        version = st.text_input("Version", value=memoire['version'])
                    
                    # Upload d'un nouveau PDF (optionnel)
                    st.write("PDF actuel :", memoire['fichier_url'])
                    uploaded_pdf = st.file_uploader("Nouveau PDF (optionnel)", type=['pdf'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        cancel = st.form_submit_button("Annuler")
                    with col2:
                        submit = st.form_submit_button("Enregistrer")
                    
                    if cancel:
                        del st.session_state.edit_memoire
                        st.rerun()
                    
                    if submit:
                        if not titre or not auteurs or not encadreur or not resume or not selected_filiere or not selected_session:
                            st.error("Veuillez remplir tous les champs obligatoires.")
                        else:
                            # Si un nouveau PDF est uploadé
                            pdf_path = None
                            if uploaded_pdf:
                                filename = f"{uuid.uuid4()}.pdf"
                                success, pdf_path = save_pdf(uploaded_pdf, filename)
                                if not success:
                                    st.error("Erreur lors de l'enregistrement du nouveau PDF.")
                                    return
                            
                            # Mise à jour du mémoire
                            success, message = update_memoire(
                                memoire_id, titre, auteurs, encadreur, resume,
                                pdf_path, tags, selected_filiere, selected_session, version
                            )
                            
                            if success:
                                add_log(f"Modification du mémoire: {titre}", st.session_state.user_id)
                                st.success(message)
                                del st.session_state.edit_memoire
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(message)
                                if pdf_path and os.path.exists(pdf_path):
                                    os.remove(pdf_path)
                
                return

        # Sinon, afficher les onglets
        tab1, tab2, tab3, tab4 = st.tabs(["Ajouter un mémoire", "Import en masse", "Import complet", "Liste des mémoires"])
        
        with tab1:
            st.subheader("Ajouter un nouveau mémoire")
            
            # Vérifier si les éléments nécessaires existent
            entities = get_all_entities()
            sessions = get_all_sessions()
            
            if entities.empty or sessions.empty:
                if entities.empty:
                    st.warning("Vous devez d'abord ajouter des entités.")
                    if st.button("Aller à la gestion des entités", key="goto_entities"):
                        show_entities_management()
                        return
                if sessions.empty:
                    st.warning("Vous devez d'abord ajouter des sessions (années universitaires).")
                    if st.button("Aller à la gestion des sessions", key="goto_sessions"):
                        show_sessions_management()
                        return
            else:
                # Formulaire d'ajout
                with st.form(key="add_memoire_form"):
                    titre = st.text_input("Titre", key="add_titre")
                    auteurs = st.text_input("Auteur(s)", key="add_auteurs")
                    encadreur = st.text_input("Encadreur", key="add_encadreur")
                    resume = st.text_area("Résumé", height=150, key="add_resume")
                    tags = st.text_input("Mots-clés (séparés par des virgules)", key="add_tags")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Sélection de l'entité et filière
                        entity_options = [(row['id'], row['nom']) for _, row in entities.iterrows()]
                        selected_entity = st.selectbox("Entité", 
                                                    options=[id for id, _ in entity_options],
                                                    format_func=lambda x: next((name for id, name in entity_options if id == x), ""),
                                                    key="add_entity")
                        
                        filieres = get_filieres_by_entity(selected_entity)
                        
                        if filieres.empty:
                            st.warning(f"Aucune filière n'est associée à cette entité. Veuillez en ajouter.")
                            selected_filiere = None
                        else:
                            filiere_options = [(row['id'], row['nom']) for _, row in filieres.iterrows()]
                            selected_filiere = st.selectbox("Filière", 
                                                        options=[id for id, _ in filiere_options],
                                                        format_func=lambda x: next((name for id, name in filiere_options if id == x), ""),
                                                        key="add_filiere")
                    
                    with col2:
                        # Sélection de la session
                        session_options = [(row['id'], row['annee_universitaire']) for _, row in sessions.iterrows()]
                        selected_session = st.selectbox("Année universitaire", 
                                                    options=[id for id, _ in session_options],
                                                    format_func=lambda x: next((name for id, name in session_options if id == x), ""),
                                                    key="add_session")
                        
                        version = st.text_input("Version (optionnel)", key="add_version")
                    
                    # Upload du fichier PDF
                    uploaded_pdf = st.file_uploader("Fichier PDF du mémoire", type=['pdf'], key="add_pdf")
                    
                    submitted = st.form_submit_button("Ajouter le mémoire")
                    
                    if submitted:
                        if not titre:
                            st.error("Le titre est obligatoire")
                        if not auteurs:
                            st.error("Le(s) auteur(s) est/sont obligatoire(s)")
                        if not encadreur:
                            st.error("L'encadreur est obligatoire")
                        if not resume:
                            st.error("Le résumé est obligatoire")
                        if not selected_filiere:
                            st.error("La filière est obligatoire")
                        if not selected_session:
                            st.error("La session est obligatoire")
                        if not uploaded_pdf:
                            st.error("Le fichier PDF est obligatoire")
                        
                        if titre and auteurs and encadreur and resume and selected_filiere and selected_session and uploaded_pdf:
                            # Enregistrer le fichier PDF
                            filename = f"{uuid.uuid4()}.pdf"
                            success, pdf_path = save_pdf(uploaded_pdf, filename)
                            
                            if success:
                                # Ajouter le mémoire à la base de données
                                success, message = add_memoire(
                                    titre, auteurs, encadreur, resume, pdf_path, 
                                    tags, selected_filiere, selected_session, version
                                )
                                
                                if success:
                                    add_log(f"Ajout du mémoire: {titre}", st.session_state.user_id)
                                    st.success(message)
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    # Supprimer le fichier en cas d'erreur
                                    if os.path.exists(pdf_path):
                                        os.remove(pdf_path)
                                    st.error(message)
                            else:
                                st.error("Erreur lors de l'enregistrement du fichier PDF.")
                        else:
                            st.warning("Veuillez remplir tous les champs obligatoires.")
        
        with tab2:
            st.subheader("Import en masse de mémoires")
            
            # Guide d'utilisation
            with st.expander("📖 Guide d'utilisation", expanded=True):
                st.markdown("""
                ### Comment utiliser l'import en masse ?
                
                1. **Préparez votre fichier Excel ou CSV** avec les colonnes suivantes :
                   - `titre` (obligatoire)
                   - `auteurs` (obligatoire)
                   - `encadreur` (obligatoire)
                   - `resume` (obligatoire)
                   - `tags` (optionnel)
                   - `filiere_nom` (obligatoire) - doit correspondre exactement au nom dans la base
                   - `annee_universitaire` (obligatoire) - doit exister dans la base
                   - `version` (optionnel)
                   - `nom_fichier` (obligatoire) - nom du fichier PDF dans le dossier
                
                2. **Préparez vos fichiers PDF** :
                   - Placez tous vos fichiers PDF dans un dossier
                   - Les noms des fichiers doivent correspondre à la colonne `nom_fichier`
                
                3. **Importez les données** :
                   - Sélectionnez votre fichier Excel/CSV
                   - Indiquez le chemin du dossier contenant les PDFs
                   - Cliquez sur "Lancer l'import"
                
                ### Remarques importantes
                
                - Vérifiez que les noms des filières correspondent exactement à ceux de la base
                - Les années universitaires doivent déjà exister dans la base
                - Les fichiers PDF doivent être nommés de manière unique
                """)
            
            # Formulaire d'import
            with st.form("import_form"):
                metadata_file = st.file_uploader(
                    "Fichier Excel/CSV des métadonnées", 
                    type=['xlsx', 'csv'],
                    help="Fichier contenant les métadonnées des mémoires"
                )
                
                pdf_folder = st.text_input(
                    "Chemin du dossier des PDFs",
                    help="Chemin absolu vers le dossier contenant tous les fichiers PDF"
                )
                
                submitted = st.form_submit_button("Lancer l'import")
                
                if submitted:
                    if not metadata_file:
                        st.error("Veuillez sélectionner un fichier de métadonnées")
                    elif not pdf_folder:
                        st.error("Veuillez indiquer le chemin du dossier des PDFs")
                    elif not os.path.exists(pdf_folder):
                        st.error("Le dossier spécifié n'existe pas")
                    else:
                        with st.spinner("Import en cours..."):
                            success, result = bulk_import_memoires(metadata_file, pdf_folder)
                            
                            if success:
                                st.success(f"""
                                Import terminé avec succès !
                                - Mémoires importés : {result['success_count']}
                                - Erreurs : {result['error_count']}
                                """)
                                
                                if result['errors']:
                                    with st.expander("Voir les erreurs"):
                                        for error in result['errors']:
                                            st.error(error)
                            else:
                                st.error(f"Erreur lors de l'import : {result}")
        
        with tab3:
            st.subheader("Import complet (Structure + Mémoires)")
            
            # Guide d'utilisation
            with st.expander("📖 Guide d'utilisation", expanded=True):
                st.markdown("""
                ### Comment utiliser l'import complet ?
                
                Cette fonction permet d'importer à la fois la structure (entités, filières, sessions) et les mémoires.
                
                1. **Préparez votre fichier Excel de structure** avec 3 feuilles :
                   
                   Feuille "entites" :
                   - `nom` (obligatoire) : Nom de l'entité
                   
                   Feuille "filieres" :
                   - `nom` (obligatoire) : Nom de la filière
                   - `entite_nom` (obligatoire) : Nom de l'entité parente
                   
                   Feuille "sessions" :
                   - `annee_universitaire` (obligatoire) : Année universitaire
                
                2. **Préparez votre fichier Excel des mémoires** avec les colonnes :
                   - `titre` (obligatoire)
                   - `auteurs` (obligatoire)
                   - `encadreur` (obligatoire)
                   - `resume` (obligatoire)
                   - `tags` (optionnel)
                   - `filiere_nom` (obligatoire) - doit correspondre à une filière du fichier structure
                   - `annee_universitaire` (obligatoire) - doit correspondre à une session du fichier structure
                   - `version` (optionnel)
                   - `nom_fichier` (obligatoire) - nom du fichier PDF dans le dossier
                
                3. **Préparez vos fichiers PDF** :
                   - Placez tous vos fichiers PDF dans un dossier
                   - Les noms des fichiers doivent correspondre à la colonne `nom_fichier`
                
                4. **Importez les données** :
                   - Sélectionnez votre fichier Excel de structure
                   - Sélectionnez votre fichier Excel des mémoires
                   - Indiquez le chemin du dossier contenant les PDFs
                   - Cliquez sur "Lancer l'import complet"
                
                ### Remarques importantes
                
                - L'import est transactionnel : en cas d'erreur, les changements sont annulés
                - Les entités, filières et sessions existantes ne seront pas dupliquées
                - Les erreurs sont reportées de manière détaillée
                """)
            
            # Formulaire d'import
            with st.form("import_complete_form"):
                structure_file = st.file_uploader(
                    "Fichier Excel de structure (entités, filières, sessions)", 
                    type=['xlsx'],
                    help="Fichier Excel contenant les feuilles : entites, filieres, sessions"
                )
                
                metadata_file = st.file_uploader(
                    "Fichier Excel/CSV des métadonnées des mémoires", 
                    type=['xlsx', 'csv'],
                    help="Fichier contenant les métadonnées des mémoires"
                )
                
                pdf_folder = st.text_input(
                    "Chemin du dossier des PDFs",
                    help="Chemin absolu vers le dossier contenant tous les fichiers PDF"
                )
                
                submitted = st.form_submit_button("Lancer l'import complet")
                
                if submitted:
                    if not structure_file:
                        st.error("Veuillez sélectionner le fichier de structure")
                    elif not metadata_file:
                        st.error("Veuillez sélectionner le fichier des métadonnées")
                    elif not pdf_folder:
                        st.error("Veuillez indiquer le chemin du dossier des PDFs")
                    elif not os.path.exists(pdf_folder):
                        st.error("Le dossier spécifié n'existe pas")
                    else:
                        with st.spinner("Import complet en cours..."):
                            success, result = bulk_import_structure_and_memoires(
                                structure_file, metadata_file, pdf_folder
                            )
                            
                            if success:
                                st.success(f"""
                                Import complet terminé avec succès !
                                
                                Structure importée :
                                - Entités : {result['entites_count']}
                                - Filières : {result['filieres_count']}
                                - Sessions : {result['sessions_count']}
                                
                                Mémoires :
                                - Importés : {result['memoires_success']}
                                - Erreurs : {result['memoires_error']}
                                """)
                                
                                if result['errors']:
                                    with st.expander("Voir les erreurs"):
                                        for error in result['errors']:
                                            st.error(error)
                            else:
                                st.error(f"Erreur lors de l'import : {result}")
        
        with tab4:
            st.subheader("Liste des mémoires")
            
            # Recherche simple
            search_query = st.text_input("Rechercher un mémoire", key="manage_search")
            
            memoires = get_all_memoires()
            
            if search_query:
                # Filtrer les mémoires par la recherche
                memoires = memoires[
                    memoires['titre'].str.contains(search_query, case=False) | 
                    memoires['auteurs'].str.contains(search_query, case=False) |
                    memoires['resume'].str.contains(search_query, case=False) |
                    memoires['tags'].str.contains(search_query, case=False)
                ]
            
            if memoires.empty:
                st.info("Aucun mémoire trouvé.")
            else:
                st.write(f"{len(memoires)} mémoires trouvés.")
                
                # Afficher les mémoires avec pagination
                memoires_per_page = 10
                total_pages = (len(memoires) + memoires_per_page - 1) // memoires_per_page
                
                if 'current_page' not in st.session_state:
                    st.session_state.current_page = 1
                
                # Boutons de pagination
                col1, col2, col3 = st.columns([1, 3, 1])
                
                with col1:
                    if st.button("◀️ Précédent") and st.session_state.current_page > 1:
                        st.session_state.current_page -= 1
                
                with col2:
                    st.write(f"Page {st.session_state.current_page}/{total_pages}")
                
                with col3:
                    if st.button("Suivant ▶️") and st.session_state.current_page < total_pages:
                        st.session_state.current_page += 1
                
                # Calculer l'indice de début et de fin
                start_idx = (st.session_state.current_page - 1) * memoires_per_page
                end_idx = min(start_idx + memoires_per_page, len(memoires))
                
                # Afficher les mémoires de la page courante
                for idx in range(start_idx, end_idx):
                    memoire = memoires.iloc[idx]
                    with st.expander(f"{memoire['titre']} - {memoire['auteurs']} ({memoire['annee_universitaire']})"):
                        st.write(f"**Encadreur:** {memoire['encadreur']}")
                        st.write(f"**Filière:** {memoire['filiere_nom']} - {memoire['entite_nom']}")
                        st.write(f"**Résumé:** {memoire['resume'][:200]}..." if len(memoire['resume']) > 200 else f"**Résumé:** {memoire['resume']}")
                        st.markdown(f"**Mots-clés:** {memoire['tags']}")
                        
                        # Actions sur le mémoire
                        action_col1, action_col2, action_col3 = st.columns(3)
                        
                        # Téléchargement
                        with action_col1:
                            if memoire['fichier_url'].startswith("local://"):
                                st.markdown(get_download_link(memoire['fichier_url'], "📥 Télécharger le PDF"), unsafe_allow_html=True)
                        
                        # Modification
                        with action_col2:
                            if st.button("✏️ Modifier", key=f"edit_memoire_{memoire['id']}"):
                                st.session_state.edit_memoire = memoire['id']
                                st.rerun()
                        
                        # Suppression
                        with action_col3:
                            delete_key = f"delete_memoire_{memoire['id']}"
                            confirm_key = f"confirm_delete_{memoire['id']}"
                            
                            if confirm_key not in st.session_state:
                                if st.button("🗑️ Supprimer", key=delete_key):
                                    st.session_state[confirm_key] = True
                                    st.rerun()
                            else:
                                st.warning("Êtes-vous sûr de vouloir supprimer ce mémoire ?")
                                conf_col1, conf_col2 = st.columns(2)
                                
                                with conf_col1:
                                    if st.button("✔️ Oui", key=f"confirm_yes_{memoire['id']}"):
                                        # Débogage
                                        st.write(f"Tentative de suppression du mémoire ID: {memoire['id']}")
                                        # Vérifier que l'ID est un entier
                                        memoire_id = int(memoire['id'])
                                        success, message = delete_memoire(memoire_id)
                                        if success:
                                            add_log(f"Suppression du mémoire: {memoire['titre']}", st.session_state.user_id)
                                            st.success(message)
                                            del st.session_state[confirm_key]
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"Erreur lors de la suppression : {message}")
                                
                                with conf_col2:
                                    if st.button("❌ Non", key=f"confirm_no_{memoire['id']}"):
                                        del st.session_state[confirm_key]
                                        st.rerun()

def show_logs():
    st.header("📋 Journal d'activité")
    st.markdown("---")
    container = st.container()
    with container:
        # Connexion à la base de données
        conn = sqlite3.connect(DB_PATH)
        
        # Récupération des logs avec noms d'utilisateurs
        query = """
        SELECT l.id, l.action, u.nom, l.date 
        FROM logs l
        LEFT JOIN utilisateurs u ON l.user_id = u.id
        ORDER BY l.date DESC
        LIMIT 100
        """
        logs = pd.read_sql_query(query, conn)
        conn.close()
        
        # Affichage des logs
        st.write("Dernières actions effectuées (100 maximum):")
        
        if logs.empty:
            st.info("Aucune activité enregistrée.")
        else:
            # Formater le dataframe pour l'affichage
            logs.columns = ['ID', 'Action', 'Utilisateur', 'Date']
            logs['Utilisateur'] = logs['Utilisateur'].fillna('Visiteur')
            
            st.dataframe(logs, use_container_width=True)

# Point d'entrée principal de l'application
if __name__ == "__main__":
    main()