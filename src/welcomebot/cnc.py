from importlib.metadata import version
import hashlib

from signalbot import Command, Context, MessageType
from .util import update_group
from .periodic import to_ymd, today, Reminder

HELP_MESSAGE = """you can use these commands:
  list_groups: return enumerated known group names
  set_motd GROUP <newline> message
  get_motd GROUP
  set_tos <newline> message
  get_tos
  list_reminders
  set_reminder GROUP periodicity <newline> message
  get_reminder REMINDER_ID
  delete_reminder REMINDER_ID
  who: list members of cnc chat
  get_group_id GROUP: get the internal Signal ID of a group
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
        for group in group_info:
            group['tag'] = hashlib.sha256(group['internal_id'].encode()).hexdigest()[0:5].upper()
        group_info = { group['tag'] : group for group in group_info }
        return group_info
    
    def _get_group_lookup(self):
        group_info = self._get_group_info()
        return { group['internal_id'] : group for _, group in group_info.items() }
                             
    async def handle(self, context: Context) -> None:
        if context.message.group != self.cnc:  # guard against DMs
            self.logger.info("cnc ignoring message not in the CNC group chat")
            return
        
        if not self.store.has_group(context.message.group):
            await update_group(self.logger, self.bot, context, self.store)

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
                    reply += '\n'.join([ f'{tag}: {group_info[tag]['name']}' for tag in group_info.keys() ])
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

                    if group_tag not in group_info:
                        reply = f'invalid group index: {group_tag}'
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

                    if group_tag not in group_info:
                        reply = f'invalid group index: {group_tag}'
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

                case 'get_group_id':
                    self.logger.info("cnc processing get_group_id request")
                    if len(ops) < 2:
                        reply = 'unrecognized get_group_id syntax'
                        await context.send(reply)
                        return
                    
                    group_info = self._get_group_info()                   
                    group_tag = ops[1]

                    if group_tag not in group_info:
                        reply = f'invalid group index: {group_tag}'
                        await context.send(reply)
                        return
                    
                    group = group_info[group_tag]
                    reply = f'id for group {group['name']} is: {group['internal_id']}'
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

                case 'list_reminders':
                    self.logger.info("cnc processing list_reminders request")

                    reminders = self.store.get_all_reminders()
                    if reminders:
                        gl = self._get_group_lookup()
                        reply = 'reminders:\n'
                        reply += '\n'.join(
                            [ f'ID {r.id}: \n\tgroup: {gl[r.group_id]['name']}\n\tnext post: {to_ymd(r.next)}\n\tevery {r.interval}d' for r in reminders ]
                        )
                    else:
                        reply = 'there are no reminders'
                    await context.send(reply)
                    return
                
                case 'set_reminder':
                    self.logger.info("cnc processing set_reminder request") 
                    # set_reminder GROUP periodicity <newline> message
                    if len(ops) < 3:
                        reply = 'unrecognized set_reminder syntax'
                        await context.send(reply)
                        return
                    
                    group_info = self._get_group_info()                   
                    group_tag = ops[1]

                    if group_tag not in group_info:
                        reply = f'invalid group index: {group_tag}'
                        await context.send(reply)
                        return
                    
                    group = group_info[group_tag]
                    id = self.store.put_reminder(Reminder(group['internal_id'], today(), ops[2], parts[1]))
                    if id:
                        reply = f'reminder set: {id}'
                    else:
                        reply = 'fail!'
                    await context.send(reply)
                    return
                
                case 'get_reminder':
                    self.logger.info("cnc processing get_reminder request")
                    if len(ops) < 2:
                        reply = 'unrecognized get_reminder syntax'
                        await context.send(reply)
                        return
                    id = None
                    try:
                        id = int(ops[1])
                    except (ValueError, TypeError):
                        reply = f'get_reminder takes an integer index: {ops[1]}'
                        await context.send(reply)
                        return
                    reminders = self.store.get_all_reminders()
                    reminders = [ reminder for reminder in reminders if reminder.id == id ]
                    if reminders:
                        reply = '\n'.join(
                            [ f'ID {r.id}:\n{r.message}' for r in reminders ]
                        )
                    else:
                        reply = f'could not find reminder {id}'
                    await context.send(reply)
                    return
                
                case 'delete_reminder':
                    self.logger.info("cnc processing delete_reminder request")
                    if len(ops) < 2:
                        reply = 'unrecognized delete_reminder syntax'
                        await context.send(reply)
                        return
                    id = None
                    try:
                        id = int(ops[1])
                    except (ValueError, TypeError):
                        reply = f'delete_reminder takes an integer index: {ops[1]}'
                        await context.send(reply)
                        return
                    reminders = self.store.delete_reminder(id)
                    reply = f'deleted reminder {id}'
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


            self.logger.info("cnc received an unknown command in the CNC group chat")
            reply = """unknown command, type "help" for a list"""
            await context.send(reply)
            return
