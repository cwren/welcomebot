from signalbot import Command, Context, MessageType

class MotDCommand(Command):
    def __init__(self, logger, cnc, store):
        self.logger = logger
        self.cnc = cnc
        self.store = store

    async def handle(self, context: Context) -> None:
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
            post_group = self.bot.get_group(context.message.group)
            prev_members = self.store.get_members(context.message.group)
            new_member = False
            if prev_members:
                for member in post_group["members"]:
                    self.logger.debug(f'  looking for {member} in old group')
                    if member not in prev_members:
                        self.logger.debug("  found a new member of the group")
                        new_member = True
                for member in prev_members:
                    self.logger.debug(f'  looking for {member} in new group')
                    if member not in post_group["members"]:
                        self.logger.debug("  a member left the group")
            else:
                self.logger.debug("  found a new group")
                # TODO post TOC

            # update member cache
            self.store.put_members(context.message.group, post_group["members"])
            valid_group_ids = [ g["internal_id"] for g in self.bot.groups ]
            self.store.retain_only(valid_group_ids)

            if new_member:
                motd = self.store.get_motd(context.message.group)
                # TODO don't send too frequently
                if motd:
                    self.logger.info("sent the message of the day")
                    await context.send(motd)
                else:
                    self.logger.info("no message of the day to send")
            return
