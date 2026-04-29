from dotenv import load_dotenv
import logging
import os
from pathlib import Path
import re
from signalbot import SignalBot, Config, SQLiteConfig, enable_console_logging

from . import cnc
from . import motd
from . import store

logger = logging.getLogger("welcomebot")
config_directory = os.environ["HOME"] / Path('.local/share/welcomebot')
 
def loop():
    logger.info("main init")
    bot = SignalBot(
        Config(
            signal_service=os.environ["SIGNAL_SERVICE"],
            phone_number=os.environ["PHONE_NUMBER"],
            storage=SQLiteConfig(
                sqlite_db=config_directory / 'signalbot_internal_state.db',
            )
        )
    )

    cnc_id = os.environ["WELCOME_CNC"]
    managers = re.split(r'[\s|,:]+', os.environ["WELCOME_MANAGER"])

    bot_store = store.BotStore(logger, db=config_directory / "bot_memory.db")
    bot.register(cnc.CNCCommand(logger, managers, cnc_id, bot_store), groups=[cnc_id]) # monitor other groups
    bot.register(motd.MotDCommand(logger, cnc_id, bot_store)) # monitor other groups
    logger.info("bot started")
    bot.start()


def main():
    # signalbot logs
    enable_console_logging(logging.WARNING)
    load_dotenv()

    # welcomebot logs
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    logtag = os.environ["LOGTAG"] if "LOGTAG" in os.environ else "DEV"
    formatter = logging.Formatter(
        f'%(asctime)s %(name)s {logtag} %(filename)s [%(levelname)s] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    loop()


if __name__ == "__main__":
    main()