from minio import Minio
import os
import io
from datetime import timedelta
import time
import subprocess
import atexit
import uuid
from dotenv import load_dotenv

class FileStorage:
    def __init__(self):
        # Charger les variables d'environnement
        load_dotenv()
        
        # Détecter l'environnement
        self.is_production = os.getenv('PRODUCTION', 'false').lower() == 'true'
        
        if self.is_production:
            # Configuration pour la production
            self.endpoint = os.getenv('MINIO_ENDPOINT')
            self.access_key = os.getenv('MINIO_ACCESS_KEY')
            self.secret_key = os.getenv('MINIO_SECRET_KEY')
            self.bucket_name = os.getenv('MINIO_BUCKET_NAME')
            self.secure = True
            
            if not all([self.endpoint, self.access_key, self.secret_key, self.bucket_name]):
                raise ValueError("Les configurations MinIO sont manquantes dans les variables d'environnement")
        else:
            # Configuration pour le développement local
            self.endpoint = "localhost:9000"
            self.access_key = "minioadmin"
            self.secret_key = "minioadmin"
            self.bucket_name = "memoires"
            self.secure = False
            self.minio_process = None
            
            # Démarrer le serveur MinIO local
            self.start_local_minio()
        
        self.initialize_client()
        self.ensure_bucket_exists()
    
    def start_local_minio(self):
        """Démarre le serveur MinIO local en développement."""
        if not self.is_production:
            try:
                # Créer le dossier data s'il n'existe pas
                data_dir = os.path.join(os.getcwd(), "data")
                os.makedirs(data_dir, exist_ok=True)
                
                # Chemin vers minio.exe
                minio_path = os.path.join(os.getcwd(), "minio", "minio.exe")
                
                if not os.path.exists(minio_path):
                    raise RuntimeError(
                        "MinIO n'est pas installé localement.\n"
                        "Pour installer MinIO :\n"
                        "1. Téléchargez l'exécutable depuis https://min.io/download#/windows\n"
                        "2. Créez un dossier 'minio' dans votre projet\n"
                        "3. Placez minio.exe dans le dossier 'minio'"
                    )
                
                # Démarrer MinIO
                self.minio_process = subprocess.Popen(
                    [minio_path, "server", data_dir],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                # Attendre que MinIO soit prêt
                time.sleep(2)
                
                # Enregistrer la fonction de nettoyage
                atexit.register(self.stop_local_minio)
                
            except Exception as e:
                print(f"Erreur lors du démarrage de MinIO local: {e}")
                raise
    
    def stop_local_minio(self):
        """Arrête le serveur MinIO local."""
        if not self.is_production and self.minio_process:
            self.minio_process.terminate()
            self.minio_process.wait()
    
    def initialize_client(self):
        """Initialise le client MinIO."""
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            # Tester la connexion
            self.client.list_buckets()
            env_type = "production" if self.is_production else "développement"
            print(f"Connexion à MinIO ({env_type}) établie avec succès")
        except Exception as e:
            raise Exception(f"Impossible de se connecter à MinIO: {str(e)}")
    
    def ensure_bucket_exists(self):
        """S'assure que le bucket existe, le crée si nécessaire."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Bucket '{self.bucket_name}' créé avec succès")
            else:
                print(f"Bucket '{self.bucket_name}' existe déjà")
        except Exception as e:
            raise Exception(f"Erreur lors de la vérification/création du bucket: {str(e)}")
    
    def save_file(self, file_obj, filename):
        """Sauvegarde un fichier dans MinIO."""
        try:
            # Générer un nom unique pour le fichier
            object_name = f"{uuid.uuid4()}_{filename}"
            
            # Sauvegarder le fichier
            if hasattr(file_obj, 'read'):
                # Si c'est un objet fichier (comme UploadedFile de Streamlit)
                content = file_obj.read()
                content_type = "application/pdf"  # Pour les fichiers PDF
            else:
                # Si c'est déjà des bytes
                content = file_obj
                content_type = "application/pdf"

            # Mettre le fichier dans MinIO
            self.client.put_object(
                self.bucket_name,
                object_name,
                io.BytesIO(content),
                len(content),
                content_type=content_type
            )
            
            # Retourner le chemin MinIO
            return True, f"minio://{object_name}"
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du fichier: {str(e)}")
            return False, None
    
    def get_file(self, file_path):
        """Récupère un fichier depuis MinIO."""
        try:
            if not file_path.startswith("minio://"):
                raise ValueError("Le chemin du fichier doit commencer par 'minio://'")
            
            # Extraire le nom du fichier du chemin minio://
            object_name = file_path.replace("minio://", "")
            
            # Récupérer l'objet
            try:
                data = self.client.get_object(self.bucket_name, object_name)
                return data.read()
            finally:
                if 'data' in locals():
                    data.close()
                
        except Exception as e:
            print(f"Erreur lors de la récupération du fichier {file_path}: {str(e)}")
            return None
    
    def delete_file(self, file_path):
        """Supprime un fichier de MinIO."""
        try:
            if not file_path.startswith("minio://"):
                raise ValueError("Le chemin du fichier doit commencer par 'minio://'")
                
            object_name = file_path.replace("minio://", "")
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier: {e}")
            return False
    
    def get_download_url(self, file_path, expires=3600):
        """Génère une URL présignée pour le téléchargement."""
        try:
            if not file_path.startswith("minio://"):
                raise ValueError("Le chemin du fichier doit commencer par 'minio://'")
                
            object_name = file_path.replace("minio://", "")
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except Exception as e:
            print(f"Erreur lors de la génération de l'URL: {e}")
            return None 