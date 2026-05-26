from datetime import datetime 
import juliandate as jd

def today(dt=datetime):
    return int(jd.from_gregorian(*list(dt.now().timetuple())[0:3]))

def to_ymd(julian_date):
    return datetime(*jd.to_gregorian(julian_date)).strftime('%Y-%m-%d')

class Reminder():
    def __init__(self, group_id, next, interval, message, id=None):
        self.id = id
        self.group_id = group_id
        self.next = next
        self.interval = interval
        self.message = message

    
class Reminders():
    def __init__(self, logger, bot, store):
        self.logger = logger
        self.bot = bot
        self.store = store
    
    async def process_queue(self):
        self.logger.info("poke")
        await self.bot.send("Mbj8dzEIFfw9OGvL9SVmzopOXyOzERCE/YfnZAKk7N0=", "lubdub")