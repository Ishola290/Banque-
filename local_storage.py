import os
import shutil
from datetime import datetime
import uuid

class LocalStorage:
    def __init__(self):
        self.storage_path = os.getenv('LOCAL_STORAGE_PATH', 'data/files')
        os.makedirs(self.storage_path, exist_ok=True)
    
    def save_file(self, file_obj, filename=None):
        """Sauvegarde un fichier dans le stockage local."""
        try:
            if filename is None:
                # Générer un nom unique
                ext = os.path.splitext(file_obj.name)[1]
                filename = f"{uuid.uuid4()}{ext}"
            
            # Créer le chemin complet
            file_path = os.path.join(self.storage_path, filename)
            
            # Sauvegarder le fichier
            with open(file_path, 'wb') as f:
                if hasattr(file_obj, 'read'):
                    # Si c'est un objet fichier
                    shutil.copyfileobj(file_obj, f)
                else:
                    # Si c'est des bytes
                    f.write(file_obj)
            
            # Retourner le chemin relatif
            return True, f"local://{filename}"
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier : {str(e)}")
            return False, None
    
    def get_file(self, file_path):
        """Récupère un fichier du stockage local."""
        try:
            if file_path.startswith('local://'):
                filename = file_path.replace('local://', '')
                full_path = os.path.join(self.storage_path, filename)
                
                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        return f.read()
            return None
            
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier : {str(e)}")
            return None
    
    def delete_file(self, file_path):
        """Supprime un fichier du stockage local."""
        try:
            if file_path.startswith('local://'):
                filename = file_path.replace('local://', '')
                full_path = os.path.join(self.storage_path, filename)
                
                if os.path.exists(full_path):
                    os.remove(full_path)
                    return True
            return False
            
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier : {str(e)}")
            return False

# Instance globale du gestionnaire de stockage local
storage = LocalStorage() 