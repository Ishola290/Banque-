import os
import io
import uuid
import shutil
from datetime import datetime
from pathlib import Path

class FileStorage:
    def __init__(self):
        # Créer le dossier de stockage des fichiers
        self.storage_dir = os.path.join(os.getcwd(), "data", "files")
        os.makedirs(self.storage_dir, exist_ok=True)
        print("✓ Système de stockage local initialisé")
    
    def save_file(self, file_obj, filename):
        """Sauvegarde un fichier dans le stockage local."""
        try:
            # Générer un nom unique pour le fichier
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(self.storage_dir, unique_filename)
            
            # Sauvegarder le fichier
            if hasattr(file_obj, 'read'):
                # Si c'est un objet fichier (comme UploadedFile de Streamlit)
                content = file_obj.read()
            else:
                # Si c'est déjà des bytes
                content = file_obj
            
            # Écrire le fichier
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Retourner le chemin relatif
            return True, f"local://{unique_filename}"
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier: {str(e)}")
            return False, None
    
    def get_file(self, file_path):
        """Récupère un fichier depuis le stockage local."""
        try:
            if not file_path.startswith("local://"):
                raise ValueError("Le chemin du fichier doit commencer par 'local://'")
            
            # Extraire le nom du fichier
            filename = file_path.replace("local://", "")
            full_path = os.path.join(self.storage_dir, filename)
            
            # Vérifier si le fichier existe
            if not os.path.exists(full_path):
                print(f"Fichier non trouvé: {full_path}")
                return None
            
            # Lire et retourner le contenu du fichier
            with open(full_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            print(f"Erreur lors de la récupération du fichier {file_path}: {str(e)}")
            return None
    
    def delete_file(self, file_path):
        """Supprime un fichier du stockage local."""
        try:
            if not file_path.startswith("local://"):
                raise ValueError("Le chemin du fichier doit commencer par 'local://'")
                
            filename = file_path.replace("local://", "")
            full_path = os.path.join(self.storage_dir, filename)
            
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier: {e}")
            return False
    
    def get_download_url(self, file_path, expires=3600):
        """Retourne le chemin local du fichier pour le téléchargement."""
        try:
            if not file_path.startswith("local://"):
                raise ValueError("Le chemin du fichier doit commencer par 'local://'")
                
            filename = file_path.replace("local://", "")
            full_path = os.path.join(self.storage_dir, filename)
            
            if os.path.exists(full_path):
                return full_path
            return None
        except Exception as e:
            print(f"Erreur lors de la récupération du chemin: {e}")
            return None 