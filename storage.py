from minio import Minio
import os
import io
from datetime import timedelta
import time
import subprocess
import atexit
import shutil
from urllib3.exceptions import MaxRetryError
import uuid

class FileStorage:
    def __init__(self, max_retries=3, retry_delay=2):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = None
        self.bucket_name = "memoires"
        self.minio_process = None
        self.minio_path = os.path.join(os.getcwd(), "minio", "minio.exe")
        self.check_minio_installation()
        self.start_minio()
        self.initialize_client()
        self.ensure_bucket_exists()
    
    def check_minio_installation(self):
        """Vérifie si MinIO est installé localement."""
        if not os.path.exists(self.minio_path):
            raise RuntimeError(
                "MinIO n'est pas installé localement.\n"
                "Pour installer MinIO :\n"
                "1. Téléchargez l'exécutable depuis https://min.io/download#/windows\n"
                "2. Extrayez le fichier minio.exe\n"
                "3. Placez minio.exe dans le dossier 'minio' de votre projet"
            )
    
    def start_minio(self):
        """Démarre le serveur MinIO en arrière-plan."""
        try:
            # Créer le dossier data s'il n'existe pas
            data_dir = os.path.join(os.getcwd(), "data")
            os.makedirs(data_dir, exist_ok=True)
            
            # Démarrer MinIO
            self.minio_process = subprocess.Popen(
                [self.minio_path, "server", data_dir],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW  # Pour Windows
            )
            
            # Attendre que MinIO soit prêt
            time.sleep(2)
            
            # Enregistrer la fonction de nettoyage
            atexit.register(self.stop_minio)
            
        except Exception as e:
            print(f"Erreur lors du démarrage de MinIO: {e}")
            raise
    
    def stop_minio(self):
        """Arrête le serveur MinIO."""
        if self.minio_process:
            self.minio_process.terminate()
            self.minio_process.wait()
    
    def initialize_client(self):
        """Initialise le client MinIO avec gestion des erreurs."""
        for attempt in range(self.max_retries):
            try:
                self.client = Minio(
                    "localhost:9000",
                    access_key="minioadmin",
                    secret_key="minioadmin",
                    secure=False
                )
                # Tester la connexion
                self.client.list_buckets()
                print("Connexion à MinIO établie avec succès")
                return
            except Exception as e:
                print(f"Tentative {attempt + 1}/{self.max_retries} échouée: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception("Impossible de se connecter à MinIO après plusieurs tentatives")
    
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
                data.close()
                
        except Exception as e:
            print(f"Erreur lors de la récupération du fichier {file_path}: {str(e)}")
            return None
    
    def delete_file(self, file_path):
        """Supprime un fichier de MinIO."""
        try:
            if not self.client:
                self.initialize_client()
                
            filename = file_path.replace(f"minio://{self.bucket_name}/", "")
            self.client.remove_object(self.bucket_name, filename)
            return True
        except Exception as e:
            print(f"Erreur lors de la suppression du fichier: {e}")
            return False
    
    def get_download_url(self, file_path, expires=3600):
        """Génère une URL présignée pour le téléchargement."""
        try:
            if not self.client:
                self.initialize_client()
                
            filename = file_path.replace(f"minio://{self.bucket_name}/", "")
            url = self.client.presigned_get_object(
                self.bucket_name,
                filename,
                expires=timedelta(seconds=expires)
            )
            return url
        except Exception as e:
            print(f"Erreur lors de la génération de l'URL: {e}")
            return None 