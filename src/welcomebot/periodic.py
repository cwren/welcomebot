import asyncio
from datetime import datetime 
import juliandate as jd


class Calendar():
    def __init__(self, dt=datetime):
        self.dt = dt
    
    def today(self):
        return int(jd.from_gregorian(*list(self.dt.now().timetuple())[0:3], 12))

    def to_ymd(self, julian_date):
        return datetime(*jd.to_gregorian(julian_date)).strftime('%Y-%m-%d')


class Reminder():
    def __init__(self, group_id, next, interval, message, id=None):
        self.id = id
        self.group_id = group_id
        self.next = next
        self.interval = interval
        self.message = message

    def __eq__(self, other):
        if not isinstance(other, Reminder):
            return NotImplemented
        return ((self.id == other.id or not self.id or not other.id) and
                self.group_id == other.group_id and
                self.next == other.next and
                self.interval == other.interval and
                self.message == other.message
        )

    
class Reminders():
    def __init__(self, logger, bot, store, cal=Calendar()):
        self.logger = logger
        self.bot = bot
        self.store = store
        self.cal = cal
    
    async def process_queue(self):
        self.logger.info('checking for reminders')
        reminders = self.store.get_due_reminders()
        recipients = set()
        promises = []
        for reminder in reminders:
            if reminder.group_id in recipients:
                self.logger.info(f'skipping reminder {reminder.id} in group {reminder.group_id}')
            else:
                self.logger.info(f'sending reminder ß{reminder.id} to group {reminder.group_id}')
                recipients.add(reminder.group_id)
                promises.append(self.bot.send(reminder.group_id, reminder.message))
                if reminder.interval:
                    today = self.cal.today()
                    next = today + reminder.interval - (today - reminder.next) % reminder.interval
                    self.store.repost_reminder(reminder.id, next)
                else:
                    self.store.delete_reminder(reminder.id)
        return asyncio.gather(*promises)       