import ollama
from config import ConfigurationAssistant
from gui import InterfaceAssistantIA

def verifier_ollama():
    try:
        # Tenter de récupérer la liste des modèles
        modeles = ollama.list()
        print("Modèles Ollama disponibles :")
        for modele in modeles.get('models', []):
            print(f"- {modele.get('name', 'Modèle sans nom')}")
    except Exception as e:
        print(f"Erreur de connexion à Ollama : {e}")
        print("Assurez-vous qu'Ollama est lancé et accessible.")

def principale():
    print("Point d'entrée principal de l'application")
    verifier_ollama()
    
    gestionnaire_config = ConfigurationAssistant()
    application = InterfaceAssistantIA(gestionnaire_config)
    application.executer()

if __name__ == "__main__":
    principale()