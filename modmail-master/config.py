import bcrypt

# Bot's token
token = "NDk3NDQ2NDY1NzIzOTU3MjU4.Xo2Zwg.1xEeKSFhagqtY-UpxPzAj_8ZW04"

# DiscordBotList token
dbl_token = ""

# Discord Bots token
dbots_token = ""

# Bots on Discord token
bod_token = ""

# Bots for Discord token
bfd_token = ""

# Discord Boats token
dboats_token = ""

# Sentry URL
sentry_url = ""

# Whether the bot is for testing, if true, stats and errors will not be posted
testing = False

# The default prefix for commands
default_prefix = "="

# Status of the bot
activity = [
    f"DM to ANONYMOUSLY Contact Staff | {default_prefix}help",
]

# The main bot owner
owner = 258948386353446922

# Bot owners that have access to owner commands
owners = [
    258948386353446922
]

# Bot admins that have access to admin commands
admins = [
]

# Cogs to load on startup
initial_extensions = [
    "cogs.admin",
    "cogs.configuration",
    "cogs.direct_message",
    "cogs.error_handler",
    "cogs.events",
    "cogs.general",
    "cogs.main",
    "cogs.miscellaneous",
    "cogs.modmail_channel",
    "cogs.owner",
    "cogs.premium",
]

# Channels to send logs
join_channel = 611647931484864550
event_channel = 611647931484864550
admin_channel = 611647931484864550

# This is where patron roles are at
main_server = 593201641919086602

# Patron roles for premium servers
premium1 = 000000000000000000
premium3 = 000000000000000000
premium5 = 000000000000000000

# IMPROVED Embed & avatar colors
class Color():
    def __init__(self, name, avatar_url, hex_code):
        self.name = name
        self.avatar_url = avatar_url
        self.hex_code = hex_code

blurple = Color('blurple', 'https://cdn.discordapp.com/embed/avatars/0.png', 0x7289da)
grey = Color('grey', 'https://cdn.discordapp.com/embed/avatars/1.png', 0x747f8d)
green = Color('green', 'https://cdn.discordapp.com/embed/avatars/2.png', 0x43b581)
orange = Color('orange', 'https://cdn.discordapp.com/embed/avatars/3.png', 0xfaa61a)
red = Color('red', 'https://cdn.discordapp.com/embed/avatars/4.png', 0xf04747)

colors = [
    blurple, grey, green, orange, red
]

# The colour used in embeds
primary_colour = 0x1E90FF
user_colour = 0x00FF00
mod_colour = 0xFF4500
# mod_colour = colors[colors.index(blurple)]
error_colour = 0xFF0000

# Version of bot
__version__ = "1.4.0"

# Used for hashing user information with Bcrypt
salt = bcrypt.gensalt(rounds=10)