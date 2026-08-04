from dotenv import load_dotenv
import json
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


async def remind(reminder) -> None:
    await reminder.process_queue()


async def welcome(welcomer) -> None:
    await welcomer.process_queue()


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
    instant_welcome = json.loads(os.environ.get('INSTANT_WELCOME', 'true'))

    bot_store = store.BotStore(logger,
                               db=config_directory / "bot_memory.db",
                               file_store=config_directory / "attachments")
    reminder = periodic.Reminders(logger, bot, bot_store)
    welcomer = motd.MotDCommand(logger, cnc_id, bot, bot_store, instant=instant_welcome)
    commander = cnc.CNCCommand(logger, managers, cnc_id, bot_store, reminder)

    bot.register(commander, groups=[cnc_id]) # monitor other groups
    bot.register(welcomer) # monitor other groups

    bot.scheduler.add_job(lubdub, trigger="interval", seconds=60, coalesce=True, max_instances=1)
    bot.scheduler.add_job(
        remind,
        args=[reminder],
        trigger='cron',
        hour=os.environ.get('REMINDER_TIMES', '13'), # once a day, US timezone friendly
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1)
    bot.scheduler.add_job(
        welcome,
        args=[welcomer],
        trigger='cron',
        hour=os.environ.get('WELCOME_TIMES', '*'), # once and hour on the hour
        minute=30,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1)

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