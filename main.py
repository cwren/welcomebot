import json
import logging
import os
from dotenv import load_dotenv
from signalbot import SignalBot, Config, Command, Context, MessageType, SQLiteConfig, enable_console_logging

done = False
cnc = ""
manager = ""
group_members = {}

class CNCCommand(Command):
    async def handle(self, context: Context) -> None:
        print("processing cnc message")
        if context.message.group != cnc:  # guard against DMs
            print("ignoring DM message")
            return
        if context.message.type == MessageType.DATA_MESSAGE:
            reply = ""
            if context.message.source_uuid == manager:
                reply += "hello manager\n"
            if context.message.group == cnc:
                reply += "we are in the cnc channel\n"
            reply += f'I heard {context.message.text}'
            await context.send(reply)
        if context.message.type == MessageType.GROUP_UPDATE_MESSAGE:
            group = self.bot._groups_by_internal_id[context.message.group]
            reply = f'saw a group update for {group["name"]}\n'
            if context.message.group in group_members:
                for member in group["members"]:
                    if member not in group_members[context.message.group]:
                        reply += f'welcome: {member}\n'
            group_members[context.message.group] = group["members"]
            await context.send(reply)

class SocialCommand(Command):
    async def handle(self, context: Context) -> None:
        reply = ""
        if context.message.group == cnc:
            print("ignoring cnc message")
            return
        if context.message.group == None:
            print("DM message")
            if context.message.source_uuid == manager:
                reply += "hello manager, this is not CNC\n"
            else:
                reply += "I am not allowed to talk to strangers"
            await context.send(reply)
            return
        if context.message.type == MessageType.DATA_MESSAGE:
            reply = ""
            if context.message.source_uuid == manager:
                reply += "hello manager\n"
            reply += f'I heard {context.message.text}'
            await context.send(reply)
            return
        if context.message.type == MessageType.GROUP_UPDATE_MESSAGE:
            group = self.bot._groups_by_internal_id[context.message.group]
            reply = f'saw a group update for {group["name"]}\n'
            if context.message.group in group_members:
                for member in group["members"]:
                    if member not in group_members[context.message.group]:
                        reply += f'welcome: {member}\n'
            group_members[context.message.group] = group["members"]
            await context.send(reply)
            return

def main():
    bot = SignalBot(
        Config(
            signal_service=os.environ["SIGNAL_SERVICE"],
            phone_number=os.environ["PHONE_NUMBER"],
            storage=SQLiteConfig(
                sqlite_db='state.sql',
            )
        )
    )
    bot.register(CNCCommand(), groups=[cnc]) # Run the command for all contacts and groups
    bot.register(SocialCommand()) # Run the command for all contacts and groups
    bot.start()

if __name__ == "__main__":
    enable_console_logging(logging.INFO)
    load_dotenv()
    cnc = os.environ["WELCOME_CNC"]
    manager = os.environ["WELCOME_MANAGER"]
    main()
