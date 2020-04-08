import io
import copy
import datetime
import discord
from discord.ext import commands

from utils import checks
from cogs.modmail_channel import ModMailEvents

import bcrypt


class Main(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Reply to the ticket anonymously.", usage="areply <message>")
    async def areply(self, ctx, *, message):
        modmail = ModMailEvents(self.bot)
        await modmail.send_mail_mod(ctx.message, ctx.prefix, True, message)

    async def close_channel(self, ctx, reason, anon: bool = False):
        try:
            await ctx.send(embed=discord.Embed(description="Closing channel...", colour=self.bot.primary_colour))
            data = self.bot.get_data(ctx.guild.id)
            ticketID = self.bot.tools.get_ticket_id(self.bot, ctx.channel)
            c = self.bot.conn.cursor()
            # "status" determines whether the ticket is open or closed, by being set to 1 or 0
            c.execute("SELECT status FROM tickets WHERE ticket=?", (ticketID,))
            isOpen = c.fetchone()[0]
            if isOpen == 1:
                isOpen = 0
                c.execute("UPDATE tickets SET status=? WHERE ticket=?", (isOpen, ticketID))
                self.bot.conn.commit()
            if data[7] == 1:
                messages = await ctx.channel.history(limit=10000).flatten()
            await ctx.channel.delete()
            embed = discord.Embed(
                title="Ticket Closed",
                description=(reason if reason else "No reason was provided."),
                colour=self.bot.error_colour,
                timestamp=datetime.datetime.utcnow(),
            )
            embed.set_author(
                name=f"{ctx.author.name}#{ctx.author.discriminator}" if anon is False else "staff#0000",
                icon_url=ctx.author.avatar_url if anon is False else "https://cdn.discordapp.com/embed/avatars/0.png",
            )
            embed.set_footer(text=f"{ctx.guild.name} | {ctx.guild.id}", icon_url=ctx.guild.icon_url)
            member = ctx.guild.get_member(await self.bot.tools.get_member_id(self.bot, ctx.channel))
            if member:
                try:
                    data = self.bot.get_data(ctx.guild.id)
                    if data[6]:
                        embed2 = discord.Embed(
                            title="Custom Close Message",
                            description=self.bot.tools.tag_format(data[6], member),
                            colour=self.bot.mod_colour,
                            timestamp=datetime.datetime.utcnow(),
                        )
                        embed2.set_footer(
                            text=f"{ctx.guild.name} | {ctx.guild.id}", icon_url=ctx.guild.icon_url,
                        )
                        await member.send(embed=embed2)
                    await member.send(embed=embed)
                except discord.Forbidden:
                    pass
            if data[4]:
                channel = ctx.guild.get_channel(data[4])
                if channel:
                    try:
                        if member is None:
                            member = await self.bot.fetch_user(self.bot.tools.get_member_id(self.bot, ctx.channel))
                        if member and not checks.is_ticket_anon(self.bot, ctx.channel):
                            embed.set_footer(
                                text=f"{member.name}#{member.discriminator} | {member.id}", icon_url=member.avatar_url,
                            )
                        else:
                            embed.set_footer(
                                text=f"member#0000 | 000000000000000000",
                                icon_url="https://cdn.discordapp.com/embed/avatars/0.png",
                            )
                        if data[7] == 1:
                            history = ""
                            for m in messages:
                                if (
                                    m.author.id != self.bot.user.id
                                    or len(m.embeds) <= 0
                                    or m.embeds[0].title not in ["Message Received", "Message Sent"]
                                ):
                                    continue
                                if hash(m.embeds[0].colour) == hash(self.bot.user_colour):
                                    author = f"{m.embeds[0].author.name} (User)"
                                elif hash(m.embeds[0].colour) == hash(self.bot.mod_colour):
                                    author = f"{m.embeds[0].author.name} (Staff)"
                                else:
                                    author = f"{m.embeds[0].author.name} (Unknown)"
                                description = m.embeds[0].description
                                for attachment in [
                                    field.value for field in m.embeds[0].fields if field.name.startswith("Attachment ")
                                ]:
                                    if not description:
                                        description = f"(Attachment: {attachment})"
                                    else:
                                        description = description + f" (Attachment: {attachment})"
                                history = (
                                    f"[{str(m.created_at.replace(microsecond=0))}] {author}: "
                                    f"{description}\n" + history
                                )
                            history = io.BytesIO(history.encode())
                            file = discord.File(
                                history, f"modmail_log_{self.bot.tools.get_ticket_id(self.bot, ctx.channel)}.txt"
                            )
                            return await channel.send(embed=embed, file=file)
                        await channel.send(embed=embed)
                    except discord.Forbidden:
                        pass
        except discord.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    description="Missing permissions to delete this channel.", colour=self.bot.error_colour,
                )
            )

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close the ticket.", usage="close [reason]")
    async def close(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason)

    @checks.is_modmail_channel()
    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close the ticket anonymously.", usage="aclose [reason]")
    async def aclose(self, ctx, *, reason: str = None):
        await self.close_channel(ctx, reason, True)

    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close all of the tickets.", usage="closeall [reason]")
    async def closeall(self, ctx, *, reason: str = None):
        category = self.bot.get_data(ctx.guild.id)[2]
        category = ctx.guild.get_channel(category)
        if category:
            for channel in category.text_channels:
                if checks.is_modmail_channel2(self.bot, channel):
                    msg = copy.copy(ctx.message)
                    msg.channel = channel
                    new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                    await self.close_channel(new_ctx, reason)
        try:
            await ctx.send(
                embed=discord.Embed(
                    description="All channels are successfully closed.", colour=self.bot.primary_colour,
                )
            )
        except discord.HTTPException:
            pass

    @checks.in_database()
    @checks.is_mod()
    @commands.bot_has_permissions(manage_channels=True)
    @commands.guild_only()
    @commands.command(description="Close all of the tickets anonymously.", usage="acloseall [reason]")
    async def acloseall(self, ctx, *, reason: str = None):
        category = self.bot.get_data(ctx.guild.id)[2]
        category = ctx.guild.get_channel(category)
        if category:
            for channel in category.text_channels:
                if checks.is_modmail_channel2(self.bot, channel):
                    msg = copy.copy(ctx.message)
                    msg.channel = channel
                    new_ctx = await self.bot.get_context(msg, cls=type(ctx))
                    await self.close_channel(new_ctx, reason, True)
        try:
            await ctx.send(
                embed=discord.Embed(
                    description="All channels are successfully closed anonymously.", colour=self.bot.primary_colour,
                )
            )
        except discord.HTTPException:
            pass

    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Blacklist a user from creating tickets.",
        usage="blacklist <member>",
        aliases=["block"],
    )
    async def blacklist(self, ctx, *, member: discord.Member):
        data = self.bot.get_data(ctx.guild.id)
        blacklist = data[9]
        if blacklist is None:
            blacklist = []
        else:
            blacklist = blacklist.split(",")
            
        if str(member.id) in blacklist:
            return await ctx.send(
                embed=discord.Embed(description="The user is already blacklisted.", colour=self.bot.error_colour)
            )
        blacklist.append(str(member.id))
        blacklist = ",".join(blacklist)
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET blacklist=? WHERE guild=?", (blacklist, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="The user is blacklisted successfully.", colour=self.bot.primary_colour)
        )
        
    ##############################################################################
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Blacklist an anonymous user from creating tickets using their ticket ID.",
        usage="anonBlacklist <ticket ID>",
        aliases=["anonBlock"],
    )
    async def anonBlacklist(self, ctx, *, ticketID: int):
        c = self.bot.conn.cursor()
        c.execute("SELECT user FROM tickets WHERE ticket=?", (ticketID,))
        user_id = c.fetchone()
        if not user_id or not user_id[0]:
            return await ctx.send(
                embed=discord.Embed(
                    description="Something went wrong... Double check ticket ID maybe?" ,colour=self.bot.error_colour)
                           )
        user_id = user_id[0]
        blacklist = self.bot.get_data(ctx.guild.id)[9]
        if blacklist is None:
            blacklist = []
        else:
            blacklist = blacklist.split(",")
        if user_id in blacklist:
            return await ctx.send(
                embed=discord.Embed(description="The user is already blacklisted.", colour=self.bot.error_colour)
            )
        blacklist.append(user_id)
        blacklist = ",".join(blacklist)
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET blacklist=? WHERE guild=?", (blacklist, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="The user is blacklisted successfully.", colour=self.bot.primary_colour)
        )
    ##############################################################################
    
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Remove a user from the blacklist.",
        usage="whitelist <member>",
        aliases=["unblock"],
    )
    async def whitelist(self, ctx, *, member: discord.Member):
        blacklist = self.bot.get_data(ctx.guild.id)[9]
        if blacklist is None:
            blacklist = []
        else:
            blacklist = blacklist.split(",")
            
        if str(member.id) not in blacklist:
            return await ctx.send(
                embed=discord.Embed(description="The user is not blacklisted.", colour=self.bot.error_colour)
            )
        blacklist.remove(str(member.id))
        if len(blacklist) == 0:
            blacklist = None
        else:
            blacklist = ",".join(blacklist)
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET blacklist=? WHERE guild=?", (blacklist, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="The user is whitelisted successfully.", colour=self.bot.primary_colour)
        )
    
    ##############################################################################
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(
        description="Remove a user from the blacklist using their ticket ID.",
        usage="anonWhitelist <ticket ID>",
        aliases=["anonUnblock"],
    )
    async def anonWhitelist(self, ctx, *, ticketID: int):
        c = self.bot.conn.cursor()
        c.execute("SELECT user FROM tickets WHERE ticket=?", (ticketID,))
        user_id = c.fetchone()
        if not user_id or not user_id[0]:
            return await ctx.send(
                embed=discord.Embed(
                    description="Something went wrong... Double check ticket ID maybe?" ,colour=self.bot.error_colour)
                           )
        user_id = user_id[0]
        blacklist = self.bot.get_data(ctx.guild.id)[9]
        if blacklist is None:
            blacklist = []
        else:
            blacklist = blacklist.split(",")
        if user_id not in blacklist:
            return await ctx.send(
                embed=discord.Embed(description="The user is not blacklisted.", colour=self.bot.error_colour)
            )
        blacklist.remove(user_id)
        blacklist = ",".join(blacklist)
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET blacklist=? WHERE guild=?", (blacklist, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="The user is whitelisted successfully.", colour=self.bot.primary_colour)
        )
    ##############################################################################
    
    ##############################################################################
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Remove all users from the blacklist.", usage="blacklistclear")
    async def blacklistclear(self, ctx):
        c = self.bot.conn.cursor()
        c.execute("UPDATE data SET blacklist=? WHERE guild=?", (None, ctx.guild.id))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="The blacklist is cleared successfully.", colour=self.bot.primary_colour)
        )
    ##############################################################################
    
    ##############################################################################       
    @checks.in_database()
    @checks.is_mod()
    @commands.guild_only()
    @commands.command(description="Get the status of anonymous messaging on this server.", usage="isanon")
    async def isanon(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                title="Anonymous Status",
                description=f"Anonymous messaging is turned {'on' if checks.is_guild_anon(self.bot, ctx.guild) == 1 else 'off'}.",
                colour=self.bot.primary_colour,
                )
            )
    ##############################################################################

def setup(bot):
    bot.add_cog(Main(bot))
