from dotenv import load_dotenv
import logging
import os
import re
from signalbot import SignalBot, Config, SQLiteConfig, enable_console_logging

from . import cnc
from . import motd
from . import store

logger = logging.getLogger("welcomebot")

def loop():
    bot = SignalBot(
        Config(
            signal_service=os.environ["SIGNAL_SERVICE"],
            phone_number=os.environ["PHONE_NUMBER"],
            storage=SQLiteConfig(
                sqlite_db='signalbot_internal_state.db',
            )
        )
    )

    cnc_id = os.environ["WELCOME_CNC"]
    managers = re.split(r'[\s|,:]+', os.environ["WELCOME_MANAGER"])

    bot_store = store.BotStore(logger)
    bot.register(cnc.CNCCommand(logger, managers, cnc_id, bot_store), groups=[cnc_id]) # monitor other groups
    bot.register(motd.MotDCommand(logger, cnc_id, bot_store)) # monitor other groups
    bot.start()
    logger.info("bot started")


def main():
    # signalbot logs
    enable_console_logging(logging.WARNING)

    # welcomebot logs
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(name)s %(filename)s [%(levelname)s] - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    load_dotenv()

    loop()


if __name__ == "__main__":
    main()