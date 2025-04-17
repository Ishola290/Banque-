# Gestionnaire de Fichiers Local avec Streamlit

Une application web simple pour gérer des fichiers en local, construite avec Streamlit.

## Fonctionnalités

- Upload de fichiers
- Visualisation de la liste des fichiers stockés
- Suppression de fichiers
- Stockage local sécurisé

## Installation

1. Clonez ce dépôt :
```bash
git clone <votre-url-github>
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

Pour lancer l'application :

```bash
streamlit run streamlit_app.py
```

L'application sera accessible à l'adresse : http://localhost:8501

## Structure du projet

- `streamlit_app.py` : Application principale Streamlit
- `local_storage.py` : Gestionnaire de stockage local
- `requirements.txt` : Dépendances du projet
- `data/files/` : Dossier de stockage des fichiers (créé automatiquement) 