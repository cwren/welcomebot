import logging
from pathlib import Path

from welcomebot import store
from welcomebot import cnc
from welcomebot import motd
from welcomebot import main
from welcomebot import periodic

logger = logging.getLogger("smoke")
bot_store = store.BotStore(logger, db=":memory:", file_store= Path("/tmp") / "attachments")
reminders = periodic.Reminders(logger, [], bot_store)
cnc.CNCCommand(logger, [], "foo", bot_store, reminders)
motd.MotDCommand(logger, "foo", bot_store)
assert main.main