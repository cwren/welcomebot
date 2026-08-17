from dotenv import load_dotenv
import logging
import os
from pathlib import Path
from signalbot import SignalBot, Config, SQLiteConfig

from . import cnc
from . import motd
from . import periodic
from . import store
from . import config

logger = logging.getLogger("welcomebot")
config_directory = os.environ["HOME"] / Path('.local/share/welcomebot')


def lubdub() -> None:
    logger.info("heartbeat")


async def remind(reminder) -> None:
    await reminder.process_queue()


async def welcome(welcomer) -> None:
    await welcomer.process_queue()


def loop(my_config):
    logger.debug("main init")
    bot = SignalBot(
        Config(
            signal_service=my_config.signal_service,
            phone_number=my_config.phone_number,
            storage=SQLiteConfig(
                db=config_directory / 'signalbot_internal_state.db',
            ),
        )
    )

    bot_store = store.BotStore(logger,
                               db=config_directory / "bot_memory.db",
                               file_store=config_directory / "attachments")
    reminder = periodic.Reminders(my_config, bot, bot_store)
    welcomer = motd.MotDCommand(my_config, bot, bot_store)
    commander = cnc.CNCCommand(my_config, bot_store, reminder)

    bot.register(commander, groups=[my_config.welcome_cnc]) # monitor other groups
    bot.register(welcomer) # monitor other groups

    bot.scheduler.add_job(lubdub, trigger="interval", seconds=60, coalesce=True, max_instances=1)
    bot.scheduler.add_job(
        remind,
        args=[reminder],
        trigger='cron',
        hour=my_config.reminder_times,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1)
    bot.scheduler.add_job(
        welcome,
        args=[welcomer],
        trigger='cron',
        hour=my_config.welcome_times,
        minute=30,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1)

    logger.info("bot started")
    bot.start()


def main():
    # signalbot logs
    my_config = config.Configuration(logger)
    # welcomebot logs
    
    logger.setLevel(my_config.log_level)
    handler = logging.StreamHandler()
    logtag = my_config.log_tag
    formatter = logging.Formatter(
        f'%(asctime)s %(name)s {logtag} %(filename)s [%(levelname)s] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    loop(my_config)


if __name__ == "__main__":
    load_dotenv()
    main()