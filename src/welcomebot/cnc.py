from importlib.metadata import version
import re

from signalbot import Command, Context, MessageType
from . import util

HELP_MESSAGE = """you can use these commands:
  list_groups: return enumerated known group names
  set_motd group <newline> message
  get_motd group
  set_tos <newline> message
  get_tos
  who: list members of cnc chat
  version: report the bot version number

  motd is the message posted in a specific group when a new member joins.

  tos is the message posted in response to DMs or mentions of the bot.
  """


class CNCCommand(Command):
    def __init__(self, logger, managers, cnc, store):
        self.logger = logger
        self.managers = managers
        self.cnc = cnc
        self.store = store

    def _get_group_info(self):
        group_info = [ { key: group[key] for key in ['name', 'internal_id'] } for group in self.bot.groups ]
        group_info = sorted(group_info, key=lambda x: x['name'])
        for i, info in enumerate(group_info):
            info['tag'] = i
        return group_info
                             
    async def handle(self, context: Context) -> None:
        if context.message.group != self.cnc:  # guard against DMs
            self.logger.info("cnc ignoring message not in the CNC group chat")
            return
        
        if not self.store.has_group(context.message.group):
            await util.update_group(self.logger, self.bot, context, self.store)

        if context.message.type == MessageType.DATA_MESSAGE:
            self.logger.info("cnc processing data message")
            if context.message.source_uuid not in self.managers:
                self.logger.info("cnc ignoring message not in the CNC group chat")
                return
            
            parts = context.message.text.split('\n', maxsplit=1)
            ops = parts[0].split(maxsplit=2)
            
            match(ops[0].lower()):
                case 'help':
                    self.logger.info("cnc sending help message")
                    await context.send(HELP_MESSAGE)
                    return

                case 'list_groups':
                    self.logger.info("cnc processing list request")
                    group_info = self._get_group_info()
                    reply = 'known groups:\n'
                    reply += '\n'.join([ f'{group['tag']}: {group["name"]}' for group in group_info ])
                    await context.send(reply)
                    return

                case 'set_motd':
                    self.logger.info("cnc processing set_mod request")
                    if len(ops) < 2:
                        reply = 'unrecognized set_motd syntax'
                        await context.send(reply)
                        return

                    group_info = self._get_group_info()                    
                    group_tag = ops[1]

                    motd = parts[1] if len(parts) == 2 else None

                    try: 
                        group_tag = int(group_tag)
                    except ValueError:
                        reply = f'invalid group index: {group_tag}'
                        await context.send(reply)
                        return

                    if group_tag > len(group_info):
                        reply = f'group index out of range: {group_tag}'
                        await context.send(reply)
                        return

                    group = group_info[group_tag]
                    self.store.put_motd(group['internal_id'], motd)
                    if motd:
                        reply = f'motd set for group {group_tag} ({group['name']})'
                    else:
                        reply = f'motd cleared for group {group_tag} ({group['name']}'
                    await context.send(reply)
                    return

                case 'get_motd':
                    self.logger.info("cnc processing get_mod request")
                    if len(ops) < 2:
                        reply = 'unrecognized get_motd syntax'
                        await context.send(reply)
                        return
                    
                    group_info = self._get_group_info()                   
                    group_tag = ops[1]

                    try: 
                        group_tag = int(group_tag)
                    except ValueError:
                        reply = f'invalid group index: {group_tag}'
                        await context.send(reply)
                        return

                    if group_tag >= len(group_info):
                        reply = f'group index out of range: {group_tag}'
                        await context.send(reply)
                        return
                    
                    group = group_info[group_tag]
                    motd = self.store.get_motd(group['internal_id'])
                    if motd:
                        reply = f'motd for group {group_tag} ({group['name']}) is: \n{motd}'
                    else:
                        reply = f'there is no motd for group {group_tag} ({group['name']})'
                    await context.send(reply)
                    return

                case 'set_tos':
                    self.logger.info("cnc processing set_tos request")
                    if len(ops) < 1:
                        reply = 'unrecognized set_tos syntax'
                        await context.send(reply)
                        return

                    tos = parts[1] if len(parts) == 2 else None

                    self.store.put_motd('TOS', tos)
                    if tos:
                        reply = 'tos set'
                    else:
                        reply = 'tos cleared'
                    await context.send(reply)
                    return

                case 'get_tos':
                    self.logger.info("cnc processing get_tos request")

                    tos = self.store.get_motd('TOS')
                    if tos:
                        reply = f'tos is: \n{tos}'
                    else:
                        reply = 'there is no tos for this bot'
                    await context.send(reply)
                    return

                case 'who':
                    self.logger.info("cnc processing who request")
                    members = self.bot.get_group(context.message.group)['members']
                    reply = 'who is in this chat:\n'
                    reply += '\n'.join([ f'{m}' for m in members ])
                    await context.send(reply)
                    return

                case 'version':
                    self.logger.info("cnc processing version request")
                    reply = f'I am running welcomebot {version('welcomebot')}'
                    await context.send(reply)
                    return

            reply = """unknown command, type "help" for a list"""
            await context.send(reply)
            return
