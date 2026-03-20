import re

from signalbot import Command, Context, MessageType

HELP_MESSAGE = """you can use these commands:
  list_groups: return known group names
  set_motd: set_motd group <newline> message"""

class CNCCommand(Command):
    def __init__(self, logger, managers, cnc, bs):
        self.logger = logger
        self.managers = managers
        self.cnc = cnc
        self.bs = bs

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
            match(context.message.text.split()[0].lower()):
                case 'help':
                    self.logger.info("cnc sending help message")
                    await context.send(HELP_MESSAGE)
                    return

                case 'list_groups':
                    self.logger.info("cnc processing list request")
                    groups = self.bs.list_groups()
                    known_groups = self.bot._groups_by_internal_id.keys()
                    groups = [group for group in groups if group in known_groups]
                    group_names = [self.bot._groups_by_internal_id[group]["name"] for group in groups]
                    reply = 'known groups:\n'
                    reply += '\n'.join([ f'{name}' for name in group_names])
                    await context.send(reply)
                    return

                case 'set_motd':
                    self.logger.info("cnc processing set_mod request")
                    ops = re.match(r'^set_motd ([A-Za-z0-9_+-]*={0,2})\n*(.*)$', # TODO validate this group re
                                   context.message.text, re.DOTALL)
                    group = ops[1]
                    motd = ops[2].strip()

                    if group not in self.bot._groups_by_name:
                        reply = f'unknown group {group}'
                        await context.send(reply)
                        return
                    
                    groups = self.bot._groups_by_name[group]
                    if len(groups) > 1:
                        reply = f'error: multiple groups with the name {group}:\n'
                        reply += '\n'.join([ f'{group["internal_id"]}' for group in groups])
                        await context.send(reply)
                        return

                    self.bs.put_motd(groups[0]["internal_id"], motd)
                    if motd:
                        reply = f'motd set for group {group}'
                    else:
                        reply = f'motd cleared for group {group}'
                    await context.send(reply)
                    return

            reply = """unknown command, type "help" for a list"""
            await context.send(reply)
            return
