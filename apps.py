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





# Configuration de la page
st.set_page_config(
    page_title="Gestion des Mémoires Universitaires",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

#with open("style.css") as f:
    #st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Créer les dossiers nécessaires s'ils n'existent pas
os.makedirs("data", exist_ok=True)
os.makedirs("data/memoires", exist_ok=True)

# Chemin de la base de données
DB_PATH = "data/memoires_db.sqlite"

# Fonction pour initialiser la base de données
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Modification de la table utilisateurs pour ajouter les nouveaux champs
    c.execute('''
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY,
        nom TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        mot_de_passe TEXT NOT NULL,
        role TEXT NOT NULL,
        date_naissance TEXT,
        genre TEXT,
        telephone TEXT
    )
    ''')
    
    # Création de la table entites
    c.execute('''
    CREATE TABLE IF NOT EXISTS entites (
        id INTEGER PRIMARY KEY,
        nom TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Création de la table filieres
    c.execute('''
    CREATE TABLE IF NOT EXISTS filieres (
        id INTEGER PRIMARY KEY,
        nom TEXT NOT NULL,
        entite_id INTEGER NOT NULL,
        FOREIGN KEY (entite_id) REFERENCES entites (id),
        UNIQUE(nom, entite_id)
    )
    ''')
    
    # Création de la table sessions
    c.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY,
        annee_universitaire TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Création de la table memoires
    c.execute('''
    CREATE TABLE IF NOT EXISTS memoires (
        id INTEGER PRIMARY KEY,
        titre TEXT NOT NULL,
        auteurs TEXT NOT NULL,
        encadreur TEXT NOT NULL,
        resume TEXT,
        fichier_pdf TEXT NOT NULL,
        tags TEXT,
        filiere_id INTEGER NOT NULL,
        session_id INTEGER NOT NULL,
        version TEXT,
        date_ajout TEXT NOT NULL,
        FOREIGN KEY (filiere_id) REFERENCES filieres (id),
        FOREIGN KEY (session_id) REFERENCES sessions (id)
    )
    ''')
    
    # Création de la table favoris
    c.execute('''
    CREATE TABLE IF NOT EXISTS favoris (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        memoire_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES utilisateurs (id),
        FOREIGN KEY (memoire_id) REFERENCES memoires (id),
        UNIQUE(user_id, memoire_id)
    )
    ''')
    
    # Création de la table logs
    c.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY,
        action TEXT NOT NULL,
        user_id INTEGER,
        date TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES utilisateurs (id)
    )
    ''')
    
    # Vérification si un admin existe déjà, sinon on en crée un par défaut
    c.execute("SELECT * FROM utilisateurs WHERE role='admin' LIMIT 1")
    if not c.fetchone():
        # Création d'un admin par défaut (admin@universite.com / admin123)
        hashed_pwd = hashlib.sha256("Admin@0128".encode()).hexdigest()
        c.execute("INSERT INTO utilisateurs (nom, email, mot_de_passe, role) VALUES (?, ?, ?, ?)",
                 ("Administrateur", "admin@universite.com", hashed_pwd, "admin"))
    
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
    hashed_pwd = hashlib.sha256(password.encode()).hexdigest()
    c.execute("SELECT id, nom, role FROM utilisateurs WHERE email=? AND mot_de_passe=?", 
             (email, hashed_pwd))
    user = c.fetchone()
    conn.close()
    return user

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
        file_path = os.path.join("data/memoires", filename)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return True, file_path
    return False, None

# Fonction pour ajouter un mémoire
def add_memoire(titre, auteurs, encadreur, resume, fichier_pdf, tags, filiere_id, session_id, version):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
        INSERT INTO memoires 
        (titre, auteurs, encadreur, resume, fichier_pdf, tags, filiere_id, session_id, version, date_ajout) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (titre, auteurs, encadreur, resume, fichier_pdf, tags, filiere_id, session_id, version, date_now))
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
    SELECT m.id, m.titre, m.auteurs, m.encadreur, m.resume, m.fichier_pdf, m.tags, 
           f.nom as filiere_nom, s.annee_universitaire, m.version, m.date_ajout,
           e.nom as entite_nom
    FROM memoires m
    JOIN filieres f ON m.filiere_id = f.id
    JOIN sessions s ON m.session_id = s.id
    JOIN entites e ON f.entite_id = e.id
    ORDER BY m.date_ajout DESC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Fonction pour supprimer un mémoire
