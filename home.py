import streamlit as st
from apps import *  # Import all functions from apps.py
from apps import (
    show_login_page, get_all_memoires, get_download_link, 
    show_home_page as show_admin_home, show_search_page, 
    show_statistics_page, show_entities_management,
    show_filieres_management, show_sessions_management,
    show_memoires_management, show_logs
)
import time

# Styles personnalisés
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
    <link rel="manifest" href="manifest.json">
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('service-worker.js')
                    .then((registration) => {
                        console.log('Service Worker registered');
                    })
                    .catch((error) => {
                        console.log('Service Worker registration failed:', error);
                    });
            });

            // Vérifier si l'application est installable
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                const installBtn = document.createElement('button');
                installBtn.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    z-index: 9999;
                    padding: 10px 20px;
                    background: linear-gradient(45deg, #2C3E50, #3498DB);
                    color: white;
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    display: flex;
                    align-items: center;
                    gap: 8px;
                `;
                installBtn.innerHTML = '📱 Installer l\'application';
                
                installBtn.addEventListener('click', async () => {
                    try {
                        await e.prompt();
                        const choiceResult = await e.userChoice;
                        if (choiceResult.outcome === 'accepted') {
                            console.log('Application installée');
                            installBtn.remove();
                        }
                    } catch (error) {
                        console.error('Erreur lors de l\'installation:', error);
                    }
                });

                document.body.appendChild(installBtn);
            });
        }
    </script>
    <style>
        /* Variables globales */
        :root {
            --primary-color: #2C3E50;
            --secondary-color: #3498DB;
            --accent-color: #E74C3C;
            --background-color: #F8F9FA;
            --text-color: #2C3E50;
            --text-light: #6C757D;
            --card-background: #FFFFFF;
            --shadow-sm: 0 2px 4px rgba(0,0,0,0.1);
            --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
            --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
            --transition: all 0.3s ease;
        }

        /* Mode sombre */
        @media (prefers-color-scheme: dark) {
            :root {
                --primary-color: #3498DB;
                --secondary-color: #2C3E50;
                --background-color: #1a1a1a;
                --text-color: #FFFFFF;
                --text-light: #CCCCCC;
                --card-background: #2d2d2d;
                --shadow-sm: 0 2px 4px rgba(0,0,0,0.3);
                --shadow-md: 0 4px 6px rgba(0,0,0,0.3);
                --shadow-lg: 0 10px 15px rgba(0,0,0,0.3);
            }

            .stApp {
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%) !important;
            }

            .stat-card, .streamlit-expanderHeader, .welcome-header, .footer {
                background: var(--card-background) !important;
                color: var(--text-color) !important;
            }

            .dataframe {
                background: var(--card-background) !important;
                color: var(--text-color) !important;
            }

            .dataframe thead th {
                background: var(--primary-color) !important;
                color: white !important;
            }

            .dataframe tbody tr:nth-child(even) {
                background: rgba(255, 255, 255, 0.05) !important;
            }

            .dataframe tbody tr:hover {
                background: rgba(52, 152, 219, 0.2) !important;
            }

            blockquote {
                background: rgba(52, 152, 219, 0.1) !important;
                color: var(--text-light) !important;
            }

            /* Amélioration de la lisibilité des textes */
            p, h1, h2, h3, h4, h5, h6 {
                color: var(--text-color) !important;
            }

            .stMarkdown {
                color: var(--text-color) !important;
            }

            /* Adaptation des boutons pour le mode sombre */
            .stButton > button {
                background: linear-gradient(45deg, var(--primary-color), var(--secondary-color)) !important;
                color: white !important;
            }

            /* Adaptation des inputs pour le mode sombre */
            .stTextInput > div > div > input,
            .stSelectbox > div > div > select {
                background: var(--card-background) !important;
                color: var(--text-color) !important;
                border-color: var(--primary-color) !important;
            }

            /* Amélioration des contrastes pour les métriques */
            .stMetric {
                background: var(--card-background) !important;
                color: var(--text-color) !important;
            }

            /* Adaptation de la barre latérale */
            .css-1d391kg {
                background: var(--card-background) !important;
            }

            .sidebar .sidebar-content {
                background: linear-gradient(180deg, var(--card-background) 0%, var(--background-color) 100%) !important;
            }
        }

        /* Styles de base (conservez le reste du CSS existant) */
        .stApp {
            font-family: 'Roboto', sans-serif;
            color: var(--text-color);
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }

        .main {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* Typographie */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Montserrat', sans-serif;
            font-weight: 600;
            letter-spacing: -0.5px;
        }

        h1 {
            color: var(--primary-color);
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            margin-bottom: 1.5rem !important;
            text-align: center;
            background: linear-gradient(120deg, var(--primary-color), var(--secondary-color));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            padding: 1rem 0;
        }

        h2 {
            color: var(--primary-color);
            font-size: 2rem !important;
            margin-top: 2.5rem !important;
            margin-bottom: 1.5rem !important;
            position: relative;
        }

        h2::after {
            content: '';
            display: block;
            width: 50px;
            height: 4px;
            background: var(--secondary-color);
            margin-top: 0.5rem;
            border-radius: 2px;
        }

        /* Cartes et conteneurs */
        .stat-card {
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: var(--shadow-md);
            margin-bottom: 1.5rem;
            transition: var(--transition);
            border: 1px solid rgba(0,0,0,0.05);
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: var(--shadow-lg);
        }

        /* Boutons et interactions */
        .stButton > button {
            font-family: 'Montserrat', sans-serif;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            border-radius: 10px;
            border: none;
            background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
            color: white;
            transition: var(--transition);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            box-shadow: var(--shadow-sm);
        }

        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
            opacity: 0.9;
        }

        /* Widgets et inputs */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > select {
            border-radius: 10px;
            border: 2px solid #E2E8F0;
            padding: 0.75rem 1rem;
            font-family: 'Roboto', sans-serif;
            transition: var(--transition);
        }

        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {
            border-color: var(--secondary-color);
            box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
        }

        /* Expanders */
        .streamlit-expanderHeader {
            background: white;
            border-radius: 10px;
            padding: 1rem !important;
            font-weight: 500;
            color: var(--primary-color);
            border: 1px solid rgba(0,0,0,0.05);
            margin-bottom: 0.5rem;
            transition: var(--transition);
        }

        .streamlit-expanderHeader:hover {
            background: var(--background-color);
        }

        /* Métriques */
        .stMetric {
            background: white;
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: var(--shadow-sm);
            transition: var(--transition);
        }

        .stMetric:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
        }

        /* Sidebar */
        .css-1d391kg {
            background: var(--primary-color);
            padding: 2rem 1rem;
        }

        .sidebar .sidebar-content {
            background: linear-gradient(180deg, var(--primary-color) 0%, #34495E 100%);
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 3rem 0;
            color: var(--text-light);
            font-size: 0.9rem;
            background: white;
            border-radius: 15px;
            margin-top: 3rem;
            box-shadow: var(--shadow-sm);
        }

        /* Responsive design */
        @media (max-width: 768px) {
            .main {
                padding: 0.5rem;
            }

            h1 {
                font-size: 1.8rem !important;
                padding: 0.5rem 0;
            }

            h2 {
                font-size: 1.3rem !important;
                margin-top: 1.5rem !important;
            }

            .stat-card {
                padding: 0.75rem;
                margin-bottom: 1rem;
            }

            .stButton > button {
                width: 100%;
                padding: 0.5rem;
                font-size: 0.9rem;
            }

            /* Amélioration de la navigation mobile */
            .sidebar .sidebar-content {
                padding: 1rem 0.5rem;
            }

            /* Ajustement des colonnes pour mobile */
            .row-widget.stHorizontal > div {
                flex: 1 1 100% !important;
                width: 100% !important;
            }

            /* Amélioration de la lisibilité des tableaux sur mobile */
            .dataframe {
                font-size: 0.8rem;
                overflow-x: auto;
            }

            .dataframe td, .dataframe th {
                padding: 0.5rem !important;
                white-space: nowrap;
            }

            /* Ajustement des métriques pour mobile */
            .stMetric {
                padding: 0.75rem;
                font-size: 0.9rem;
            }

            /* Optimisation des formulaires pour mobile */
            .stTextInput > div > div > input,
            .stSelectbox > div > div > select {
                padding: 0.5rem;
                font-size: 0.9rem;
            }

            /* Ajustement des expandeurs pour mobile */
            .streamlit-expanderHeader {
                padding: 0.75rem !important;
                font-size: 0.9rem;
            }

            /* Optimisation des images pour mobile */
            img {
                max-width: 100%;
                height: auto;
            }

            /* Ajustement de l'en-tête pour mobile */
            .welcome-header {
                margin: 2rem auto;
                padding: 1rem;
            }

            .welcome-header h1 {
                font-size: 2rem !important;
            }

            .welcome-header .subtitle {
                font-size: 1rem;
                margin-bottom: 1rem;
            }

            /* Optimisation des boutons de la page d'accueil */
            .welcome-header .buttons-container {
                flex-direction: column;
                gap: 0.5rem;
            }

            .welcome-header .stButton > button {
                min-width: unset;
                width: 100%;
            }

            /* Amélioration du footer pour mobile */
            .footer {
                padding: 1.5rem 0;
                margin-top: 2rem;
                font-size: 0.8rem;
            }

            /* Gestion du zoom sur les inputs pour iOS */
            input[type="text"],
            input[type="email"],
            input[type="password"] {
                font-size: 16px !important;
            }
        }

        /* Ajustements pour les très petits écrans */
        @media (max-width: 480px) {
            h1 {
                font-size: 1.5rem !important;
            }

            .stat-card {
                margin: 0.5rem 0;
            }

            .stButton > button {
                font-size: 0.85rem;
            }
        }

        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .animate-fade-in {
            animation: fadeIn 0.5s ease-out forwards;
        }

        /* Citations et blocs de texte */
        blockquote {
            border-left: 4px solid var(--secondary-color);
            padding-left: 1rem;
            margin: 1rem 0;
            color: var(--text-light);
            font-style: italic;
            background: rgba(52, 152, 219, 0.1);
            padding: 1rem;
            border-radius: 0 10px 10px 0;
        }

        /* Tableaux */
        .dataframe {
            border: none;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: var(--shadow-sm);
        }

        .dataframe thead th {
            background: var(--primary-color);
            color: white;
            font-weight: 500;
            padding: 1rem;
        }

        .dataframe tbody tr:nth-child(even) {
            background: var(--background-color);
        }

        .dataframe tbody td {
            padding: 0.75rem;
            border: none;
            transition: var(--transition);
        }

        .dataframe tbody tr:hover {
            background: rgba(52, 152, 219, 0.1);
        }

        /* Ajout des styles pour la section d'en-tête */
        .welcome-header {
            max-width: 800px;
            margin: 4rem auto;
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 20px;
            box-shadow: var(--shadow-md);
        }

        .welcome-header h1 {
            color: #2C3E50;
            font-size: 3rem !important;
            margin-bottom: 1rem !important;
            background: linear-gradient(120deg, #2C3E50, #3498DB);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .welcome-header .subtitle {
            font-size: 1.2rem;
            color: var(--text-light);
            margin-bottom: 2rem;
        }

        .welcome-header .buttons-container {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 2rem;
        }

        .welcome-header .stButton > button {
            min-width: 200px;
        }
    </style>
""", unsafe_allow_html=True)

# Création du fichier manifest.json
manifest = {
    "name": "Banque des Mémoires UNSTIM",
    "short_name": "Mémoires UNSTIM",
    "description": "Plateforme de gestion des mémoires universitaires de l'UNSTIM",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#ffffff",
    "theme_color": "#2C3E50",
    "icons": [
        {
            "src": "assets/unstim.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "assets/unstim.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}

# Création du service worker
service_worker = """
const CACHE_NAME = 'memoires-unstim-v1';
const urlsToCache = [
    '/',
    '/assets/unstim.png',
    '/assets/mesrs.png',
    'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&family=Roboto:wght@300;400;500&display=swap'
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            })
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
"""

import json
import os

# Créer le dossier pour les fichiers PWA s'il n'existe pas
os.makedirs("static", exist_ok=True)

# Écrire le fichier manifest.json
with open("static/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)

# Écrire le fichier service-worker.js
with open("static/service-worker.js", "w") as f:
    f.write(service_worker)

def show_welcome_page():
    # En-tête avec les logos et le titre
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        try:
            st.image("assets/unstim.png", width=120)
        except:
            st.error("Logo UNSTIM non trouvé")
    
    with col2:
        st.markdown("""
            <div style="text-align: center; padding: 0 20px;">
                <h1 style="font-size: 2.5rem; margin: 0; background: linear-gradient(120deg, #2C3E50, #3498DB); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    Banque des Mémoires UNSTIM
                </h1>
                <p style="font-size: 1.2rem; color: #666; margin-top: 10px;">
                    Votre plateforme centralisée pour accéder aux mémoires académiques
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        try:
            st.image("assets/mesrs.png", width=120)
        except:
            st.error("Logo MESRS non trouvé")

    # Section des boutons de connexion et d'inscription avec style amélioré
    st.markdown("""
        <div style="max-width: 600px; margin: 40px auto; text-align: center;">
            <div style="display: flex; justify-content: center; gap: 20px;">
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔐 SE CONNECTER", key="login_btn", use_container_width=True, type="primary"):
            st.session_state.show_login = True
            st.session_state.show_register = False
            st.rerun()

    with col2:
        if st.button("📝 S'INSCRIRE", key="register_btn", use_container_width=True, type="primary"):
            st.session_state.show_register = True
            st.session_state.show_login = False
            st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

    # Afficher le formulaire d'inscription si le bouton est cliqué
    if st.session_state.show_register:
        show_register_page()
        return

    # Section des derniers mémoires ajoutés
    st.markdown('<h2>Derniers mémoires ajoutés</h2>', unsafe_allow_html=True)
    
    memoires = get_all_memoires().head(5)  # Direct call to imported function
    
    if len(memoires) == 0:
        st.info("Aucun mémoire n'a encore été ajouté.")
    else:
        for idx in range(len(memoires)):
            memoire = memoires.iloc[idx]
            with st.expander(f"📚 {memoire['titre']}"):
                st.markdown(f"""
                    <div class="memoire-card animate-fade-in">
                        <h3>{memoire['titre']}</h3>
                        <p><strong>Auteurs:</strong> {memoire['auteurs']}</p>
                        <p><strong>Année:</strong> {memoire['annee_universitaire']}</p>
                        <p><strong>Encadreur:</strong> {memoire['encadreur']}</p>
                        <p><strong>Filière:</strong> {memoire['filiere_nom']}</p>
                        <blockquote>{memoire['resume']}</blockquote>
                        <p><strong>Mots-clés:</strong> {memoire['tags']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("📥 Télécharger ce mémoire", key=f"download_{memoire['id']}"):
                    st.warning("""
                        ⚠️ Vous devez être connecté pour télécharger ce mémoire.
                        <a href="#" onclick="document.querySelector('[data-testid=\\"stSidebarNav\\"] button:nth-child(1)').click();">Se connecter</a> ou 
                        <a href="#" onclick="document.querySelector('[data-testid=\\"stSidebarNav\\"] button:nth-child(2)').click();">S'inscrire</a>
                    """, icon="⚠️")

    # Section des fonctionnalités
    st.markdown("""
        <div class="features-section animate-fade-in">
            <h2>Découvrez notre plateforme</h2>
            <div class="features-grid">
                <div class="stat-card">
                    <h3>🔍 Recherche avancée</h3>
                    <p>Trouvez rapidement les mémoires par mots-clés, auteur, filière ou année</p>
                </div>
                <div class="stat-card">
                    <h3>📱 Interface moderne</h3>
                    <p>Une expérience utilisateur optimisée sur tous les appareils</p>
                </div>
                <div class="stat-card">
                    <h3>🔒 Accès sécurisé</h3>
                    <p>Vos données sont protégées avec les dernières normes de sécurité</p>
                </div>
                <div class="stat-card">
                    <h3>📊 Statistiques détaillées</h3>
                    <p>Suivez les tendances et l'évolution de la base documentaire</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Section des statistiques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Mémoires", len(memoires))
    with col2:
        st.metric("👨‍🎓 Étudiants", "500+")
    with col3:
        st.metric("🏢 Départements", "8")
    with col4:
        st.metric("⚡ Disponibilité", "99.9%")

    # Footer
    st.markdown("""
        <div class="footer">
            <p>© 2024 Banque des Mémoires UNSTIM. Tous droits réservés.</p>
            <p>Développé avec ❤️ pour la communauté universitaire</p>
        </div>
    """, unsafe_allow_html=True)

def main():
    # Initialisation des variables de session
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.session_state.user_role = None
    
    # Sidebar pour la navigation (toujours visible)
    st.sidebar.title("🎓 Mémoires Universitaires (UNSTIM)")
    st.sidebar.title(" Auteurs : ")
    st.sidebar.title(" B. Zamane SOULEMANE ")
    st.sidebar.title(" A. Elisé LOKOSSOU ")
    
    # Affichage conditionnel en fonction de l'authentification
    if st.session_state.logged_in:
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
            st.session_state.show_login = False
            st.rerun()
        
        # Navigation vers les différentes pages
        if menu == "Accueil":
            show_home_page()  # Direct call to imported function
        elif menu == "Recherche":
            show_search_page()  # Direct call to imported function
        elif menu == "Statistiques":
            show_statistics_page()  # Direct call to imported function
        elif menu == "Gestion des Entités" and st.session_state.user_role == "admin":
            show_entities_management()  # Direct call to imported function
        elif menu == "Gestion des Filières" and st.session_state.user_role == "admin":
            show_filieres_management()  # Direct call to imported function
        elif menu == "Gestion des Sessions" and st.session_state.user_role == "admin":
            show_sessions_management()  # Direct call to imported function
        elif menu == "Gestion des Mémoires" and st.session_state.user_role == "admin":
            show_memoires_management()  # Direct call to imported function
        elif menu == "Journal d'activité" and st.session_state.user_role == "admin":
            show_logs()  # Direct call to imported function
    elif st.session_state.show_login:
        # Afficher la page de connexion
        if show_login_page():  # Direct call to imported function
            st.session_state.show_login = False
            st.rerun()
    else:
        show_welcome_page()

if __name__ == "__main__":
    main() 