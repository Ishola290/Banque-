import os
import requests
import zipfile
import io
import shutil

def download_minio():
    # URL de téléchargement de MinIO pour Windows
    url = "https://dl.min.io/server/minio/release/windows-amd64/archive/minio.RELEASE.2024-02-15T19-57-54Z"
    
    # Dossier de destination
    minio_dir = os.path.join(os.getcwd(), "minio")
    os.makedirs(minio_dir, exist_ok=True)
    
    print("Téléchargement de MinIO...")
    try:
        # Télécharger le fichier
        response = requests.get(url)
        response.raise_for_status()
        
        # Sauvegarder l'exécutable
        minio_path = os.path.join(minio_dir, "minio.exe")
        with open(minio_path, "wb") as f:
            f.write(response.content)
        
        print("MinIO a été téléchargé avec succès dans le dossier 'minio'")
        print(f"Chemin de l'exécutable: {minio_path}")
        
    except Exception as e:
        print(f"Erreur lors du téléchargement: {e}")
        raise

if __name__ == "__main__":
    download_minio() 