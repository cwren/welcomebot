import sqlite3

class BotStore():
    def __init__(self, logger, db="bot_memory.db"):
        self.logger = logger
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
        cur.close()

    def __del__(self):
        self.con.close()

    def list_groups(self):
        cur = self.con.cursor()
        res = cur.execute('SELECT DISTINCT group_id FROM group_members')
        rows = res.fetchall()
        cur.close()
        return [ row[0] for row in rows ]

    def retain_only(self, known_groups):
        # TODO also prune old groups
        saved_groups = self.list_groups()
        obsolete_groups = [ group for group in saved_groups if group not in known_groups]
        if obsolete_groups:
            self.logger.debug(f'dropping {len(obsolete_groups)} obsolete groups')
            cur = self.con.cursor()
            placeholders = ', '.join('?' for _ in obsolete_groups)
            cur.executemany(f'DELETE FROM group_members WHERE group_id = ({placeholders})', obsolete_groups)
            self.con.commit()
            cur.close()
        else:
            self.logger.debug('no obsolete groups to prune')
        return obsolete_groups

    def get_members(self, group):
        cur = self.con.cursor()
        res = cur.execute(f'SELECT member_id FROM group_members WHERE group_id = "{group}"')
        rows = res.fetchall()
        cur.close()
        return [ row[0] for row in rows ]

    def put_members(self, group, members):
        cur = self.con.cursor()
        cur.execute(f'DELETE FROM group_members WHERE group_id = "{group}"')
        self.con.commit()
        rows = [ (group, member) for member in members ]
        cur = self.con.cursor()
        cur.executemany("INSERT INTO group_members VALUES(?, ?)", rows)
        self.con.commit()
        cur.close()

    def get_motd(self, group):
        cur = self.con.cursor()
        res = cur.execute(f'SELECT motd FROM motd WHERE group_id = "{group}"')
        row = res.fetchone()
        cur.close()
        return row[0] if row else None

    def put_motd(self, group, motd):
        cur = self.con.cursor()
        cur.execute(f'DELETE FROM motd WHERE group_id = "{group}"')
        self.con.commit()
        if motd:
            cur = self.con.cursor()
            cur.executemany("INSERT INTO motd VALUES(?, ?)", [ ( group, motd ) ] )
            self.con.commit()
            cur.close()
            return motd
        return None
