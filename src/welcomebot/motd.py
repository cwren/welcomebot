from signalbot import Command, Context, MessageType
from . import util

class MotDCommand(Command):
    def __init__(self, logger, cnc, store):
        self.logger = logger
        self.cnc = cnc
        self.store = store

    async def handle(self, context: Context) -> None:
        group_refresh_needed = not self.store.has_group(context.message.group)

        if context.message.group == self.cnc:
            self.logger.info("social is ignoring cnc message")
            return

        if context.message.group == None:
            self.logger.info("social rebuffing DM message")
            reply = "I only reply to messages in the group chats"
            await context.send(reply)
            return

        if context.message.type == MessageType.DATA_MESSAGE:
            self.logger.info("social processing data message")
            reply = f'I heard {context.message.text}'
            self.logger.debug("social sending response")
            await context.send(reply)
            return

        if context.message.type == MessageType.GROUP_UPDATE_MESSAGE:
            self.logger.info("social processing group update")
            group_refresh_needed = True

        if group_refresh_needed:
            await util.update_group(self.logger, self.bot, context, self.store)