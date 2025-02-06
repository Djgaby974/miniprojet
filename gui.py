import tkinter as tk
import customtkinter as ctk
import ollama
import threading
import re
import os
import json
import pyperclip
import markdown2
from tkinter import filedialog, messagebox
from typing import List, Dict, Any
import random
import PyPDF2
import docx
import textract

# Palette de couleurs (conservée de l'ancienne implémentation)
COULEURS = {
    "fond_principal": "#1E1E2E",
    "accent_primaire": "#7E57C2",
    "accent_secondaire": "#4DB6AC",
    "texte_principal": "#E0E0E0",
    "texte_secondaire": "#B0BEC5",
    "fond_chat": "#2C3E50",
    "fond_code": "#263238",
    "fond_secondaire": "#2C3E50"
}

class ConversationOnglet(ctk.CTkFrame):
    def __init__(self, master, gestionnaire_config, **kwargs):
        super().__init__(
            master, 
            fg_color=COULEURS["fond_principal"],  
            corner_radius=10,
            **kwargs
        )
        
        self.gestionnaire_config = gestionnaire_config
        self.contexte_actuel = "Développement"
        self.fichier_charge = None
        
        # Cadre de chat avec style IDE
        self.cadre_chat = ctk.CTkScrollableFrame(
            self, 
            fg_color=COULEURS["fond_chat"],  
            corner_radius=10
        )
        self.cadre_chat.pack(expand=True, fill='both', padx=10, pady=10)
        
        # Cadre de saisie
        self.cadre_saisie = ctk.CTkFrame(
            self, 
            fg_color=COULEURS["fond_principal"]
        )
        self.cadre_saisie.pack(fill='x', padx=10, pady=10)
        
        self.saisie_message = ctk.CTkEntry(
            self.cadre_saisie, 
            placeholder_text="Saisissez votre commande ou message...",
            width=1100,
            fg_color=COULEURS["fond_chat"],
            text_color=COULEURS["texte_principal"],
            placeholder_text_color=COULEURS["texte_secondaire"]
        )
        self.saisie_message.pack(side='left', padx=10, expand=True, fill='x')
        self.saisie_message.bind('<Return>', self.envoyer_message)
        self.saisie_message.bind('<Tab>', self._autocompletion)
        self.saisie_message.bind('<KeyRelease>', self._suggestion_commande)
        
        self.bouton_envoi = ctk.CTkButton(
            self.cadre_saisie, 
            text="Envoyer", 
            command=self.envoyer_message,
            fg_color=COULEURS["accent_secondaire"],
            hover_color=COULEURS["accent_primaire"],
            text_color=COULEURS["texte_principal"]
        )
        self.bouton_envoi.pack(side='right', padx=10)
        
        # Liste de suggestions
        self.liste_suggestions = tk.Listbox(
            self, 
            height=5, 
            width=50, 
            bg=COULEURS["fond_chat"], 
            fg=COULEURS["texte_principal"],
            selectbackground=COULEURS["accent_primaire"]
        )
        self.liste_suggestions.pack(fill='x', padx=10, pady=5)
        self.liste_suggestions.bind('<Double-1>', self._selectionner_suggestion)
        
        # Barre d'outils pour les contextes
        self.barre_outils = ctk.CTkFrame(
            self, 
            fg_color="transparent", 
            corner_radius=0
        )
        self.barre_outils.pack(fill='x', padx=10, pady=5)
        
        # Sélecteur de contexte
        ctk.CTkLabel(
            self.barre_outils, 
            text="Contexte", 
            text_color=COULEURS["texte_principal"],
            font=("Arial", 12, "bold")
        ).pack(side='left', padx=(10,5))
        
        self.selection_contexte = ctk.CTkComboBox(
            self.barre_outils, 
            values=["Développement", "Cybersécurité", "Data Science", "Cloud"],
            command=self._changer_contexte,
            width=250,
            state="readonly"
        )
        self.selection_contexte.pack(side='left', padx=5)
        
        # Bouton pour charger un fichier
        self.bouton_charger = ctk.CTkButton(
            self.barre_outils, 
            text=" Charger Fichier", 
            command=self._charger_fichier,
            width=150
        )
        self.bouton_charger.pack(side='left', padx=5)
        
        # Bouton pour résumer le fichier
        self.bouton_resumer = ctk.CTkButton(
            self.barre_outils, 
            text=" Résumer", 
            command=self._resumer_fichier,
            width=150,
            state='disabled'
        )
        self.bouton_resumer.pack(side='left', padx=5)
        
    def _ajouter_message(self, expediteur, message):
        cadre_message = ctk.CTkFrame(
            self.cadre_chat, 
            fg_color=COULEURS["fond_principal"]
        )
        cadre_message.pack(fill='x', padx=5, pady=5)

        libelle_expediteur = ctk.CTkLabel(
            cadre_message, 
            text=f"{expediteur} :", 
            font=('Helvetica', 12, 'bold'),
            text_color=COULEURS["accent_secondaire"]
        )
        libelle_expediteur.pack(anchor='w')

        libelle_message = ctk.CTkLabel(
            cadre_message, 
            text=message, 
            wraplength=1200, 
            justify='left',
            text_color=COULEURS["texte_principal"]
        )
        libelle_message.pack(anchor='w')
        
    def envoyer_message(self, event=None):
        message = self.saisie_message.get()
        if message:
            # Vérifier si c'est une commande spéciale
            resultat_commande = self._traiter_commande_speciale(message)
            
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
        
        if message and self.fichier_charge:
            # Si un fichier est chargé, proposer des interactions
            interactions = [
                "Peux-tu résumer ce document ?",
                "Quels sont les points clés ?",
                "Explique-moi ce document"
            ]
            
            # Ajouter des suggestions d'interaction avec le document
            self.liste_suggestions.delete(0, tk.END)
            for interaction in interactions:
                self.liste_suggestions.insert(tk.END, interaction)
        
    def _generer_reponse_ia(self, message):
        try:
            # Récupérer la configuration
            config = self.gestionnaire_config.obtenir_configuration()
            modele = config.get('modeles', {}).get('actif', 'llama3.2')

            # Prompts spécifiques par contexte
            prompts_contextuels = {
                "Développement": """
                Tu es un expert en développement logiciel. 
                Réponds aux questions techniques avec précision et des exemples de code.
                Utilise les bonnes pratiques de programmation et explique clairement.
                """,
                "Cybersécurité": """
                Tu es un expert en cybersécurité. 
                Analyse les questions sous l'angle de la sécurité informatique.
                Fournis des recommandations de sécurité et explique les risques potentiels.
                """,
                "Data Science": """
                Tu es un data scientist expérimenté. 
                Réponds aux questions avec des insights analytiques et statistiques.
                Propose des approches méthodologiques et des techniques d'analyse.
                """,
                "Cloud": """
                Tu es un architecte cloud et expert en infrastructure.
                Réponds aux questions sur les technologies cloud, l'architecture et le déploiement.
                Donne des conseils pratiques sur les solutions cloud.
                """
            }

            # Prompt de système pour le contexte actuel
            prompt_systeme = prompts_contextuels.get(self.contexte_actuel, """
            Tu es un assistant IA conversationnel. 
            Réponds TOUJOURS en français avec précision et clarté.
            """)

            # Générer la réponse avec Ollama
            reponse = ollama.chat(
                model=modele,
                messages=[
                    {'role': 'system', 'content': prompt_systeme},
                    {'role': 'user', 'content': message}
                ]
            )

            # Ajouter la réponse de l'IA
            self._ajouter_message("Assistant IA", reponse['message']['content'])
        except Exception as e:
            self._ajouter_message("Assistant IA", f"Erreur : {str(e)}")
        finally:
            # Réactiver la saisie
            self.saisie_message.configure(state='normal')

    def _changer_contexte(self, nouveau_contexte):
        """Change le contexte de la conversation"""
        self.contexte_actuel = nouveau_contexte
        self._ajouter_message("Système", f"Contexte changé pour : {nouveau_contexte}")
        
    def _suggestion_commande(self, event):
        """Génère des suggestions de commandes basées sur le contexte"""
        commande = self.saisie_message.get()
        suggestions = self._obtenir_suggestions(commande)
        
        self.liste_suggestions.delete(0, tk.END)
        for suggestion in suggestions:
            self.liste_suggestions.insert(tk.END, suggestion)
        
    def _obtenir_suggestions(self, commande):
        """Retourne les suggestions de commandes par contexte"""
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
    
    def _selectionner_suggestion(self, event):
        """Sélectionne une suggestion de la liste"""
        selection = self.liste_suggestions.get(self.liste_suggestions.curselection())
        self.saisie_message.delete(0, tk.END)
        self.saisie_message.insert(0, selection)
    
    def _autocompletion(self, event):
        """Complète automatiquement la commande"""
        commande = self.saisie_message.get()
        suggestions = self._obtenir_suggestions(commande)
        
        if suggestions:
            self.saisie_message.delete(0, tk.END)
            self.saisie_message.insert(0, suggestions[0])
        
        return 'break'
    
    def _traiter_commande_speciale(self, commande):
        """Traite les commandes spéciales"""
        commandes_speciales = {
            "/generer_code_python": self._generer_code_python,
            "/debugger": self._mode_debug,
            "/generer_classe": self._generer_classe,
            "/scanner_vulnerabilite": self._scanner_vulnerabilite,
            "/analyser_donnees": self._analyser_donnees
        }
        
        for prefixe, fonction in commandes_speciales.items():
            if commande.startswith(prefixe):
                return fonction(commande[len(prefixe):].strip())
        
        return None
    
    def _generer_code_python(self, contexte):
        """Génère un exemple de code Python"""
        exemples = {
            "": "class ExempleClasse:\n    def __init__(self):\n        pass\n\n    def methode_exemple(self):\n        return 'Hello, World!'",
            "api": "import flask\n\napp = flask.Flask(__name__)\n\n@app.route('/')\ndef hello_world():\n    return 'Hello, World!'",
            "machine_learning": "import numpy as np\nfrom sklearn.linear_model import LinearRegression\n\n# Exemple de régression linéaire\nX = np.array([[1], [2], [3], [4]])\ny = np.array([2, 4, 5, 4])\n\nmodel = LinearRegression()\nmodel.fit(X, y)"
        }
        code = exemples.get(contexte, exemples[""])
        return f"```python\n{code}\n```"

    def _mode_debug(self, code):
        """Simule un débogage"""
        erreurs_simulees = [
            "Aucune erreur détectée.",
            "Attention : Variable non initialisée.",
            "Syntaxe incorrecte à la ligne 3.",
            "Importation manquante : numpy"
        ]
        return random.choice(erreurs_simulees)

    def _generer_classe(self, nom_classe):
        """Génère une classe Python"""
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

    def _scanner_vulnerabilite(self, cible):
        """Simule un scan de vulnérabilité"""
        resultats = [
            "Aucune vulnérabilité critique détectée.",
            "Attention : Potentielle faille XSS détectée.",
            "Risque de injection SQL identifié.",
            "Configuration de sécurité recommandée."
        ]
        return random.choice(resultats)

    def _analyser_donnees(self, description):
        """Simule une analyse de données"""
        analyses = [
            "Distribution normale détectée.",
            "Corrélation significative entre variables.",
            "Données nécessitant un prétraitement.",
            "Recommandation : Réduction de dimensionnalité"
        ]
        return random.choice(analyses)

    def _charger_fichier(self):
        """Charge un fichier et prépare pour résumé"""
        try:
            # Ouvrir le sélecteur de fichier
            chemin_fichier = filedialog.askopenfilename(
                title="Sélectionner un fichier",
                filetypes=[
                    ("Tous les fichiers", "*.*"),
                    ("Fichiers PDF", "*.pdf"),
                    ("Documents Word", "*.docx"),
                    ("Fichiers Texte", "*.txt"),
                ]
            )
            
            if not chemin_fichier:
                return
            
            # Extraire le texte selon le type de fichier
            self.fichier_charge = self._extraire_texte(chemin_fichier)
            
            # Activer le bouton de résumé
            self.bouton_resumer.configure(state='normal')
            
            # Afficher un message de confirmation
            self._ajouter_message("Système", f"Fichier chargé : {os.path.basename(chemin_fichier)}")
            
        except Exception as e:
            self._ajouter_message("Système", f"Erreur de chargement : {str(e)}")
        
    def _extraire_texte(self, chemin_fichier):
        """Extrait le texte de différents types de fichiers"""
        extension = os.path.splitext(chemin_fichier)[1].lower()
        
        try:
            if extension == '.pdf':
                with open(chemin_fichier, 'rb') as fichier:
                    lecteur_pdf = PyPDF2.PdfReader(fichier)
                    texte = ""
                    for page in lecteur_pdf.pages:
                        texte += page.extract_text()
            elif extension == '.docx':
                doc = docx.Document(chemin_fichier)
                texte = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            elif extension in ['.txt', '.md']:
                with open(chemin_fichier, 'r', encoding='utf-8') as fichier:
                    texte = fichier.read()
            else:
                # Utiliser textract pour les autres formats
                texte = textract.process(chemin_fichier).decode('utf-8')
            
            return texte
        except Exception as e:
            self._ajouter_message("Système", f"Erreur d'extraction : {str(e)}")
            return None
        
    def _resumer_fichier(self):
        """Génère un résumé du fichier chargé"""
        if not self.fichier_charge:
            self._ajouter_message("Système", "Aucun fichier chargé.")
            return
        
        try:
            # Générer un résumé avec Ollama
            reponse = ollama.chat(
                model='llama3.2',
                messages=[
                    {
                        'role': 'system', 
                        'content': """
                        Tu es un assistant spécialisé en résumé de documents.
                        Fournis un résumé concis, structuré et informatif.
                        Mets en évidence les points clés et les informations principales.
                        """
                    },
                    {
                        'role': 'user', 
                        'content': f"Résume ce document :\n\n{self.fichier_charge[:4000]}"
                    }
                ]
            )
            
            # Afficher le résumé
            self._ajouter_message("Résumé", reponse['message']['content'])
            
        except Exception as e:
            self._ajouter_message("Système", f"Erreur de résumé : {str(e)}")
        
