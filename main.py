import logging
import os
from dotenv import load_dotenv
from signalbot import SignalBot, Config, Command, Context, MessageType, SQLiteConfig, enable_console_logging

group_members = {}
logger = logging.getLogger("welcomebot")

class CNCCommand(Command):
    def __init__(self, manager, cnc):
        self.manager = manager
        self.cnc = cnc

    async def handle(self, context: Context) -> None:
        if context.message.group != self.cnc:  # guard against DMs
            logger.info("cnc ignoring DM message")
            return

        if context.message.type == MessageType.DATA_MESSAGE:
            logger.info("cnc processing data message")
            reply = ""
            if context.message.source_uuid == self.manager:
                reply += "hello manager\n"
            if context.message.group == self.cnc:
                reply += "we are in the cnc channel\n"
            reply += f'I heard {context.message.text}'
            logger.debug("cnc sending response")
            await context.send(reply)

class SocialCommand(Command):
    def __init__(self, manager, cnc):
        self.manager = manager
        self.cnc = cnc

    async def handle(self, context: Context) -> None:
        if context.message.group == self.cnc:
            logger.info("social is ignoring cnc message")
            return

        if context.message.group == None:
            logger.info("social rebuffing DM message")
            reply = ""
            if context.message.source_uuid == self.manager:
                reply += "hello manager, this is not CNC\n"
            else:
                reply += "I am not allowed to talk to strangers"
            await context.send(reply)
            return

        if context.message.type == MessageType.DATA_MESSAGE:
            logger.info("social processing data message")
            reply = ""
            if context.message.source_uuid == self.manager:
                reply += "hello manager\n"
            reply += f'I heard {context.message.text}'
            logger.debug("social sending response")
            await context.send(reply)
            return

        if context.message.type == MessageType.GROUP_UPDATE_MESSAGE:
            logger.info("social processing group update")
            reply = ""
            group = self.bot._groups_by_internal_id[context.message.group]
            reply = f'saw a group update for {group["name"]}\n'
            if context.message.group in group_members:
                for member in group["members"]:
                    logger.debug(f'  looking for {member}')
                    if member not in group_members[context.message.group]:
                        logger.debug("  found a new member of the group")
                        reply += f'welcome: {member}\n'
            else:
                logger.debug("  found a new group")
            group_members[context.message.group] = group["members"]
            logger.debug("social acknowledging group change")
            await context.send(reply)
            return

def main():
    bot = SignalBot(
        Config(
            signal_service=os.environ["SIGNAL_SERVICE"],
            phone_number=os.environ["PHONE_NUMBER"],
            storage=SQLiteConfig(
                sqlite_db='signalbot_internal_state.sql',
            )
        )
    )

    cnc = os.environ["WELCOME_CNC"]
    manager = os.environ["WELCOME_MANAGER"]

    bot.register(CNCCommand(manager, cnc), groups=[cnc]) # monitor CNC group
    bot.register(SocialCommand(manager, cnc)) # monitor other groups
    bot.start()
    logger.info("bot started")

if __name__ == "__main__":
    # signalbot logs
    enable_console_logging(logging.WARNING)

    # welcomebot logs
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s %(name)s [%(levelname)s] - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    load_dotenv()

    main()
