from dotenv import load_dotenv
import logging
import os
from pathlib import Path
import re
from signalbot import SignalBot, Config, SQLiteConfig, enable_console_logging

from . import cnc
from . import motd
from . import periodic
from . import store

logger = logging.getLogger("welcomebot")
config_directory = os.environ["HOME"] / Path('.local/share/welcomebot')
 
def lubdub() -> None:
    logger.info("heartbeat")


async def remind(reminders) -> None:
    await reminders.process_queue()


def loop():
    logger.debug("main init")
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
    reminders = periodic.Reminders(logger, bot, bot_store)
    bot.register(cnc.CNCCommand(logger, managers, cnc_id, bot_store), groups=[cnc_id]) # monitor other groups
    bot.register(motd.MotDCommand(logger, cnc_id, bot_store)) # monitor other groups
    bot.scheduler.add_job(lubdub, trigger="interval", seconds=60, coalesce=True, max_instances=1)
    bot.scheduler.add_job(remind, args=[reminders], trigger='cron', hour='13', coalesce=True, max_instances=1)

    logger.info("bot started")
    bot.start()


def main():
    # signalbot logs
    enable_console_logging(logging.WARNING)
    load_dotenv()

    # welcomebot logs
    
    logger.setLevel(os.environ.get('LOGLEVEL', 'INFO').upper())
    handler = logging.StreamHandler()
    logtag = os.environ.get('LOGTAG', 'DEV')
    formatter = logging.Formatter(
        f'%(asctime)s %(name)s {logtag} %(filename)s [%(levelname)s] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    loop()


if __name__ == "__main__":
    main()