class InterfaceAssistantIA(ctk.CTk):
    def __init__(self, gestionnaire_config):
        super().__init__()
        
        # Configuration de base
        self.title(" Assistant IA - Style ChatGPT")
        self.geometry("1600x900")
        
        # Centrer la fenêtre sur l'écran
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 1600) // 2
        y = (screen_height - 900) // 2
        self.geometry(f'1600x900+{x}+{y}')
        
        # Configuration du thème
        ctk.set_appearance_mode("dark")  # Mode sombre par défaut
        ctk.set_default_color_theme("blue")  # Thème de couleur
        
        # Gestionnaire de configuration
        self.gestionnaire_config = gestionnaire_config
        
        # Création de la structure principale
        self._creer_interface_principale()
        
    def _creer_interface_principale(self):
        """Crée l'interface principale avec système d'onglets"""
        # Configuration du grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Barre latérale pour l'historique
        self.barre_laterale = ctk.CTkFrame(
            self, 
            width=250, 
            fg_color=COULEURS["fond_secondaire"]
        )
        self.barre_laterale.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Bouton pour nouvelle conversation
        self.bouton_nouvelle_conv = ctk.CTkButton(
            self.barre_laterale, 
            text=" Nouvelle conversation", 
            command=self._creer_nouvelle_conversation,
            fg_color=COULEURS["accent_primaire"],
            hover_color=COULEURS["accent_secondaire"]
        )
        self.bouton_nouvelle_conv.pack(pady=10, padx=10, fill="x")
        
        # Liste des conversations historiques
        self.liste_historique = ctk.CTkScrollableFrame(
            self.barre_laterale, 
            fg_color="transparent"
        )
        self.liste_historique.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Zone d'onglets
        self.gestionnaire_onglets = ctk.CTkTabview(
            self, 
            width=1350,  
            height=800,
            fg_color=COULEURS["fond_principal"]
        )
        self.gestionnaire_onglets.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Créer un premier onglet par défaut
        self._creer_nouvelle_conversation()
        
    def _creer_nouvelle_conversation(self):
        """Crée une nouvelle conversation"""
        titre = f"Conversation {len(list(self.gestionnaire_onglets._tab_dict.keys())) + 1}"
        nouvel_onglet = self.gestionnaire_onglets.add(titre)
        
        # Créer l'onglet de conversation
        conversation_onglet = ConversationOnglet(
            nouvel_onglet, 
            self.gestionnaire_config
        )
        conversation_onglet.pack(fill='both', expand=True)
        
        # Ajouter un bouton dans l'historique
        bouton_conv = ctk.CTkButton(
            self.liste_historique, 
            text=titre, 
            command=lambda t=titre: self.gestionnaire_onglets.set(t),
            fg_color=COULEURS["fond_secondaire"],
            hover_color=COULEURS["accent_primaire"]
        )
        bouton_conv.pack(pady=5, fill="x")
        
    def executer(self):
        """Lance l'application"""
        self.mainloop()