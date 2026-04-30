import logging

from welcomebot import store
from welcomebot import cnc
from welcomebot import motd
from welcomebot import main

logger = logging.getLogger("smoke")
bot_store = store.BotStore(logger, db=":memory:")
cnc.CNCCommand(logger, [], "foo", bot_store)
motd.MotDCommand(logger, "foo", bot_store)
assert main.main