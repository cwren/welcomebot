from signalbot import Command, Context, MessageType

class MotDCommand(Command):
    def __init__(self, logger, cnc, gm):
        self.logger = logger
        self.cnc = cnc
        self.gm = gm

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
            reply = f'saw a group update for {post_group["name"]}\n'
            prev_members = self.gm.get_members(context.message.group)
            if prev_members:
                for member in post_group["members"]:
                    self.logger.debug(f'  looking for {member} in old group')
                    if member not in prev_members:
                        self.logger.debug("  found a new member of the group")
                        reply += f'welcome: {member}\n'
                for member in prev_members:
                    self.logger.debug(f'  looking for {member} in new group')
                    if member not in post_group["members"]:
                        self.logger.debug("  a member left the group")
                        reply += f'goodbye: {member}\n'
            else:
                self.logger.debug("  found a new group")
                reply += f'this is a new group for me: hello all!\n'
            self.gm.put_members(context.message.group, post_group["members"])
            self.gm.retain_only(list(self.bot._groups_by_internal_id.keys()))
            self.logger.debug("social acknowledging group change")
            await context.send(reply)
            return