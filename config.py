import json
import os
from typing import Dict, Any, List

class ConfigurationAssistant:
    def __init__(self, chemin_config='configuration.json'):
        self.chemin_config = chemin_config
        self.configuration = self._charger_configuration()

    def _charger_configuration(self):
        config_defaut = {
            'modeles': {
                'actif': 'llama3.2',
                'disponibles': ['llama3.2', 'mistral', 'gemma'],
                'parametres': {
                    'temperature': 0.7,
                    'max_tokens': 4096,
                    'top_p': 0.9
                }
            },
            'conversation': {
                'historique_max': 20,  # Nombre maximum de messages à conserver
                'taille_contexte_max': 8192,  # Tokens maximum dans le contexte
                'mode_contexte': 'rolling_window'  # Stratégie de gestion du contexte
            },
            'role': 'Assistant Général',
            'theme': 'sombre',
            'taille_police': 12,
            'langue': 'français',
            'prompt_systeme': """
            Tu es un assistant IA conversationnel avancé. 
            Règles importantes :
            - Réponds TOUJOURS en français
            - Sois précis et concis
            - Adapte ton langage au contexte de la conversation
            - Utilise du markdown pour formater les réponses complexes
            - Gère les demandes techniques avec une grande expertise
            """
        }

        if os.path.exists(self.chemin_config):
            try:
                with open(self.chemin_config, 'r', encoding='utf-8') as fichier:
                    config_sauvegardee = json.load(fichier)
                    return {**config_defaut, **config_sauvegardee}
            except (json.JSONDecodeError, IOError):
                return config_defaut
        return config_defaut

    def sauvegarder_configuration(self, nouvelle_config: Dict[str, Any]):
        self.configuration.update(nouvelle_config)
        with open(self.chemin_config, 'w', encoding='utf-8') as fichier:
            json.dump(self.configuration, fichier, indent=4, ensure_ascii=False)

    def obtenir_configuration(self) -> Dict[str, Any]:
        return self.configuration.copy()

    def obtenir_modele_actif(self) -> str:
        return self.configuration['modeles']['actif']

    def obtenir_modeles_disponibles(self) -> List[str]:
        return self.configuration['modeles']['disponibles']

    def obtenir_parametres_modele(self) -> Dict[str, Any]:
        return self.configuration['modeles']['parametres']