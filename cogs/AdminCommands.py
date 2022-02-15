from discord.ext import commands
from discord.ext.commands import has_permissions
import cogs.colourEmbed as functions
import traceback
import sys
import discord
from Database import Database
from cogs.BalanceHandler import Player, Guild
import json

def dmyConverter(seconds):
    secondsInDays = 60 * 60 * 24
    secondsInHours = 60 * 60
    secondsInMinutes = 60

    days = seconds // secondsInDays
    hours = (seconds - (days * secondsInDays)) // secondsInHours
    minutes = ((seconds - (days * secondsInDays)) - (hours * secondsInHours)) // secondsInMinutes
    remainingSeconds = seconds - (days * secondsInDays) - (hours * secondsInHours) - (
            minutes * secondsInMinutes)

    timeStatement = ""

    if days != 0:
        timeStatement += f"{round(days)} days,"
    if hours != 0:
        timeStatement += f" {round(hours)} hours,"
    if minutes != 0:
        timeStatement += f" {round(minutes)} minutes,"
    if remainingSeconds != 0:
        timeStatement += f" {round(remainingSeconds)} seconds"
    if timeStatement[-1] == ",":
        timeStatement = timeStatement[:-1]

    return timeStatement


class AdminCommands(commands.Cog, name="🛠️ Admin Commands"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Checks the server's current settings.",
                      description=f"checkserversettings**\n\nChecks the server's current settings. Administrator Only.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def checkserversettings(self, ctx):

        guild_object = Guild(ctx.guild.id)
        guild_object.get_all_or_nothing_win_odds()
        guild_object.get_coin_flip_win_odds()
        guild_object.get_profit()

        description = f"The current payout for win is **{(guild_object.victory_profit * 100):,.2f}%**.\n"
        description += f"The current coin flip win rate is **{', '.join([f'{i * 100:,.2f}%' for i in guild_object.coin_flip_win_odds])}** in descending order.\n"
        description += f"The current all-or-nothing win rate is **{', '.join([f'{i * 100:,.2f}%' for i in guild_object.all_or_nothing_win_odds])}** in descending order.\n"
        embed = discord.Embed(description=description)
        await ctx.send(embed=embed)

    @commands.command(brief="Sets the victory profit in decimal (E.g. 100% = 1)",
                      description=f"setvictoryprofit [0-1]**\n\nSets the victory profit in decimal (E.g. 100% = 1). Administrator Only.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def setvictoryprofit(self, ctx, amount: float):

        Database.execute('UPDATE guildProfile SET victoryProfit = ? WHERE guildID = ? ', amount, ctx.guild.id)

        embed = discord.Embed(title="Update Successful",
                              description=f"Successfully set the victory profit to **{amount * 100:,.2f}%**",
                              colour=functions.embedColour(ctx.guild.id))
        await ctx.send(embed=embed)

    # @commands.command(brief="Sets the special winning odds in decimal (E.g. 50% = 0.5)",
    #                   description=f"setspecialodds [0-1]**\n\nSets the special winning odds in decimal (E.g. 50% = 0.5). Administrator Only.")
    # @commands.cooldown(1, 5, commands.BucketType.user)
    # @has_permissions(administrator=True)
    # async def setspecialodds(self, ctx, amount: float):
    #
    #     Database.execute('UPDATE guildProfile SET coinFlipSpecial = ? WHERE guildID = ? ', amount, ctx.guild.id)
    #
    #     embed = discord.Embed(title="Update Successful",
    #                           description=f"Successfully set the special win rate to **{amount * 100:,.2f}%**",
    #                           colour=functions.embedColour(ctx.guild.id))
    #     await ctx.send(embed=embed)

    @commands.command(brief="Sets the winning odds in decimal (E.g. 50% = 0.5)",
                      description=f"setwinodds [Odd #1] [Odd #2] [Odd #3] [Odd #4]**\n\n"
                                  f"Sets the winning odds in decimal (E.g. 50% = 0.5). Administrator Only.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def setwinodds(self, ctx, amount1: float, amount2: float, amount3: float, amount4: float):

        odds_list = [amount1, amount2, amount3, amount4]
        new_lst = json.dumps(odds_list)
        Database.execute('UPDATE guildProfile SET coinFlipWin = ? WHERE guildID = ? ', new_lst, ctx.guild.id)

        embed = discord.Embed(title="Update Successful",
                              description=f"Successfully set the win rate to {', '.join([f'{i * 100:,.2f}%' for i in odds_list])}",
                              colour=functions.embedColour(ctx.guild.id))
        await ctx.send(embed=embed)

    @commands.command(brief="Sets the all-or-nothing winning odds in decimal (E.g. 50% = 0.5)",
                      description=f"setwinodds [Odd #1] [Odd #2] [Odd #3]**\n\n"
                                  f"Sets the all-or-nothing winning odds in decimal (E.g. 50% = 0.5). Administrator Only.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def setallornothingodds(self, ctx, amount1: float, amount2: float, amount3: float):

        odds_list = [amount1, amount2, amount3]
        new_lst = json.dumps(odds_list)
        Database.execute('UPDATE guildProfile SET allOrNothingWin = ? WHERE guildID = ? ', new_lst, ctx.guild.id)

        embed = discord.Embed(title="Update Successful",
                              description=f"Successfully set the all-or-nothing win rate to **{', '.join([f'{i * 100:,.2f}%' for i in odds_list])}**",
                              colour=functions.embedColour(ctx.guild.id))
        await ctx.send(embed=embed)

    @commands.command(brief="Admin Command to add bought credit to a user. Administrator Only.",
                      description=f"addboughtcredit [@User] [Amount]**\n\nAdmin Command to add bought credit to a user. Administrator Only.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def addboughtcredit(self, ctx, user: discord.Member, amount: float):

        player_object = Player(user.id)
        new_balance = player_object.bought_credit_transaction(amount)

        if new_balance is None:
            return await functions.errorEmbedTemplate(ctx, f"The user does not have an account created.", ctx.author)

        embed = discord.Embed(title="Credit Successful",
                              description=f"{user.mention} has been credited with **{amount:,} Bought Tokens** and"
                                          f" now has **{new_balance:,} Bought Tokens**.", colour=functions.embedColour(ctx.guild.id))
        await ctx.send(embed=embed)

    @commands.command(brief="Admin Command to add won credit to a user. Administrator Only.",
                      description=f"addwoncredit [@User] [Amount]**\n\nAdmin Command to add won credit to a user. Administrator Only.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def addwoncredit(self, ctx, user: discord.Member, amount: float):

        player_object = Player(user.id)
        new_balance = player_object.won_credit_transaction(amount)

        if new_balance is None:
            return await functions.errorEmbedTemplate(ctx, f"The user does not have an account created.", ctx.author)

        embed = discord.Embed(title="Credit Successful",
                              description=f"{user.mention} has been credited with **{amount:,} Won Tokens** and"
                                          f" now has **{new_balance:,} Won Tokens**.", colour=functions.embedColour(ctx.guild.id))
        await ctx.send(embed=embed)

    @commands.command(brief="Changes the colour of the embed. Administrator Only.",
                      description=f"embedsettings [Colour Code e.g. 0xffff0]**\n\nChanges the colour of the embed. Administrator Only.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @has_permissions(administrator=True)
    async def embedsettings(self, ctx, colour: str):

        try:
            colourCode = int(colour, 16)
            if not 16777216 >= colourCode >= 0:
                return await functions.errorEmbedTemplate(ctx, f"The colour code input is invalid, please try again.",
                                                          ctx.author)
            await functions.colourChange(ctx, colour)

        except ValueError:
            traceback.print_exc()
            return await functions.errorEmbedTemplate(ctx, f"The colour code input is invalid, please try again.",
                                                      ctx.author)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        # if ctx.author.id == 624251187277070357:
        #     return await ctx.reinvoke()
        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(description=f"This command is on cooldown. "
                                              f"Please try again after{dmyConverter(round(error.retry_after, 1))}")
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(description="You are missing the required permissions to run this command!")
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(description=f"Missing a required argument: `{error.param}`")
            ctx.command.reset_cooldown(ctx)
        elif isinstance(error, commands.MissingAnyRole):
            embed = discord.Embed(
                description=f"{ctx.author.mention}, You do not have the required role to run this command.")
        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(description=f"This command can only be run by the Bot Owner!")
        else:
            embed = discord.Embed(description=f"{ctx.author.mention}, "
                                              f"Oh no! Something went wrong while running the command!")
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        await ctx.send(embed=embed, delete_after=10)


def setup(bot):
    bot.add_cog(AdminCommands(bot))
