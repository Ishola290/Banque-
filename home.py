import streamlit as st

# Configuration de la page Streamlit - DOIT ÊTRE EN PREMIER
st.set_page_config(
    page_title="Banque des Mémoires UNSTIM",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@unstim.bj',
        'Report a bug': "mailto:support@unstim.bj",
        'About': "# Banque des Mémoires UNSTIM\nVotre plateforme centralisée de gestion des mémoires universitaires."
    }
)

# Imports après la configuration de la page
from apps import *
import time
import base64
from theme import setup_theme, section_title, card, metric_card, info_card, action_button, data_table

# Configuration du thème
setup_theme()

from apps import (
    show_login_page, get_all_memoires, get_download_link, 
    show_home_page as show_admin_home, show_search_page, 
    show_statistics_page, show_entities_management,
    show_filieres_management, show_sessions_management,
    show_memoires_management, show_logs
)

def show_welcome_page():
    # En-tête principal avec logos
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            st.image("assets/unstim.png", use_column_width=True)
        
        with col2:
            st.markdown("""
                <div style='text-align: center; padding: 2rem 0;'>
                    <h1 style='color: var(--primary-color); font-size: 2.5rem; font-weight: 700; margin-bottom: 1rem;'>
                        🎓 Banque des Mémoires
                    </h1>
                    <p style='font-size: 1.2rem; color: var(--text-color); opacity: 0.8;'>
                        Plateforme de Gestion des Mémoires Universitaires
                    </p>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.image("assets/mesrs.png", use_column_width=True)

    # Section d'authentification avec style amélioré
    with st.container():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
                <div style='
                    background-color: var(--card-background);
                    padding: 2rem;
                    border-radius: var(--border-radius);
                    box-shadow: var(--box-shadow);
                    text-align: center;
                    margin: 2rem 0;
                '>
                    <h2 style='color: var(--primary-color); margin-bottom: 1.5rem;'>
                        Commencez votre exploration
                    </h2>
                </div>
            """, unsafe_allow_html=True)
            
            btn_col1, space, btn_col2 = st.columns([1, 0.2, 1])
            with btn_col1:
                if st.button("🔐 SE CONNECTER", use_container_width=True, key="login_btn"):
                    st.session_state.show_login = True
                    st.session_state.show_register = False
                    st.rerun()
            with btn_col2:
                if st.button("📝 S'INSCRIRE", use_container_width=True, key="register_btn"):
                    st.session_state.show_register = True
                    st.session_state.show_login = False
                    st.rerun()

    if st.session_state.show_register:
        show_register_page()
        return

    # Section des derniers mémoires avec style amélioré
    st.markdown("---")
    st.markdown("""
        <h2 style='
            color: var(--primary-color);
            font-size: 1.8rem;
            font-weight: 600;
            margin: 2rem 0;
            text-align: center;
        '>
            📚 Derniers mémoires ajoutés
        </h2>
    """, unsafe_allow_html=True)
    
    memoires = get_all_memoires().head(5)
    
    if len(memoires) == 0:
        st.markdown("""
            <div style='
                background-color: #E8F4F9;
                color: #2E86AB;
                padding: 1rem;
                border-radius: var(--border-radius);
                text-align: center;
                margin: 1rem 0;
            '>
                <p style='margin: 0;'>Aucun mémoire n'a encore été ajouté.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        for idx in range(len(memoires)):
            memoire = memoires.iloc[idx]
            with st.expander(f"📑 {memoire['titre']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                        <div style='
                            background: linear-gradient(135deg, var(--card-background) 0%, #f8f9fa 100%);
                            padding: 1.5rem;
                            border-radius: 15px;
                            box-shadow: 0 10px 20px rgba(0,0,0,0.05);
                            margin-bottom: 1rem;
                        '>
                            <h3 style='color: var(--primary-color); margin-bottom: 1rem;'>{memoire['titre']}</h3>
                            <p>👥 <strong>Auteurs:</strong> {memoire['auteurs']}</p>
                            <p>📅 <strong>Année:</strong> {memoire['annee_universitaire']}</p>
                            <p>👨‍🏫 <strong>Encadreur:</strong> {memoire['encadreur']}</p>
                            <p>🎓 <strong>Filière:</strong> {memoire['filiere_nom']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if not st.session_state.logged_in:
                        st.markdown("""
                            <div style='
                                background-color: #FFF3E0;
                                padding: 1rem;
                                border-radius: 10px;
                                text-align: center;
                                border: 1px solid #FFE0B2;
                                margin-bottom: 1rem;
                            '>
                                <p style='
                                    color: #E65100;
                                    margin: 0;
                                    font-size: 0.9rem;
                                    font-weight: 500;
                                '>
                                    🔒 Connectez-vous pour télécharger
                                </p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        login_col, register_col = st.columns(2)
                        with login_col:
                            if st.button("🔐 Connexion", key=f"login_btn_{memoire['id']}", use_container_width=True):
                                st.session_state.show_login = True
                                st.session_state.show_register = False
                                st.rerun()
                        with register_col:
                            if st.button("📝 Inscription", key=f"register_btn_{memoire['id']}", use_container_width=True):
                                st.session_state.show_register = True
                                st.session_state.show_login = False
                                st.rerun()
                    else:
                        if st.button("📥 Télécharger", key=f"download_{memoire['id']}", use_container_width=True):
                            get_download_link(memoire['fichier_pdf'], "Télécharger le PDF")
                
                st.info(memoire['resume'])
                st.markdown(f"**🏷️ Mots-clés:** {memoire['tags']}")

    # Section des fonctionnalités avec style amélioré
    st.markdown("---")
    st.markdown("""
        <h2 style='
            color: var(--primary-color);
            font-size: 1.8rem;
            font-weight: 600;
            margin: 2rem 0;
            text-align: center;
        '>
            ✨ Fonctionnalités
        </h2>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <div style='
                background-color: var(--card-background);
                padding: 1.5rem;
                border-radius: var(--border-radius);
                box-shadow: var(--box-shadow);
                margin: 0.5rem;
                height: 100%;
            '>
                <h3 style='color: var(--primary-color);'>🔍 Recherche avancée</h3>
                <p>Trouvez rapidement les mémoires par mots-clés, auteur, ou filière</p>
            </div>
            
            <div style='
                background-color: var(--card-background);
                padding: 1.5rem;
                border-radius: var(--border-radius);
                box-shadow: var(--box-shadow);
                margin: 0.5rem;
                height: 100%;
            '>
                <h3 style='color: var(--primary-color);'>🔒 Accès sécurisé</h3>
                <p>Vos données sont protégées avec les dernières normes de sécurité</p>
                </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div style='
                background-color: var(--card-background);
                padding: 1.5rem;
                border-radius: var(--border-radius);
                box-shadow: var(--box-shadow);
                margin: 0.5rem;
                height: 100%;
            '>
                <h3 style='color: var(--primary-color);'>📱 Interface moderne</h3>
                    <p>Une expérience utilisateur optimisée sur tous les appareils</p>
                </div>
            
            <div style='
                background-color: var(--card-background);
                padding: 1.5rem;
                border-radius: var(--border-radius);
                box-shadow: var(--box-shadow);
                margin: 0.5rem;
                height: 100%;
            '>
                <h3 style='color: var(--primary-color);'>📊 Statistiques</h3>
                    <p>Suivez les tendances et l'évolution de la base documentaire</p>
                </div>
        """, unsafe_allow_html=True)

    # Section des statistiques avec style amélioré
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <div style='
                background: linear-gradient(135deg, var(--card-background) 0%, #f8f9fa 100%);
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.05);
                margin: 1rem;
                text-align: center;
                transition: all 0.3s ease;
                border: 1px solid rgba(46, 134, 171, 0.1);
                cursor: pointer;
                position: relative;
                overflow: hidden;
            '>
                <div style='
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 4px;
                    background: linear-gradient(90deg, var(--primary-color), #60a5fa);
                '></div>
                <h3 style='
                    color: var(--primary-color);
                    font-size: 1.2rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                '>
                    <span>📚</span>
                    <span>Mémoires disponibles</span>
                </h3>
                <p style='
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: var(--primary-color);
                    margin: 0;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                '>{len(memoires)}</p>
            </div>

            <div style='
                background: linear-gradient(135deg, var(--card-background) 0%, #f8f9fa 100%);
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.05);
                margin: 1rem;
                text-align: center;
                transition: all 0.3s ease;
                border: 1px solid rgba(46, 134, 171, 0.1);
                cursor: pointer;
                position: relative;
                overflow: hidden;
            '>
                <div style='
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 4px;
                    background: linear-gradient(90deg, var(--primary-color), #60a5fa);
                '></div>
                <h3 style='
                    color: var(--primary-color);
                    font-size: 1.2rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                '>
                    <span>🏢</span>
                    <span>Départements actifs</span>
                </h3>
                <p style='
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: var(--primary-color);
                    margin: 0;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                '>8</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='
                background: linear-gradient(135deg, var(--card-background) 0%, #f8f9fa 100%);
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.05);
                margin: 1rem;
                text-align: center;
                transition: all 0.3s ease;
                border: 1px solid rgba(46, 134, 171, 0.1);
                cursor: pointer;
                position: relative;
                overflow: hidden;
            '>
                <div style='
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 4px;
                    background: linear-gradient(90deg, var(--primary-color), #60a5fa);
                '></div>
                <h3 style='
                    color: var(--primary-color);
                    font-size: 1.2rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                '>
                    <span>👥</span>
                    <span>Utilisateurs</span>
                </h3>
                <p style='
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: var(--primary-color);
                    margin: 0;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                '>500+</p>
            </div>
            
            <div style='
                background: linear-gradient(135deg, var(--card-background) 0%, #f8f9fa 100%);
                padding: 2rem;
                border-radius: 15px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.05);
                margin: 1rem;
                text-align: center;
                transition: all 0.3s ease;
                border: 1px solid rgba(46, 134, 171, 0.1);
                cursor: pointer;
                position: relative;
                overflow: hidden;
            '>
                <div style='
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 4px;
                    background: linear-gradient(90deg, var(--primary-color), #60a5fa);
                '></div>
                <h3 style='
                    color: var(--primary-color);
                    font-size: 1.2rem;
                    font-weight: 600;
                    margin-bottom: 1rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                '>
                    <span>⚡</span>
                    <span>Disponibilité du service</span>
                </h3>
                <p style='
                    font-size: 2.5rem;
                    font-weight: 700;
                    color: var(--primary-color);
                    margin: 0;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
                '>99.9%</p>
            </div>
        """, unsafe_allow_html=True)

    # Footer avec style amélioré
    st.markdown("---")
    st.markdown("""
        <div style='
            text-align: center;
            padding: 2rem 0;
            background-color: var(--card-background);
            border-radius: var(--border-radius);
            margin-top: 2rem;
        '>
            <p style='color: var(--primary-color); font-weight: 600; margin-bottom: 0.5rem;'>
                © 2024 Banque des Mémoires UNSTIM
            </p>
            <p style='color: var(--text-color); opacity: 0.8;'>
                Développé avec ❤️ pour la communauté universitaire
            </p>
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

    # Sidebar pour la navigation
    with st.sidebar:
        st.title("🎓 Mémoires Universitaires")
        st.subheader("UNSTIM")
        st.write("---")
        st.subheader("Auteurs :")
        st.write("B. Zamane SOULEMANE")
        st.write("A. Elisé LOKOSSOU")
        st.write("---")
    
    # Affichage conditionnel en fonction de l'authentification
    if st.session_state.logged_in:
        # Menu pour l'administrateur ou l'utilisateur normal
        with st.sidebar:
            if st.session_state.user_role == "admin":
                menu = st.radio("Navigation", 
                    ["Accueil", "Recherche", "Statistiques", "Gestion des Entités", 
                    "Gestion des Filières", "Gestion des Sessions", "Gestion des Mémoires", "Journal d'activité"])
            else:
                menu = st.radio("Navigation", ["Accueil", "Recherche", "Statistiques"])
            
            st.write("---")
            st.write(f"👤 Connecté en tant que : **{st.session_state.user_name}**")
            if st.button("📤 Déconnexion", type="secondary", use_container_width=True):
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
    elif st.session_state.show_login:
        if show_login_page():
            st.session_state.show_login = False
            st.rerun()
    else:
        show_welcome_page()

if __name__ == "__main__":
    main() 