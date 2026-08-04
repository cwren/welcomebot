import base64
import os
from pathlib import Path
import sqlite3

from .message import Attachment, Message
from .periodic import Calendar, Reminder

class BotStore():
    def __init__(self, logger, db="bot_memory.db", file_store=Path('/tmp'), cal=Calendar()):
        self.logger = logger
        self.cal = cal
        self.logger.info(f'store connecting to {db}')
        self.con = sqlite3.connect(db)
        self.file_store = file_store

        self.file_store.mkdir(parents=True, exist_ok=True)
        
        self.create_databsae()
        self.upgrade_databsae()


    def __del__(self):
        try:
            self.con.close()
        except:
            pass


    def create_databsae(self):
        cur = self.con.cursor()

        cur.execute("""   
             CREATE TABLE IF NOT EXISTS database_info AS
             SELECT "welcomebot" as name, 0 AS version;
        """)
        self.con.commit()
        
        cur.execute("""   
             CREATE TABLE IF NOT EXISTS group_members (
                group_id TEXT,
                member_id TEXT
             );
        """)
        self.con.commit()
        
        cur.execute("""   
             CREATE TABLE IF NOT EXISTS motd (
                group_id TEXT,
                motd TEXT
             );
        """)
        self.con.commit()
        
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

        cur.execute("""   
             CREATE TABLE IF NOT EXISTS attachment (
                message_id TEXT,
                filename TEXT
             );
        """)
        self.con.commit()
        
        cur.execute("""   
             CREATE TABLE IF NOT EXISTS welcomes (
                group_id TEXT
             );
        """)
        self.con.commit()

        cur.close()

    def upgrade_databsae(self):
        version = self.get_version()

        cur = self.con.cursor()

        if version == 0:
            self.logger.debug(f'upgrading data from {version} to 1')
            cur.execute('ALTER TABLE reminder ADD COLUMN num_attachments INTEGER DEFAULT 0;')
            cur.execute('ALTER TABLE motd ADD COLUMN num_attachments INTEGER DEFAULT 0;')
            cur.execute('UPDATE database_info SET version = 1 WHERE  name = "welcomebot";')
            version = 1;

        cur.close()


    def get_version(self):
        cur = self.con.cursor()
        res = cur.execute('SELECT version FROM database_info;')
        return res.fetchone()[0]
    
    #
    # attachments
    #

    def get_attachments(self, message_id):
        attachments = []
        cur = self.con.cursor()
        res = cur.execute('SELECT filename FROM attachment WHERE message_id = ?', (message_id, ))
        rows = res.fetchall()
        for filename in rows:
            try:
                with open(self.file_store / filename[0], "rb") as input:
                    attachments.append(Attachment(filename[0], base64.b64encode(input.read()).decode('utf-8')))
            except FileNotFoundError as e:
                self.logger.warning(f'failed to load image file: {e}')
        cur.close()
        return attachments


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
        res = cur.execute('SELECT motd, num_attachments FROM motd WHERE group_id = ?', (group, ))
        row = res.fetchone()
        if not row:
            return None
        text = row[0]
        num_attachments = row[1]
        cur.close()
        attachments = self.get_attachments(group) if num_attachments > 0 else []
        return Message(text, attachments)


    def put_motd(self, group, motd):
        cur = self.con.cursor()
        cur.execute('DELETE FROM motd WHERE group_id = ?', (group, ))
        self.cleanup_attachments(group)
        self.con.commit()
        cur.close()
        if motd:
            cur = self.con.cursor()
            cur.execute("INSERT INTO motd (group_id, motd, num_attachments) VALUES(?, ?, ?)", 
                        ( group, motd.text, len(motd.attachments)) )
            self.con.commit()
            for attachment in motd.attachments:
                with open(self.file_store / attachment.filename, "wb") as output:
                    output.write(base64.b64decode(attachment.data))
                cur.execute("INSERT INTO attachment (message_id, filename) VALUES(?, ?)", 
                            (group, attachment.filename))
                self.con.commit()
            cur.close()
            return motd
        return None

    def schedule_welcome(self, group):
        cur = self.con.cursor()
        cur.execute("INSERT INTO welcomes (group_id) VALUES(?)", ( group, ) )
        self.con.commit()
        cur.close()

    def get_outstanding_welcomes(self):
        cur = self.con.cursor()
        res = cur.execute("SELECT DISTINCT group_id FROM welcomes")
        rows = res.fetchall()
        groups = { row[0] for row in rows }
        cur.close()
        return groups

    def remove_welcomes_for(self, group):
        cur = self.con.cursor()
        cur.execute('DELETE FROM welcomes WHERE group_id = ?', (group, ))
        self.con.commit()
        cur.close()

    def get_motd_groups(self):
        cur = self.con.cursor()
        res = cur.execute('SELECT DISTINCT group_id FROM group_members INTERSECT SELECT DISTINCT group_id FROM motd')
        rows = res.fetchall()
        cur.close()
        return { row[0] for row in rows }

    #
    # reminders
    #

    def put_reminder(self, reminder: Reminder):
        cur = self.con.cursor()
        cur.execute("INSERT INTO reminder (group_id, next, interval, message, num_attachments) VALUES(?, ?, ?, ?, ?)", (
            reminder.group_id,
            reminder.next, 
            reminder.interval, 
            reminder.message.text,
            len(reminder.message.attachments),
        ) )
        reminder_id = cur.lastrowid
        self.con.commit()
        for attachment in reminder.message.attachments:
            with open(self.file_store / attachment.filename, "wb") as output:
                output.write(base64.b64decode(attachment.data))
            cur.execute("INSERT INTO attachment (message_id, filename) VALUES(?, ?)", 
                        (reminder_id, attachment.filename))
            self.con.commit()
        cur.close()
        return reminder_id

    def get_reminder(self, id):
        cur = self.con.cursor()
        res = cur.execute('SELECT id, group_id, next, interval, message, num_attachments FROM reminder WHERE id = ?', (id,))
        row = res.fetchone()
        if not row:
            return None
        reminder_id = row[0]
        group_id = row[1]
        next_day = row[2]
        interval = row[3]
        text = row[4]
        num_attachments = row[5]
        cur.close()
        attachments = self.get_attachments(reminder_id) if num_attachments > 0 else []
        return Reminder(group_id, next_day, interval, Message(text, attachments=attachments), id=reminder_id)

   
    def get_all_reminders(self):
        cur = self.con.cursor()
        res = cur.execute('SELECT id, group_id, next, interval, message, num_attachments FROM reminder')
        rows = res.fetchall()
        cur.close()
        reminders = [ Reminder(row[1], row[2], row[3], Message(row[4], has_attachments=(row[5]>0)), row[0]) for row in rows ]
        return reminders

    def get_due_reminders(self):
        cur = self.con.cursor()
        res = cur.execute('SELECT id, group_id, next, interval, message, num_attachments FROM reminder WHERE next <= ? ORDER BY 3 ASC', (self.cal.today(), ))
        rows = res.fetchall()
        cur.close()
        reminders = [ Reminder(row[1], row[2], row[3], Message(row[4], has_attachments=(row[5]>0)), row[0]) for row in rows ]
        return reminders

    def delete_reminder(self, id):
        cur = self.con.cursor()
        cur.execute('DELETE FROM reminder WHERE id = ?', (id, ))
        self.con.commit()
        cur.close()
        self.cleanup_attachments(id)
        return None

    def repost_reminder(self, id, next):
        cur = self.con.cursor()
        cur.execute('UPDATE reminder SET next = ? WHERE id = ?', (next, id))
        self.con.commit()
        cur.close()
        return next
    
    def cleanup_attachments(self, message_id):
        cur = self.con.cursor()
        res = cur.execute('SELECT filename FROM attachment WHERE message_id = ?', (message_id, ))
        rows = res.fetchall()
        for filename in rows:
            try:
                os.remove(self.file_store / filename[0])
            except FileNotFoundError as e:
                self.logger.warning(f'failed to remove image file: {e}')
        
        cur.execute('DELETE FROM attachment WHERE message_id = ?', (message_id, ))
        self.con.commit()
        cur.close()