def delete_memoire(memoire_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Récupérer le chemin du fichier PDF
    c.execute("SELECT fichier_pdf FROM memoires WHERE id=?", (memoire_id,))
    file_path = c.fetchone()[0]
    
    # Supprimer le mémoire de la base de données
    c.execute("DELETE FROM memoires WHERE id=?", (memoire_id,))
    conn.commit()
    conn.close()
    
    # Supprimer le fichier PDF si nécessaire
    if os.path.exists(file_path):
        os.remove(file_path)
    
    return True, "Mémoire supprimé avec succès."

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
    SELECT m.id, m.titre, m.auteurs, m.encadreur, m.resume, m.fichier_pdf, m.tags, 
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
    SELECT m.id, m.titre, m.auteurs, m.encadreur, m.resume, m.fichier_pdf, m.tags, 
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
def update_memoire(memoire_id, titre, auteurs, encadreur, resume, fichier_pdf, tags, filiere_id, session_id, version):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        if fichier_pdf:  # Nouveau fichier PDF
            c.execute("""
            UPDATE memoires 
            SET titre=?, auteurs=?, encadreur=?, resume=?, fichier_pdf=?, tags=?, filiere_id=?, session_id=?, version=?
            WHERE id=?
            """, (titre, auteurs, encadreur, resume, fichier_pdf, tags, filiere_id, session_id, version, memoire_id))
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

# Fonction pour créer un lien de téléchargement
def get_download_link(file_path, label):
    with open(file_path, "rb") as f:
        file_bytes = f.read()
    b64 = base64.b64encode(file_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{os.path.basename(file_path)}">{label}</a>'
    return href

# Fonction pour afficher un PDF intégré
def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf">'
    st.markdown(pdf_display, unsafe_allow_html=True)

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
        
        # Création du nom complet
        nom_complet = f"{prenom} {nom}"
        
        # Insertion du nouveau visiteur avec informations supplémentaires
        c.execute('''
        INSERT INTO utilisateurs 
        (nom, email, mot_de_passe, role, date_naissance, genre, telephone) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nom_complet, email, hashed_pwd, "visitor", date_naissance, genre, telephone))
        
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
    hashed_pwd = hashlib.sha256(new_password.encode()).hexdigest()
    try:
        c.execute("UPDATE utilisateurs SET mot_de_passe=? WHERE email=?", (hashed_pwd, email))
        conn.commit()
        conn.close()
        return True, "Mot de passe mis à jour avec succès."
    except Exception as e:
        conn.close()
        return False, f"Erreur lors de la mise à jour du mot de passe: {str(e)}"

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
    st.sidebar.title("🎓 Mémoires Universitaires (UNSTIM)")
    st.sidebar.title(" Auteurs ")
    st.sidebar.title(" B. Zamane SOULEMANE ")
    st.sidebar.title(" A. Elisé LOKOSSOU ")
    
    
    # Affichage conditionnel en fonction de l'authentification
    if not st.session_state.logged_in:
        show_login_page()
    else:
        # Menu pour l'administrateur ou l'utilisateur normal
        if st.session_state.user_role == "admin":
            menu = st.sidebar.radio("Navigation", 
                ["Accueil", "Recherche", "Statistiques", "Gestion des Entités", 
                "Gestion des Filières", "Gestion des Sessions", "Gestion des Mémoires", "Journal d'activité"])
        else:
            menu = st.sidebar.radio("Navigation", ["Accueil", "Recherche", "Statistiques"])
        
        # Affichage du nom d'utilisateur connecté
        st.sidebar.write(f"👤 Connecté en tant que : **{st.session_state.user_name}**")
        if st.sidebar.button("Déconnexion"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.user_name = None
            st.session_state.user_role = None
            st.rerun()
        
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
                        time.sleep(1)
                        st.rerun()
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

def show_home_page():
    st.title("📚 Plateforme de Gestion des Mémoires Universitaires")
    st.write("Bienvenue sur la plateforme centrale des mémoires de soutenance de l'université.")
    
    # Afficher les derniers mémoires ajoutés
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
                
                col1, col2 = st.columns(2)
                with col1:
                    if os.path.exists(memoire['fichier_pdf']):
                        st.markdown(get_download_link(memoire['fichier_pdf'], "📥 Télécharger le PDF"), unsafe_allow_html=True)
                with col2:
                    if st.button("Voir les détails", key=f"view_{memoire['id']}"):
                        st.session_state.selected_memoire = memoire['id']
                        show_memoire_details(memoire['id'])
    
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
        return
    
    st.title(memoire['titre'])
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
    
    with col2:
        st.subheader("Actions")
        if os.path.exists(memoire['fichier_pdf']):
            st.markdown(get_download_link(memoire['fichier_pdf'], "📥 Télécharger le PDF"), unsafe_allow_html=True)
            
            if st.button("📄 Consulter en ligne", key=f"view_online_{memoire_id}"):
                st.session_state.view_pdf = memoire['fichier_pdf']
    
    # Affichage du PDF intégré si demandé
    if 'view_pdf' in st.session_state and st.session_state.view_pdf == memoire['fichier_pdf']:
        st.subheader("Visualisation du document")
        if os.path.exists(memoire['fichier_pdf']):
            display_pdf(memoire['fichier_pdf'])
    
    # Si admin, ajouter des boutons de modification/suppression
    if st.session_state.user_role == "admin":
        st.subheader("Administration")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✏️ Modifier", key=f"edit_{memoire_id}"):
                st.session_state.edit_memoire = memoire_id
                st.rerun()
        
        with col2:
            if st.button("🗑️ Supprimer", key=f"delete_{memoire_id}"):
                if 'confirm_delete' not in st.session_state:
                    st.session_state.confirm_delete = memoire_id
                    st.warning("Êtes-vous sûr de vouloir supprimer ce mémoire ? Cette action est irréversible.")
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        if st.button("Oui, supprimer", key=f"confirm_yes_{memoire_id}"):
                            success, message = delete_memoire(memoire_id)
                            if success:
                                add_log(f"Mémoire supprimé: {memoire['titre']}", st.session_state.user_id)
                                st.success(message)
                                del st.session_state.confirm_delete
                                del st.session_state.selected_memoire
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(message)
                    with confirm_col2:
                        if st.button("Non, annuler", key=f"confirm_no_{memoire_id}"):
                            del st.session_state.confirm_delete
                            st.rerun()

def show_search_page():
    st.title("🔍 Recherche de Mémoires")
    
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
    if search_button or search_query or selected_entity or selected_filiere or selected_session:
        results = search_memoires(search_query, 
                                  selected_entity if selected_entity else None,
                                  selected_filiere if selected_filiere else None,
                                  selected_session if selected_session else None)
        
        st.subheader(f"Résultats ({len(results)} mémoires trouvés)")
        
        if len(results) == 0:
            st.info("Aucun mémoire ne correspond à votre recherche.")
        else:
            for _, memoire in results.iterrows():
                with st.expander(f"{memoire['titre']} - {memoire['auteurs']} ({memoire['annee_universitaire']})"):
                    st.write(f"**Encadreur:** {memoire['encadreur']}")
                    st.write(f"**Filière:** {memoire['filiere_nom']} - {memoire['entite_nom']}")
                    st.write(f"**Résumé:** {memoire['resume'][:200]}..." if len(memoire['resume']) > 200 else f"**Résumé:** {memoire['resume']}")
                    st.markdown(f"**Mots-clés:** {memoire['tags']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if os.path.exists(memoire['fichier_pdf']):
                            st.markdown(get_download_link(memoire['fichier_pdf'], "📥 Télécharger le PDF"), unsafe_allow_html=True)
                    with col2:
                        if st.button("Voir les détails", key=f"search_view_{memoire['id']}"):
                            st.session_state.selected_memoire = memoire['id']
                            show_memoire_details(memoire['id'])
                            return
    
    # Si un mémoire a été sélectionné, afficher ses détails
    if "selected_memoire" in st.session_state:
        show_memoire_details(st.session_state.selected_memoire)

def show_statistics_page():
    st.title("📊 Statistiques")
    
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
    st.title("🏢 Gestion des Entités")
    
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
    st.title("🎓 Gestion des Filières")
    
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
    st.title("📅 Gestion des Sessions")
    
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
    st.title("📚 Gestion des Mémoires")
    
    # Si en mode édition d'un mémoire
    if 'edit_memoire' in st.session_state:
        memoire_id = st.session_state.edit_memoire
        memoire = get_memoire_details(memoire_id)
        
        if memoire is None:
            st.error("Ce mémoire n'existe pas ou a été supprimé.")
            del st.session_state.edit_memoire
            return
        
        st.subheader(f"Modification du mémoire: {memoire['titre']}")
        
        # Formulaire de modification
        titre = st.text_input("Titre", value=memoire['titre'], key="edit_titre")
        auteurs = st.text_input("Auteur(s)", value=memoire['auteurs'], key="edit_auteurs")
        encadreur = st.text_input("Encadreur", value=memoire['encadreur'], key="edit_encadreur")
        resume = st.text_area("Résumé", value=memoire['resume'], height=150, key="edit_resume")
        tags = st.text_input("Mots-clés (séparés par des virgules)", value=memoire['tags'], key="edit_tags")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sélection de l'entité et filière
            entities = get_all_entities()
            entity_options = [(row['id'], row['nom']) for _, row in entities.iterrows()]
            
            # Récupérer l'entité de la filière actuelle
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT entite_id FROM filieres WHERE id = ?", (memoire['filiere_id'],))
            current_entity_id = c.fetchone()[0]
            conn.close()
            
            selected_entity = st.selectbox("Entité", 
                                          options=[id for id, _ in entity_options],
                                          format_func=lambda x: next((name for id, name in entity_options if id == x), ""),
                                          index=[i for i, (id, _) in enumerate(entity_options) if id == current_entity_id][0],
                                          key="edit_entity")
            
            filieres = get_filieres_by_entity(selected_entity)
            filiere_options = [(row['id'], row['nom']) for _, row in filieres.iterrows()]
            
            try:
                filiere_index = [i for i, (id, _) in enumerate(filiere_options) if id == memoire['filiere_id']][0]
            except IndexError:
                filiere_index = 0
            
            selected_filiere = st.selectbox("Filière", 
                                           options=[id for id, _ in filiere_options],
                                           format_func=lambda x: next((name for id, name in filiere_options if id == x), ""),
                                           index=filiere_index if filiere_options else 0,
                                           key="edit_filiere")
        
        with col2:
            # Sélection de la session
            sessions = get_all_sessions()
            session_options = [(row['id'], row['annee_universitaire']) for _, row in sessions.iterrows()]
            
            try:
                session_index = [i for i, (id, _) in enumerate(session_options) if id == memoire['session_id']][0]
            except IndexError:
                session_index = 0
            
            selected_session = st.selectbox("Année universitaire", 
                                           options=[id for id, _ in session_options],
                                           format_func=lambda x: next((name for id, name in session_options if id == x), ""),
                                           index=session_index if session_options else 0,
                                           key="edit_session")
            
            version = st.text_input("Version (optionnel)", value=memoire['version'] if memoire['version'] else "", key="edit_version")
        
        # Upload d'un nouveau fichier PDF (optionnel)
        st.write("Fichier PDF actuel:", os.path.basename(memoire['fichier_pdf']))
        new_pdf = st.file_uploader("Nouveau fichier PDF (optionnel, laissez vide pour conserver l'actuel)", type=['pdf'], key="edit_pdf")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Annuler"):
                del st.session_state.edit_memoire
                st.rerun()
        
        with col2:
            if st.button("Enregistrer les modifications"):
                if titre and auteurs and encadreur and resume and selected_filiere and selected_session:
                    # Si un nouveau fichier a été téléversé
                    new_pdf_path = None
                    if new_pdf is not None:
                        filename = f"{uuid.uuid4()}.pdf"
                        success, new_pdf_path = save_pdf(new_pdf, filename)
                        if not success:
                            st.error("Erreur lors de l'enregistrement du fichier PDF.")
                            return
                    
                    # Mise à jour du mémoire
                    success, message = update_memoire(
                        memoire_id, titre, auteurs, encadreur, resume, 
                        new_pdf_path, tags, selected_filiere, selected_session, version
                    )
                    
                    if success:
                        add_log(f"Modification du mémoire ID {memoire_id}: {titre}", st.session_state.user_id)
                        st.success(message)
                        del st.session_state.edit_memoire
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Veuillez remplir tous les champs obligatoires.")
        
        return
    
    # Sinon, afficher le formulaire d'ajout et la liste des mémoires
    
    tab1, tab2 = st.tabs(["Ajouter un mémoire", "Liste des mémoires"])
    
    with tab1:
        st.subheader("Ajouter un nouveau mémoire")
        
        # Vérifier si les éléments nécessaires existent
        entities = get_all_entities()
        sessions = get_all_sessions()
        
        if entities.empty or sessions.empty:
            if entities.empty:
                st.warning("Vous devez d'abord ajouter des entités et des filières.")
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
            
            if st.button("Ajouter le mémoire"):
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
                            # Réinitialiser les champs
                            for key in ["add_titre", "add_auteurs", "add_encadreur", "add_resume", "add_tags", "add_version"]:
                                #st.session_state[key] = ""
                                #st.session_state["add_pdf"] = None
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
                    st.warning("Veuillez remplir tous les champs obligatoires et téléverser un fichier PDF.")
    
    with tab2:
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
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if os.path.exists(memoire['fichier_pdf']):
                            st.markdown(get_download_link(memoire['fichier_pdf'], "📥 Télécharger le PDF"), unsafe_allow_html=True)
                    with col2:
                        if st.button("✏️ Modifier", key=f"edit_btn_{memoire['id']}"):
                            st.session_state.edit_memoire = memoire['id']
                            st.rerun()
                    with col3:
                        if st.button("🗑️ Supprimer", key=f"del_btn_{memoire['id']}"):
                            if f"confirm_delete_{memoire['id']}" not in st.session_state:
                                st.session_state[f"confirm_delete_{memoire['id']}"] = True
                                st.warning("Êtes-vous sûr de vouloir supprimer ce mémoire ? Cette action est irréversible.")
                                confirm_col1, confirm_col2 = st.columns(2)
                                with confirm_col1:
                                    if st.button("Oui, supprimer", key=f"confirm_yes_{memoire['id']}"):
                                        success, message = delete_memoire(memoire['id'])
                                        if success:
                                            add_log(f"Suppression du mémoire: {memoire['titre']}", st.session_state.user_id)
                                            st.success(message)
                                            del st.session_state[f"confirm_delete_{memoire['id']}"]
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(message)
                                with confirm_col2:
                                    if st.button("Non, annuler", key=f"confirm_no_{memoire['id']}"):
                                        del st.session_state[f"confirm_delete_{memoire['id']}"]
                                        st.rerun()

def show_logs():
    st.title("📋 Journal d'activité")
    
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