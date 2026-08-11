import json
import os
import re

class Configuration:
    def __init__(self, logger):
        self.logger = logger
        self.signal_service = os.environ["SIGNAL_SERVICE"]
        self.phone_number = os.environ["PHONE_NUMBER"]
        self.log_level = os.environ.get('LOGLEVEL', 'INFO').upper()
        self.log_tag = os.environ.get('LOGTAG', 'DEV')
        self.welcome_cnc = os.environ["WELCOME_CNC"]
        self.welcome_managers = re.split(r'[\s|,:]+', os.environ["WELCOME_MANAGER"])
        self.instant_welcome = json.loads(os.environ.get('INSTANT_WELCOME', 'true'))
        self.reminder_times = os.environ.get('REMINDER_TIMES', '13') # once a day, US timezone friendly
        self.welcome_times = os.environ.get('WELCOME_TIMES', '*') # once and hour on the hour


    def to_strings(self):
        return [ f'{key}={value}' for (key,value) in vars(self).items() if key not in ["logger"] ]
