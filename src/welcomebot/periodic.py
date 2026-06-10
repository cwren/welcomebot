import asyncio
from datetime import datetime 
from functools import total_ordering
import juliandate as jd


class Calendar():
    def __init__(self, dt=datetime):
        self.dt = dt
    
    def today(self):
        return int(jd.from_gregorian(*list(self.dt.now().timetuple())[0:3], 12))

    def to_ymd(self, julian_date):
        return datetime(*jd.to_gregorian(julian_date)).strftime('%Y-%m-%d')

@total_ordering
class Reminder():
    DRAFT = -1

    def __init__(self, group_id, next, interval, message, id=DRAFT):
        self.id = id
        self.group_id = group_id
        self.next = next
        self.interval = interval
        self.message = message

    def _is_valid_operand(self, other):
        return isinstance(other, Reminder)
    
    def __eq__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        return ((self.id == other.id) and
                self.group_id == other.group_id and
                self.next == other.next and
                self.interval == other.interval and
                self.message == other.message
        )
    
    def repeating(self):
        return bool(self.interval)
    
    def __lt__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        return ((self.group_id,  self.repeating(),  self.next,  self.interval,  self.id,  str(self.message)) <
                (other.group_id, other.repeating(), other.next, other.interval, other.id, str(other.message)))

    
class Reminders():
    def __init__(self, logger, bot, store, cal=Calendar()):
        self.logger = logger
        self.bot = bot
        self.store = store
        self.cal = cal
    
    async def process_queue(self):
        self.logger.info('checking for reminders')
        reminders = self.store.get_due_reminders()
        reminders = sorted(reminders)
        recipients = set()
        promises = []
        for reminder in reminders:
            if reminder.group_id in recipients:
                self.logger.info(f'skipping reminder {reminder.id} in group {reminder.group_id}')
            else:
                self.logger.info(f'sending reminder {reminder.id} to group {reminder.group_id}')
                recipients.add(reminder.group_id)
                promises.append(self.bot.send(reminder.group_id, reminder.message))
                if reminder.interval:
                    today = self.cal.today()
                    next = today + reminder.interval - (today - reminder.next) % reminder.interval
                    self.store.repost_reminder(reminder.id, next)
                else:
                    self.store.delete_reminder(reminder.id)
        return asyncio.gather(*promises)       