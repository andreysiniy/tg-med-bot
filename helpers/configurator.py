import os.path
import configparser

class Config:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self._create_default_config()

    def _create_default_config(self):
        self.config['TELEGRAM'] = {
            'token': 'YOUR_TELEGRAM_BOT_TOKEN'
        }
        self.config['GOOGLE'] = {
            'token': 'YOUR_GOOGLE_AI_API_KEY',
            'model': 'YOUR_GOOGLE_AI_MODEL_NAME'
        }
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

    def get(self, section, option):
        return self.config.get(section, option)

    def set(self, section, option, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)