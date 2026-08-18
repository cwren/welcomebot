import asyncio
from signalbot import DataMessageHandler, DataMessageContext, GroupUpdateHandler, GroupUpdateContext
from .message import Message
from .util import update_group

class MotDCommand(DataMessageHandler, GroupUpdateHandler):
    def __init__(self, config, bot, store):
        self.logger = config.logger
        self.cnc = config.welcome_cnc
        self.bot = bot
        self.store = store
        self.instant = config.instant_welcome

    async def handle_data_message(self, context: DataMessageContext) -> None:
        group = context.message.group_info.group_id if context.message.group_info else None

        if group == self.cnc:
            self.logger.info("social is ignoring cnc message")
            return
                
        if not group:
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
            mentions = [ m.number for m in context.message.mentions if m ]
            if self.bot.config.phone_number in mentions:
                self.logger.info("social responding to a mention in a group")
                reply = self.store.get_motd('TOS')
                if reply:
                    await reply.send(context)
                else:
                    self.logger.warning("social has no TOS to send")
                    reply = Message("I am a simple bot that posts a welcome message when people join.")
                    await reply.send(context)

    async def handle_group_update(self, context: GroupUpdateContext) -> None:
        self.logger.info("social processing group update")

        self.logger.info("social checking group membership")
        new_member = await update_group(self.logger, self.bot, context.message.group_info.group_id, self.store)
        if new_member:  
            if self.instant:
                motd = self.store.get_motd(context.message.group_info.group_id)
                if motd:
                    self.logger.info("sent the message of the day")
                    await motd.send(context)
                else:
                    self.logger.warning("no message of the day to send")
            else:
                self.store.schedule_welcome(context.message.group_info.group_id)

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
                promises.append(motd.send(self.bot.messages, group))
            else:
                self.logger.warning(f'no message of the day found for motd group {group}')
            self.store.remove_welcomes_for(group)
        return asyncio.gather(*promises)       
