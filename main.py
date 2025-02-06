import ollama
import logging
from logging.handlers import RotatingFileHandler
import sys
from config import ConfigurationAssistant
from gui import InterfaceAssistantIA

def configurer_logging():
    """Configure un système de logging robuste"""
    logger = logging.getLogger('AssistantIA')
    logger.setLevel(logging.INFO)
    
    # Logging vers fichier
    file_handler = RotatingFileHandler(
        'assistant_ia.log', 
        maxBytes=10*1024*1024,  # 10 Mo
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # Logging vers console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def verifier_ollama(logger):
    """Vérifie la disponibilité d'Ollama avec logging détaillé"""
    try:
        modeles = ollama.list()
        logger.info("Connexion à Ollama réussie")
        logger.info("Modèles Ollama disponibles :")
        for modele in modeles.get('models', []):
            logger.info(f"- {modele.get('name', 'Modèle sans nom')}")
    except Exception as e:
        logger.error(f"Erreur de connexion à Ollama : {e}")
        logger.warning("Assurez-vous qu'Ollama est lancé et accessible.")
        sys.exit(1)

def principale():
    logger = configurer_logging()
    logger.info("Démarrage de l'Assistant IA")
    
    try:
        verifier_ollama(logger)
        
        gestionnaire_config = ConfigurationAssistant()
        application = InterfaceAssistantIA(gestionnaire_config)
        
        logger.info("Lancement de l'interface utilisateur")
        application.executer()
        
    except Exception as e:
        logger.critical(f"Erreur fatale : {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Fermeture de l'Assistant IA")

if __name__ == "__main__":
    principale()