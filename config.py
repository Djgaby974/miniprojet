import json
import os

class ConfigurationAssistant:
    def __init__(self, chemin_config='configuration.json'):
        self.chemin_config = chemin_config
        self.configuration = self._charger_configuration()

    def _charger_configuration(self):
        config_defaut = {
            'modele': 'llama3.2',  # Modèle par défaut mis à llama3.2
            'role': 'Assistant Général',
            'theme': 'sombre',
            'taille_police': 12,
            'langue': 'français'
        }

        if os.path.exists(self.chemin_config):
            try:
                with open(self.chemin_config, 'r', encoding='utf-8') as fichier:
                    config_sauvegardee = json.load(fichier)
                    return {**config_defaut, **config_sauvegardee}
            except (json.JSONDecodeError, IOError):
                return config_defaut
        return config_defaut

    def sauvegarder_configuration(self, nouvelle_config):
        self.configuration.update(nouvelle_config)
        with open(self.chemin_config, 'w', encoding='utf-8') as fichier:
            json.dump(self.configuration, fichier, indent=4, ensure_ascii=False)

    def obtenir_configuration(self):
        return self.configuration.copy()