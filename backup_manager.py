import os
import shutil
from datetime import datetime
import sqlite3
import time

class BackupManager:
    def __init__(self):
        # Création des dossiers nécessaires
        self.backup_dir = "data/backups"
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Configuration
        self.db_path = "data/memoires_db.sqlite"
        self.max_backups = 5  # Nombre maximum de sauvegardes à conserver
        
    def create_backup(self):
        """Crée une sauvegarde de la base de données."""
        try:
            # Vérifier que la base existe
            if not os.path.exists(self.db_path):
                print("Base de données non trouvée.")
                return False
                
            # Créer le nom du fichier de sauvegarde avec la date
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}.sqlite")
            
            # Attendre que la base soit disponible
            while True:
                try:
                    # Tester la connexion
                    conn = sqlite3.connect(self.db_path)
                    conn.close()
                    break
                except sqlite3.OperationalError:
                    time.sleep(1)
            
            # Copier le fichier
            shutil.copy2(self.db_path, backup_path)
            print(f"Sauvegarde créée : {backup_path}")
            
            # Nettoyer les anciennes sauvegardes
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la sauvegarde : {str(e)}")
            return False
    
    def _cleanup_old_backups(self):
        """Supprime les sauvegardes les plus anciennes si nécessaire."""
        try:
            # Lister toutes les sauvegardes
            backups = []
            for f in os.listdir(self.backup_dir):
                if f.startswith("backup_") and f.endswith(".sqlite"):
                    full_path = os.path.join(self.backup_dir, f)
                    backups.append((full_path, os.path.getmtime(full_path)))
            
            # Trier par date de modification
            backups.sort(key=lambda x: x[1], reverse=True)
            
            # Supprimer les plus anciennes
            for backup_path, _ in backups[self.max_backups:]:
                os.remove(backup_path)
                print(f"Ancienne sauvegarde supprimée : {backup_path}")
                
        except Exception as e:
            print(f"Erreur lors du nettoyage des sauvegardes : {str(e)}")
    
    def restore_backup(self, backup_name):
        """Restaure une sauvegarde spécifique."""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if not os.path.exists(backup_path):
                print("Sauvegarde non trouvée.")
                return False
            
            # Créer une copie de sécurité avant la restauration
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_copy = f"{self.db_path}.{timestamp}.safety"
            shutil.copy2(self.db_path, safety_copy)
            
            # Restaurer la sauvegarde
            shutil.copy2(backup_path, self.db_path)
            print(f"Base de données restaurée depuis : {backup_path}")
            print(f"Une copie de sécurité a été créée : {safety_copy}")
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la restauration : {str(e)}")
            return False
    
    def list_backups(self):
        """Liste toutes les sauvegardes disponibles."""
        try:
            backups = []
            for f in os.listdir(self.backup_dir):
                if f.startswith("backup_") and f.endswith(".sqlite"):
                    path = os.path.join(self.backup_dir, f)
                    size = os.path.getsize(path) / (1024 * 1024)  # Taille en MB
                    date = datetime.fromtimestamp(os.path.getmtime(path))
                    backups.append({
                        'name': f,
                        'size': f"{size:.2f} MB",
                        'date': date.strftime("%Y-%m-%d %H:%M:%S")
                    })
            return backups
        except Exception as e:
            print(f"Erreur lors de la liste des sauvegardes : {str(e)}")
            return []

# Exemple d'utilisation
if __name__ == "__main__":
    backup_mgr = BackupManager()
    
    # Créer une sauvegarde
    backup_mgr.create_backup()
    
    # Lister les sauvegardes
    backups = backup_mgr.list_backups()
    print("\nSauvegardes disponibles :")
    for backup in backups:
        print(f"Nom: {backup['name']}")
        print(f"Taille: {backup['size']}")
        print(f"Date: {backup['date']}")
        print("---") 