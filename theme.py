import streamlit as st

# Couleurs du thème
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#6C63FF',
    'background': '#F0F2F6',
    'text': '#333333',
    'success': '#28a745',
    'warning': '#ffc107',
    'error': '#dc3545'
}

# Configuration globale du thème Streamlit
def setup_theme():
    # CSS Global
    st.markdown("""
        <style>
            /* Variables CSS globales */
            :root {
                --primary-color: #2E86AB;
                --secondary-color: #6C63FF;
                --background-color: #F0F2F6;
                --text-color: #333333;
                --card-background: #FFFFFF;
                --hover-color: #247297;
            }

            /* Style général */
            .stApp {
                background-color: var(--background-color);
            }

            /* En-têtes */
            h1, h2, h3, h4, h5, h6 {
                color: var(--primary-color) !important;
                font-weight: 600;
            }

            /* Conteneurs et cartes */
            .st-emotion-cache-1r6slb0, .element-container {
                background-color: var(--card-background);
                border-radius: 10px;
                padding: 1.5rem;
                margin: 0.5rem 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }

            /* Boutons */
            .stButton > button {
                background-color: var(--primary-color);
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0.5rem 1rem;
                transition: all 0.3s ease;
            }

            .stButton > button:hover {
                background-color: var(--hover-color);
                transform: translateY(-1px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }

            /* Inputs et sélecteurs */
            .stSelectbox, .stTextInput, .stTextArea {
                background-color: var(--card-background);
                border-radius: 4px;
            }

            /* DataFrames et tables */
            .dataframe {
                background-color: var(--card-background);
                border-radius: 8px;
                overflow: hidden;
            }

            .dataframe th {
                background-color: var(--primary-color);
                color: white;
                padding: 0.5rem;
            }

            .dataframe td {
                border-bottom: 1px solid #eee;
                padding: 0.5rem;
            }

            /* Métriques */
            .stMetric {
                background-color: var(--card-background);
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }

            /* Sidebar */
            .css-1d391kg {
                background-color: var(--primary-color);
            }

            /* Animations */
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            .animate-fade-in {
                animation: fadeIn 0.5s ease-out;
            }

            /* Responsive design */
            @media (max-width: 768px) {
                .stButton > button {
                    width: 100%;
                }
                
                .element-container {
                    padding: 1rem;
                }
                
                h1 { font-size: 1.75rem; }
                h2 { font-size: 1.5rem; }
                h3 { font-size: 1.25rem; }
            }
        </style>
    """, unsafe_allow_html=True)

# Composants réutilisables
def card(title, content, icon=""):
    """Crée une carte stylisée avec titre et contenu"""
    st.markdown(f"""
        <div class="element-container animate-fade-in">
            <h3>{icon} {title}</h3>
            <p>{content}</p>
        </div>
    """, unsafe_allow_html=True)

def section_title(title, icon=""):
    """Affiche un titre de section stylisé"""
    st.markdown(f"""
        <h2 class="animate-fade-in" style="margin-bottom: 1.5rem;">
            {icon} {title}
        </h2>
    """, unsafe_allow_html=True)

def metric_card(title, value, icon="", delta=None):
    """Affiche une métrique dans une carte stylisée"""
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(f"### {icon}")
    with col2:
        if delta:
            st.metric(title, value, delta)
        else:
            st.metric(title, value)

def action_button(label, icon="", key=None):
    """Crée un bouton d'action stylisé"""
    return st.button(f"{icon} {label}", key=key, use_container_width=True)

def info_card(message, type="info"):
    """Affiche un message d'information stylisé"""
    icons = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌"
    }
    st.markdown(f"""
        <div class="element-container" style="border-left: 4px solid {COLORS[type]};">
            <p>{icons[type]} {message}</p>
        </div>
    """, unsafe_allow_html=True)

def data_table(df, title=""):
    """Affiche un tableau de données stylisé"""
    if title:
        st.markdown(f"### {title}")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

def search_filter(placeholder="Rechercher...", key=None):
    """Crée un champ de recherche stylisé"""
    return st.text_input("", placeholder=placeholder, key=key)

def status_badge(status, text):
    """Affiche un badge de statut stylisé"""
    colors = {
        "success": "#28a745",
        "warning": "#ffc107",
        "error": "#dc3545",
        "info": "#17a2b8"
    }
    return st.markdown(f"""
        <span style="
            background-color: {colors[status]};
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.875rem;
        ">{text}</span>
    """, unsafe_allow_html=True) 