
import sqlite3

from .message import Message
from .periodic import Calendar, Reminder

class BotStore():
    def __init__(self, logger, db="bot_memory.db", cal=Calendar()):
        self.logger = logger
        self.cal = cal
        self.logger.info(f'store connecting to {db}')
        self.con = sqlite3.connect(db)
        cur = self.con.cursor()
        cur.execute("""   
             CREATE TABLE IF NOT EXISTS group_members (
                group_id TEXT,
                member_id TEXT
             );
        """)
        self.con.commit()
        cur = self.con.cursor()
        cur.execute("""   
             CREATE TABLE IF NOT EXISTS motd (
                group_id TEXT,
                motd TEXT
             );
        """)
        self.con.commit()
        cur = self.con.cursor()
        cur.execute("""   
             CREATE TABLE IF NOT EXISTS reminder (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT,
                next INTEGER,
                interval INTEGER,
                message TEXT
             );
        """)
        self.con.commit()
        cur.close()


    def __del__(self):
        try:
            self.con.close()
        except:
            pass

    #
    # groups
    #

    def list_groups(self):
        cur = self.con.cursor()
        res = cur.execute('SELECT DISTINCT group_id FROM group_members')
        rows = res.fetchall()
        cur.close()
        return [ row[0] for row in rows ]

    def has_group(self, group):
        cur = self.con.cursor()
        res = cur.execute('SELECT group_id FROM group_members where group_id = ? LIMIT 1', (group, ))
        rows = res.fetchone()
        cur.close()
        return not not rows

    def retain_only(self, known_groups):
        # TODO also prune old groups
        saved_groups = self.list_groups()
        obsolete_groups = [ group for group in saved_groups if group not in known_groups]
        if obsolete_groups:
            self.logger.debug(f'dropping {len(obsolete_groups)} obsolete groups')
            cur = self.con.cursor()
            placeholders = ', '.join('?' for _ in obsolete_groups)
            cur.executemany(f'DELETE FROM group_members WHERE group_id = ({placeholders})', (obsolete_groups,))
            self.con.commit()
            cur.close()
        else:
            self.logger.debug('no obsolete groups to prune')
        return obsolete_groups


    #
    # members
    #

    def get_members(self, group):
        cur = self.con.cursor()
        res = cur.execute('SELECT member_id FROM group_members WHERE group_id = ?', (group, ))
        rows = res.fetchall()
        cur.close()
        return [ row[0] for row in rows ]

    def put_members(self, group, members):
        cur = self.con.cursor()
        cur.execute('DELETE FROM group_members WHERE group_id = ?', (group, ))
        self.con.commit()
        rows = [ (group, member) for member in members ]
        cur = self.con.cursor()
        cur.executemany("INSERT INTO group_members (group_id, member_id) VALUES(?, ?)", rows)
        self.con.commit()
        cur.close()

    #
    # motd
    #

    def get_motd(self, group):
        cur = self.con.cursor()
        res = cur.execute('SELECT motd FROM motd WHERE group_id = ?', (group, ))
        row = res.fetchone()
        cur.close()
        return Message(row[0]) if row else None

    def put_motd(self, group, motd):
        cur = self.con.cursor()
        cur.execute('DELETE FROM motd WHERE group_id = ?', (group, ))
        self.con.commit()
        if motd:
            cur = self.con.cursor()
            cur.execute("INSERT INTO motd (group_id, motd) VALUES(?, ?)", ( group, motd.text ) )
            self.con.commit()
            cur.close()
            return motd
        return None

    #
    # reminders
    #

    def put_reminder(self, reminder: Reminder):
        cur = self.con.cursor()
        cur.execute("INSERT INTO reminder (group_id, next, interval, message) VALUES(?, ?, ?, ?)", (
            reminder.group_id,
            reminder.next, 
            reminder.interval, 
            reminder.message.text
        ) )
        id = cur.lastrowid
        self.con.commit()
        cur.close()
        return id

    def get_reminder(self, id):
        cur = self.con.cursor()
        res = cur.execute('SELECT id, group_id, next, interval, message FROM reminder WHERE id = ?', (id,))
        row = res.fetchone()
        cur.close()
        return Reminder(row[1], row[2], row[3], Message(row[4]), id=row[0]) if row else None

    def get_all_reminders(self):
        cur = self.con.cursor()
        res = cur.execute('SELECT id, group_id, next, interval, message FROM reminder')
        rows = res.fetchall()
        cur.close()
        reminders = [ Reminder(row[1], row[2], row[3], Message(row[4]), row[0]) for row in rows ]
        return reminders

    def get_due_reminders(self):
        cur = self.con.cursor()
        res = cur.execute('SELECT id, group_id, next, interval, message FROM reminder WHERE next <= ? ORDER BY 3 ASC', (self.cal.today(), ))
        rows = res.fetchall()
        cur.close()
        reminders = [ Reminder(row[1], row[2], row[3], Message(row[4]), row[0]) for row in rows ]
        return reminders

    def delete_reminder(self, id):
        cur = self.con.cursor()
        cur.execute('DELETE FROM reminder WHERE id = ?', (id, ))
        self.con.commit()
        return None

    def repost_reminder(self, id, next):
        cur = self.con.cursor()
        cur.execute('UPDATE reminder SET next = ? WHERE id = ?', (next, id))
        self.con.commit()
        return next
