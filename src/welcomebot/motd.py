from signalbot import Command, Context, MessageType

class MotDCommand(Command):
    def __init__(self, logger, cnc, bs):
        self.logger = logger
        self.cnc = cnc
        self.bs = bs

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
            post_group = self.bot._groups_by_internal_id[context.message.group]
            prev_members = self.bs.get_members(context.message.group)
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
            self.bs.put_members(context.message.group, post_group["members"])
            self.bs.retain_only(list(self.bot._groups_by_internal_id.keys()))

            if new_member:
                motd = self.bs.get_motd(context.message.group)
                # TODO don't send too frequently
                if motd:
                    self.logger.info("sent the message of the day")
                    await context.send(motd)
                else:
                    self.logger.info("no message of the day to send")
            return
