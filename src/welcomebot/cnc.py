from signalbot import Command, Context, MessageType

class CNCCommand(Command):
    def __init__(self, logger, managers, cnc, gm):
        self.logger = logger
        self.managers = managers
        self.cnc = cnc
        self.gm = gm

    async def handle(self, context: Context) -> None:
        if context.message.group != self.cnc:  # guard against DMs
            self.logger.info("cnc ignoring DM message")
            reply = "I only reply to messages in the CNC channel\n"
            await context.send(reply)
            return

        if context.message.type == MessageType.DATA_MESSAGE:
            self.logger.info("cnc processing data message")
            if context.message.source_uuid not in self.managers:
                reply = "I only reply to messages from a manager\n"
                await context.send(reply)
                return
            match(context.message.text.lower()):
                case 'help':
                    self.logger.info("cnc sending help message")
                    reply = """you can use these commands:
                    *list*: list groups"""
                    await context.send(reply)
                    return

                case 'list':
                    self.logger.info("cnc sending response")
                    groups = self.gm.list()
                    known_groups = self.bot._groups_by_internal_id.keys()
                    groups = [group for group in groups if group in known_groups]
                    group_names = [self.bot._groups_by_internal_id[group]["name"] for group in groups]
                    reply = 'known groups:\n'
                    reply += '\n'.join([ f'{name}' for name in group_names])
                    await context.send(reply)
                    return

            reply = """unknown command, type "help" for a list"""
            await context.send(reply)
            return
