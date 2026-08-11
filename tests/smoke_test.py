import logging
from pathlib import Path

from welcomebot import store
from welcomebot import cnc
from welcomebot import motd
from welcomebot import main
from welcomebot import periodic
from welcomebot import config

bot={}
logger = logging.getLogger("smoke")
my_config=config.Configuration(logger)
bot_store = store.BotStore(logger, db=":memory:", file_store= Path("/tmp") / "attachments")
reminders = periodic.Reminders(my_config, bot, bot_store)
cnc.CNCCommand(my_config, bot, bot_store, reminders)
motd.MotDCommand(my_config, bot, bot_store)
assert main.main