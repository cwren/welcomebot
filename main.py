from dotenv import load_dotenv
import logging
import os
from signalbot import SignalBot, Config, Command, Context, MessageType, SQLiteConfig, enable_console_logging
import sqlite3

logger = logging.getLogger("welcomebot")

class GroupMembers():
    def __init__(self):
        self.con = sqlite3.connect("group_members.db")
        cur = self.con.cursor()
        cur.execute("""   
             CREATE TABLE IF NOT EXISTS group_members (
                 group_id TEXT,
                 member_id TEXT
             );
        """)
        self.con.commit()
        cur.close()

    def __del__(self):
        self.con.close()

    def get(self, group):
        cur = self.con.cursor()
        res = cur.execute(f'SELECT * FROM group_members WHERE group_id = "{group}"')
        rows = res.fetchall()
        cur.close()
        return [ row[1] for row in rows ]

    def put(self, group, members):
        cur = self.con.cursor()
        cur.execute(f'DELETE FROM group_members WHERE group_id = "{group}"')
        self.con.commit()
        rows = [ (group, member) for member in members ]
        cur = self.con.cursor()
        cur.executemany("INSERT INTO group_members VALUES(?, ?)", rows)
        self.con.commit()
        cur.close()


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
    def __init__(self, manager, cnc, gm):
        self.manager = manager
        self.cnc = cnc
        self.gm = gm

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
            post_group = self.bot._groups_by_internal_id[context.message.group]
            reply = f'saw a group update for {post_group["name"]}\n'
            prev_members = self.gm.get(context.message.group)
            if prev_members:
                for member in post_group["members"]:
                    logger.debug(f'  looking for {member} in old group')
                    if member not in prev_members:
                        logger.debug("  found a new member of the group")
                        reply += f'welcome: {member}\n'
                for member in prev_members:
                    logger.debug(f'  looking for {member} in new group')
                    if member not in post_group["members"]:
                        logger.debug("  a member left the group")
                        reply += f'goodbye: {member}\n'
            else:
                logger.debug("  found a new group")
                reply += f'this is a new group for me: hello all!\n'
            self.gm.put(context.message.group, post_group["members"])
            logger.debug("social acknowledging group change")
            await context.send(reply)
            return

def main():
    gm = GroupMembers()
    bot = SignalBot(
        Config(
            signal_service=os.environ["SIGNAL_SERVICE"],
            phone_number=os.environ["PHONE_NUMBER"],
            storage=SQLiteConfig(
                sqlite_db='signalbot_internal_state.db',
            )
        )
    )

    cnc = os.environ["WELCOME_CNC"]
    manager = os.environ["WELCOME_MANAGER"]

    bot.register(CNCCommand(manager, cnc), groups=[cnc]) # monitor CNC group
    bot.register(SocialCommand(manager, cnc, gm)) # monitor other groups
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
