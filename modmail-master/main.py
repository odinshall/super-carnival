import asyncio
import logging
import sentry_sdk
from discord.ext import commands

import config
from classes.bot import ModMail
from utils.tools import get_guild_prefix

if config.testing is False:
    sentry_sdk.init(config.sentry_url)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


def _get_guild_prefix(bot2, message):
    prefix = get_guild_prefix(bot2, message)
    return commands.when_mentioned_or(prefix)(bot2, message)


bot = ModMail(
    fetch_offline_members=True,
    command_prefix=_get_guild_prefix,
    case_insensitive=True,
    description="The one and only public ModMail Discord bot.",
    help_command=None,
    owner_id=config.owner,
    heartbeat_timeout=300,
)

c = bot.conn.cursor()
c.execute(
    "CREATE TABLE IF NOT EXISTS data "
    "(guild bigint NOT NULL PRIMARY KEY, prefix text, category bigint, accessrole text, "
    "logging bigint, welcome text, goodbye text, loggingplus integer, pingrole text, blacklist text, anon integer)"
)
c.execute("CREATE TABLE IF NOT EXISTS premium (user bigint NOT NULL PRIMARY KEY, server text)")
c.execute("CREATE TABLE IF NOT EXISTS banlist (id bigint NOT NULL PRIMARY KEY, type text)")
c.execute("CREATE TABLE IF NOT EXISTS usersettings (user bigint NOT NULL PRIMARY KEY, confirmation int)")
c.execute("CREATE TABLE IF NOT EXISTS stats (commands int, messages int, tickets int)")
c.execute("INSERT INTO stats SELECT 0, 0, 0 WHERE NOT EXISTS (SELECT * FROM stats)")
################################
# not sure why the "guild id" was a primary key
# from my understanding of SQL, a "primary key" column cannot have the same value...
# ...in multiple rows. which defeats what we're trying to do here, because one guild...
# ...will have multiple tickets, and will exist in multiple rows with the same value.
# a better candidate for primary key is the ticket ID, because no ticket will ever have the same ID.
# also, "guild" shouldn't even be an integer...
# ...it should be a string. afaik that's the best way to store any IDs unless they increment
# doesn't matter much rn anyway tho
c.execute("CREATE TABLE IF NOT EXISTS tickets (guild BIGINT NOT NULL, ticket INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT, user TEXT, status INTEGER DEFAULT 1, is_anon INTEGER)")
###############################
bot.conn.commit()

@bot.event
async def on_message(_):
    pass


loop = asyncio.get_event_loop()
loop.run_until_complete(bot.start_bot())
