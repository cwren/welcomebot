import asyncio
from signalbot import Command, Context, MessageType
from .message import Message
from .util import update_group

class MotDCommand(Command):
    def __init__(self, config, bot, store):
        self.logger = config.logger
        self.cnc = config.welcome_cnc
        self.bot = bot
        self.store = store
        self.instant = config.instant_welcome

    async def handle(self, context: Context) -> None:
        group_refresh_needed = not self.store.has_group(context.message.group)

        if context.message.group == self.cnc:
            self.logger.info("social is ignoring cnc message")
            return

        elif context.message.type == MessageType.READ_MESSAGE:
            group_refresh_needed = False
                
        elif context.message.type == MessageType.DATA_MESSAGE:
            if not context.message.group:
                if context.message.text:
                    self.logger.info("social processing a DM message")
                    if self.bot.config.phone_number != context.message.source_number:
                        self.logger.info("social responding to a DM message")
                        reply = self.store.get_motd('TOS')
                        if not reply:
                            reply = Message("I only reply to messages in the group chats")
                            self.logger.warning("social has no TOS to send")
                        await reply.send(context)
            else:
                self.logger.info("social processing data message")
                mentions = [ m['number'] for m in context.message.mentions if m ]
                if self.bot.config.phone_number in mentions:
                    self.logger.info("social responding to a mention in a group")
                    reply = self.store.get_motd('TOS')
                    if reply:
                        await reply.send(context)
                    else:
                        self.logger.warning("social has no TOS to send")
                        reply = Message("I am a simple bot that posts a welcome message when people join.")
                        await reply.send(context)

        elif context.message.type == MessageType.GROUP_UPDATE_MESSAGE:
            self.logger.info("social processing group update")
            group_refresh_needed = True

        if group_refresh_needed:
            self.logger.info("social checking group membership")
            new_member = await update_group(self.logger, self.bot, context.message.group, self.store)
            
            if new_member:  
                if self.instant:
                    motd = self.store.get_motd(context.message.group)
                    if motd:
                        self.logger.info("sent the message of the day")
                        await motd.send(context)
                    else:
                        self.logger.warning("no message of the day to send")
                else:
                    self.store.schedule_welcome(context.message.group)

            return

    
    async def process_queue(self):
        self.logger.info('checking for delayed welcomes')
        welcomes = set(self.store.get_outstanding_welcomes())

        for group in self.store.get_motd_groups():
            if await update_group(self.logger, self.bot, group, self.store):
                welcomes.add(group)

        promises = []
        for group in welcomes:
            motd = self.store.get_motd(group)
            if motd:
                self.logger.info(f'sending delayed welcome to group {group}')
                promises.append(motd.send(self.bot, group))
            else:
                self.logger.warning(f'no message of the day found for motd group {group}')
            self.store.remove_welcomes_for(group)
        return asyncio.gather(*promises)       
