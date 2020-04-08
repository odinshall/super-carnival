import discord
from discord.ext import commands

from utils import checks


class Premium(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        description="Get some information about ModMail premium.", usage="premium", aliases=["donate", "patron"],
    )
    async def premium(self, ctx):
        embed = discord.Embed(
            title="Premium",
            description="Purchasing premium is the best way you can show support to us. As hosting this bot for "
            "all the servers and users costs much money, your few dollars donated will help us a lot "
            "in keeping the bot running. You will also get access to the premium features listed below.",
            colour=self.bot.primary_colour,
        )
        embed.add_field(
            name="Premium Features",
            value="- Priority support.\n- Custom message on new or closed ticket.\n"
            "- Advanced logging that includes chat history.\n- More features released in future.",
            inline=False,
        )
        embed.add_field(
            name="Get Premium",
            value="Please join our support server and type `donate` over there for more information.",
            inline=False,
        )
        await ctx.send(embed=embed)

    @checks.is_premium()
    @commands.command(description="Get the premium status of this server.", usage="premiumstatus")
    async def premiumstatus(self, ctx):
        c = self.bot.conn.cursor()
        c.execute("SELECT * FROM premium")
        res = c.fetchall()
        for row in res:
            if row[1] is None:
                continue
            premium_servers = row[1].split(",")
            if str(ctx.guild.id) in premium_servers:
                return await ctx.send(
                    embed=discord.Embed(
                        description=f"This server has premium. Offered by: <@{row[0]}>.",
                        colour=self.bot.primary_colour,
                    )
                )

    @checks.is_patron()
    @commands.command(
        description="Get a list of servers you assigned premium to.",
        usage="premiumlist",
        aliases=["premiumservers", "premiumguilds"],
    )
    async def premiumlist(self, ctx):
        c = self.bot.conn.cursor()
        c.execute("SELECT server FROM premium WHERE user=?", (ctx.author.id,))
        res = c.fetchone()
        if res is None:
            return
        if res[0] is None:
            return await ctx.send(
                embed=discord.Embed(
                    description="You did not assign premium to any server currently.", colour=self.bot.primary_colour,
                )
            )
        servers = res[0].split(",")
        to_send = ""
        for server in servers:
            if self.bot.get_guild(int(server)) is None:
                to_send += f"\nUnknown server `{server}`"
            else:
                to_send += f"\n{self.bot.get_guild(int(server)).name} `{server}`"
        await ctx.send(embed=discord.Embed(description=to_send, colour=self.bot.primary_colour))

    @checks.is_patron()
    @commands.command(description="Assign premium slot to a server.", usage="premiumassign <server ID>")
    async def premiumassign(self, ctx, *, guild: int):
        if self.bot.get_guild(guild) is None:
            return await ctx.send(
                embed=discord.Embed(description="The server ID you provided is invalid.", colour=self.bot.error_colour)
            )
        c = self.bot.conn.cursor()
        c.execute("SELECT server FROM premium")
        res = c.fetchall()
        all_premium = []
        for row in res:
            if row[0] is None:
                continue
            row = row[0].split(",")
            for server in row:
                all_premium.append(server)
        if str(guild) in all_premium:
            return await ctx.send(
                embed=discord.Embed(description="That server already has premium.", colour=self.bot.error_colour)
            )
        slots = self.bot.tools.get_premium_slots(self.bot, ctx.author.id)
        c.execute("SELECT server FROM premium WHERE user=?", (ctx.author.id,))
        servers = c.fetchone()
        assigned_slots = 0 if servers[0] is None else len(servers[0].split(","))
        if assigned_slots >= slots:
            return await ctx.send(
                embed=discord.Embed(
                    description="You have reached the maximum number of slots that can be assigned.",
                    colour=self.bot.error_colour,
                )
            )
        servers = [] if servers[0] is None else servers[0].split(",")
        servers.append(str(guild))
        c.execute(
            "UPDATE premium SET server=? WHERE user=?", (",".join(servers), ctx.author.id),
        )
        self.bot.conn.commit()
        await ctx.send(embed=discord.Embed(description="That server now has premium.", colour=self.bot.primary_colour))

    @checks.is_patron()
    @commands.command(description="Remove premium slot from a server.", usage="premiumremove <server ID>")
    async def premiumremove(self, ctx, *, guild: int):
        c = self.bot.conn.cursor()
        c.execute("SELECT server FROM premium WHERE user=?", (ctx.author.id,))
        res = c.fetchone()
        if res[0] is None or str(guild) not in res[0].split(","):
            return await ctx.send("You did not assign premium to that server.")
        servers = res[0].split(",")
        servers.remove(str(guild))
        if len(servers) == 0:
            servers = None
        else:
            servers = ",".join(servers)
        c.execute("UPDATE premium SET server=? WHERE user=?", (servers, ctx.author.id))
        c.execute("UPDATE data SET welcome=?, goodbye=?, loggingplus=? WHERE guild=?", (None, None, None, guild))
        self.bot.conn.commit()
        await ctx.send(
            embed=discord.Embed(description="That server no longer has premium.", colour=self.bot.primary_colour)
        )


def setup(bot):
    bot.add_cog(Premium(bot))
