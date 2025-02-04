import tkinter as tk
import customtkinter as ctk
import ollama
import threading
import re
import random

from config import ConfigurationAssistant

class InterfaceAssistantIA(ctk.CTk):
    def __init__(self, gestionnaire_config):
        super().__init__()
        self.gestionnaire_config = gestionnaire_config
        
        # Interface de type IDE
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Assistant IA - IDE de Développement")
        self.geometry("1200x800")

        # Cadre principal de type IDE
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Barre d'outils / Menu
        self.barre_outils = ctk.CTkFrame(self, height=50)
        self.barre_outils.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        # Boutons de configuration et de contexte
        self.bouton_config = ctk.CTkButton(
            self.barre_outils, 
            text="⚙️ Configuration", 
            command=self.ouvrir_dialogue_config
        )
        self.bouton_config.pack(side='left', padx=5)

        self.selection_contexte = ctk.CTkComboBox(
            self.barre_outils, 
            values=["Développement", "Cybersécurité", "Data Science", "Cloud"],
            command=self.changer_contexte
        )
        self.selection_contexte.pack(side='left', padx=5)

        # Zone de chat avec style IDE
        self.cadre_chat = ctk.CTkScrollableFrame(
            self, 
            width=1150, 
            height=600,
            fg_color=("gray80", "gray20")  # Couleur adaptative
        )
        self.cadre_chat.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

        # Cadre de saisie avec autocomplétion
        self.cadre_saisie = ctk.CTkFrame(self)
        self.cadre_saisie.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.saisie_message = ctk.CTkEntry(
            self.cadre_saisie, 
            placeholder_text="Saisissez votre commande ou message...",
            width=1000
        )
        self.saisie_message.pack(side='left', padx=10, expand=True, fill='x')
        self.saisie_message.bind('<Return>', self.envoyer_message)
        self.saisie_message.bind('<Tab>', self.autocompletion)
        self.saisie_message.bind('<KeyRelease>', self.suggestion_commande)

        self.bouton_envoi = ctk.CTkButton(
            self.cadre_saisie, 
            text="Exécuter", 
            command=self.envoyer_message
        )
        self.bouton_envoi.pack(side='right', padx=10)

        # Liste de suggestions
        self.liste_suggestions = tk.Listbox(
            self, 
            height=5, 
            width=50, 
            bg='black', 
            fg='white'
        )
        self.liste_suggestions.grid(row=3, column=0, padx=10, sticky="ew")
        self.liste_suggestions.bind('<Double-1>', self.selectionner_suggestion)

        # Contexte initial
        self.contexte_actuel = "Développement"

    def changer_contexte(self, nouveau_contexte):
        self.contexte_actuel = nouveau_contexte
        self._ajouter_message_ia(f"Contexte changé pour : {nouveau_contexte}")

    def suggestion_commande(self, event):
        commande = self.saisie_message.get()
        suggestions = self.obtenir_suggestions(commande)
        
        self.liste_suggestions.delete(0, tk.END)
        for suggestion in suggestions:
            self.liste_suggestions.insert(tk.END, suggestion)

    def obtenir_suggestions(self, commande):
        suggestions = {
        "Développement": [
            "/generer_code_python", 
            "/debugger", 
            "/generer_classe", 
            "/refactoriser"
        ],
        "Cybersécurité": [
            "/scanner_vulnerabilite", 
            "/generer_politique", 
            "/analyser_logs"
        ],
        "Data Science": [
            "/analyser_donnees", 
            "/generer_graphique", 
            "/entrainer_modele"
        ],
        "Cloud": [
            "/deployer_container", 
            "/configurer_kubernetes", 
            "/auditer_securite"
        ]
    }
        return [cmd for cmd in suggestions.get(self.contexte_actuel, []) if cmd.startswith(commande)]

    def selectionner_suggestion(self, event):
        selection = self.liste_suggestions.get(self.liste_suggestions.curselection())
        self.saisie_message.delete(0, tk.END)
        self.saisie_message.insert(0, selection)

    def autocompletion(self, event):
        commande = self.saisie_message.get()
        suggestions = self.obtenir_suggestions(commande)
        
        if suggestions:
            self.saisie_message.delete(0, tk.END)
            self.saisie_message.insert(0, suggestions[0])
        
        return 'break'

    def envoyer_message(self, event=None):
        message = self.saisie_message.get()
        if message:
            # Vérifier si c'est une commande spéciale
            resultat_commande = self.traiter_commande_speciale(message)
            
            if resultat_commande:
                self._ajouter_message("Assistant", resultat_commande)
            else:
                # Ajouter le message de l'utilisateur
                self._ajouter_message("Utilisateur", message)
                
                # Désactiver la saisie pendant le traitement
                self.saisie_message.configure(state='disabled')
                
                # Lancer la génération de réponse dans un thread séparé
                threading.Thread(target=self._generer_reponse_ia, args=(message,), daemon=True).start()
            
            # Effacer la saisie
            self.saisie_message.delete(0, tk.END)

    def traiter_commande_speciale(self, commande):
        commandes_speciales = {
            "/generer_code python": self.generer_code_python,
            "/debugger": self.mode_debug,
            "/generer_classe": self.generer_classe,
            "/scanner_vulnerabilite": self.scanner_vulnerabilite,
            "/analyser_donnees": self.analyser_donnees
        }
        
        for prefixe, fonction in commandes_speciales.items():
            if commande.startswith(prefixe):
                return fonction(commande[len(prefixe):].strip())
        
        return None

    def generer_code_python(self, contexte):
        exemples = {
            "": "class ExempleClasse:\n    def __init__(self):\n        pass\n\n    def methode_exemple(self):\n        return 'Hello, World!'",
            "api": "import flask\n\napp = flask.Flask(__name__)\n\n@app.route('/')\ndef hello_world():\n    return 'Hello, World!'",
            "machine_learning": "import numpy as np\nfrom sklearn.linear_model import LinearRegression\n\n# Exemple de régression linéaire\nX = np.array([[1], [2], [3], [4]])\ny = np.array([2, 4, 5, 4])\n\nmodel = LinearRegression()\nmodel.fit(X, y)"
        }
        code = exemples.get(contexte, exemples[""])
        return f"```python\n{code}\n```"

    def mode_debug(self, code):
        erreurs_simulees = [
            "Aucune erreur détectée.",
            "Attention : Variable non initialisée.",
            "Syntaxe incorrecte à la ligne 3.",
            "Importation manquante : numpy"
        ]
        return random.choice(erreurs_simulees)

    def generer_classe(self, nom_classe):
        nom_classe = nom_classe or "MaClasse"
        code = f"""
class {nom_classe}:
    def __init__(self):
        \"\"\"Constructeur de la classe {nom_classe}\"\"\"
        pass

    def methode_exemple(self):
        \"\"\"Méthode exemple\"\"\"
        return "Méthode de {nom_classe}"
"""
        return f"```python\n{code}\n```"

    def scanner_vulnerabilite(self, cible):
        resultats = [
            "Aucune vulnérabilité critique détectée.",
            "Attention : Potentielle faille XSS détectée.",
            "Risque de injection SQL identifié.",
            "Configuration de sécurité recommandée."
        ]
        return random.choice(resultats)

    def analyser_donnees(self, description):
        analyses = [
            "Distribution normale détectée.",
            "Corrélation significative entre variables.",
            "Données nécessitant un prétraitement.",
            "Recommandation : Réduction de dimensionnalité"
        ]
        return random.choice(analyses)

    def _generer_reponse_ia(self, message):
        try:
            # Récupérer la configuration
            config = self.gestionnaire_config.obtenir_configuration()
            modele = config.get('modele', 'llama3.2')

            # Générer la réponse avec Ollama
            reponse = ollama.chat(
                model=modele,
                messages=[{'role': 'user', 'content': message}]
            )

            # Ajouter la réponse de l'IA
            self._ajouter_message_ia(reponse['message']['content'])
        except Exception as e:
            self._ajouter_message_ia(f"Erreur : {str(e)}")
        finally:
            # Réactiver la saisie
            self.saisie_message.configure(state='normal')

    def _ajouter_message(self, expediteur, message):
        cadre_message = ctk.CTkFrame(self.cadre_chat)
        cadre_message.pack(fill='x', padx=5, pady=5)

        # Style pour les blocs de code
        est_code = message.startswith('```') and message.endswith('```')
        
        libelle_expediteur = ctk.CTkLabel(
            cadre_message, 
            text=f"{expediteur} :", 
            font=('Helvetica', 12, 'bold')
        )
        libelle_expediteur.pack(anchor='w')

        # Style différent pour les blocs de code
        if est_code:
            message = message.strip('`')
            libelle_message = ctk.CTkTextbox(
                cadre_message, 
                width=1100, 
                height=200,
                fg_color='black',
                text_color='green',
                font=('Courier', 12)
            )
            libelle_message.pack(fill='x', padx=5, pady=5)
            libelle_message.insert('1.0', message)
            libelle_message.configure(state='disabled')
        else:
            libelle_message = ctk.CTkLabel(
                cadre_message, 
                text=message, 
                wraplength=1100, 
                justify='left'
            )
            libelle_message.pack(anchor='w')

    def _ajouter_message_ia(self, message):
        # Méthode spécifique pour ajouter les messages de l'IA
        self.saisie_message.configure(state='normal')
        self._ajouter_message("Assistant IA", message)

    def ouvrir_dialogue_config(self):
        try:
            # Récupérer les modèles disponibles
            modeles_disponibles = ollama.list()['models']
            noms_modeles = [modele.get('model', 'Modèle Inconnu') for modele in modeles_disponibles]
            
            if not noms_modeles:
                noms_modeles = ["llama3.2", "mistral", "gemma"]  # Modèles par défaut
            
            fenetre_config = ctk.CTkToplevel(self)
            fenetre_config.title("Configuration de l'Assistant")
            fenetre_config.geometry("400x300")

            # Sélection du modèle Ollama
            libelle_modele = ctk.CTkLabel(fenetre_config, text="Modèle Ollama")
            libelle_modele.pack(pady=5)
            selection_modele = ctk.CTkComboBox(
                fenetre_config, 
                values=noms_modeles  # Utiliser les modèles réellement disponibles
            )
            selection_modele.pack(pady=5)

            # Sélection du rôle
            libelle_role = ctk.CTkLabel(fenetre_config, text="Rôle de l'Assistant")
            libelle_role.pack(pady=5)
            roles_disponibles = ["Développeur", "Expert Cybersécurité", "Data Scientist", "Architecte Cloud"]
            selection_role = ctk.CTkComboBox(
                fenetre_config, 
                values=roles_disponibles
            )
            selection_role.pack(pady=5)

            # Bouton de sauvegarde
            bouton_sauvegarder = ctk.CTkButton(
                fenetre_config, 
                text="Sauvegarder la Configuration", 
                command=lambda: self.sauvegarder_configuration(
                    selection_modele.get(),
                    selection_role.get()
                )
            )
            bouton_sauvegarder.pack(pady=20)
        except Exception as e:
            # Gestion d'erreur si Ollama n'est pas disponible
            self._ajouter_message_ia(f"Erreur de configuration : {str(e)}")
            noms_modeles = ["llama3.2", "mistral", "gemma"]  # Modèles par défaut

    def sauvegarder_configuration(self, modele, role):
        nouvelle_config = {
            'modele': modele,
            'role': role
        }
        self.gestionnaire_config.sauvegarder_configuration(nouvelle_config)
        self._ajouter_message_ia(f"Configuration mise à jour. Modèle : {modele}, Rôle : {role}")

    def executer(self):
        self.mainloop()

    # Toutes les autres méthodes de la classe restent identiques