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

        elif context.message.group == None:
            self.logger.info("social processing a DM message")
            if self.bot.config.phone_number != context.message.source_number:
                self.logger.info("social responding to a DM message")
                reply = self.store.get_motd('TOS')
                if not reply:
                    reply = "I only reply to messages in the group chats"
                    self.logger.warning("social has no TOS to send")
                await context.send(reply)

        elif context.message.type == MessageType.DATA_MESSAGE:
            self.logger.info("social processing data message")
            mentions = [ m['number'] for m in context.message.mentions if m ]
            if self.bot.config.phone_number in mentions:
                self.logger.info("social responding to a mention in a group")
                reply = self.store.get_motd('TOS')
                if not reply:
                    reply = "I only reply to messages in the group chats"
                    self.logger.warning("social has no TOS to send")
                await context.send(reply)

        elif context.message.type == MessageType.GROUP_UPDATE_MESSAGE:
            self.logger.info("social processing group update")
            group_refresh_needed = True

        if group_refresh_needed:
            self.logger.info("social checking group membership")
            new_member = await util.update_group(self.logger, self.bot, context, self.store)
            
            if new_member:  
                motd = self.store.get_motd(context.message.group)
                # TODO don't send too frequently
                if motd:
                    self.logger.info("sent the message of the day")
                    await context.send(motd)
                else:
                    self.logger.warning("no message of the day to send")
            return
