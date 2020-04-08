import aiohttp
import sys
import traceback
import logging
import datetime
import sqlite3
from discord.ext import commands

import config
from utils import tools

conn = sqlite3.connect("data.sqlite")
log = logging.getLogger(__name__)


class ModMail(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.start_time = datetime.datetime.utcnow()
        self.session = aiohttp.ClientSession(loop=self.loop)

    @property
    def conn(self):
        return conn

    @property
    def uptime(self):
        return datetime.datetime.utcnow() - self.start_time

    @property
    def version(self):
        return config.__version__

    @property
    def config(self):
        return config

    @property
    def tools(self):
        return tools

    @property
    def primary_colour(self):
        return self.config.primary_colour

    @property
    def user_colour(self):
        return self.config.user_colour

    @property
    def mod_colour(self):
        return self.config.mod_colour

    @property
    def error_colour(self):
        return self.config.error_colour
    
    @property
    def colors(self):
        return self.config.colors

    def get_data(self, guild):
        c = self.conn.cursor()
        c.execute("SELECT * FROM data WHERE guild=?", (guild,))
        res = c.fetchone()
        if not res:
            c.execute(
                "INSERT INTO data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (guild, None, None, None, None, None, None, None, None, None, None),
            )
            self.conn.commit()
            return self.get_data(guild)
        else:
            return res

    all_prefix = {}
    all_category = []
    banned_guilds = []
    banned_users = []
    total_commands = 0
    total_messages = 0
    total_tickets = 0

    async def start_bot(self):
        c = self.conn.cursor()
        c.execute("SELECT guild, prefix, category FROM data")
        res = c.fetchall()
        for row in res:
            self.all_prefix[row[0]] = row[1]
            if row[2]:
                self.all_category.append(row[2])
        c.execute("SELECT id, type FROM banlist")
        res = c.fetchall()
        for row in res:
            if row[1] == "user":
                self.banned_users.append(row[0])
            elif row[1] == "guild":
                self.banned_guilds.append(row[0])
        c.execute("SELECT commands, messages, tickets FROM stats")
        res = c.fetchone()
        self.total_commands = res[0]
        self.total_messages = res[1]
        self.total_tickets = res[2]
        for extension in self.config.initial_extensions:
            try:
                self.load_extension(extension)
            except Exception:
                log.error(f"Failed to load extension {extension}.", file=sys.stderr)
                log.error(traceback.print_exc())
        await self.start(self.config.token)
