import streamlit as st
from local_storage import storage
import os

st.title("Gestionnaire de fichiers local")

# Upload de fichier
uploaded_file = st.file_uploader("Choisissez un fichier", type=None)
if uploaded_file is not None:
    success, file_path = storage.save_file(uploaded_file)
    if success:
        st.success(f"Fichier sauvegardé avec succès! Chemin: {file_path}")
    else:
        st.error("Erreur lors de la sauvegarde du fichier")

# Liste des fichiers
st.subheader("Fichiers stockés")
files = os.listdir(storage.storage_path)
for file in files:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.write(f"📄 {file}")
    with col2:
        if st.button("Supprimer", key=file):
            if storage.delete_file(f"local://{file}"):
                st.success("Fichier supprimé avec succès!")
                st.rerun()
            else:
                st.error("Erreur lors de la suppression") 