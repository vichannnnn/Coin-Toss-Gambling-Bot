import random
import discord
from discord.ext import commands
import cogs.colourEmbed as functions
from cogs.BalanceHandler import Player, Guild
from cogs.Shop import Item, ItemType


def determine_normal_win_rate(guild: discord.Guild, count: int):
    guild_object = Guild(guild.id)
    guild_object.get_coin_flip_win_odds()
    first, second, third, fourth = guild_object.coin_flip_win_odds
    win_rate = {
        1: first,
        2: second,
        3: third,
        4: fourth
    }

    try:
        rate = win_rate[count]
        return rate

    except KeyError:
        return win_rate[4]


def determine_aon_win_rate(guild: discord.Guild, count: int):
    guild_object = Guild(guild.id)
    guild_object.get_all_or_nothing_win_odds()
    first, second, third = guild_object.all_or_nothing_win_odds
    win_rate = {
        1: first,
        2: second,
        3: third
    }

    try:
        rate = win_rate[count]
        return rate

    except KeyError:
        return win_rate[3]


class CoinToss(discord.ui.View):
    def __init__(self, ctx, amount: int, player: Player, guild: Guild):
        super().__init__()
        self.message = None
        self.timeout = 60
        self.value = None
        self.ctx = ctx
        self.amount = amount
        self.player = player
        self.member = ctx.guild.get_member(self.player.user)
        self.guild = guild
        self.guild.victory_profit = self.guild.get_profit()
        self.normal_count = 1
        self.aon_count = 1
        self.won_pool = 0
        self.bought_pool = 0

    async def interaction_check(self, interaction):
        return interaction.user.id == self.ctx.author.id

    async def on_timeout(self) -> None:
        self.clear_items()
        self.add_item(item=discord.ui.Button(emoji="❎", label="Coin Toss Timed Out",
                                             style=discord.ButtonStyle.red, disabled=True))
        await self.message.edit(content=f"{self.member.mention}, game timed out and has been successfully closed.",
                                view=self)
        self.stop()

    @discord.ui.button(label="Head", emoji="<a:GoldCoins:861479450017660958>")
    async def head(self, button: discord.ui.Button, interaction: discord.Interaction):

        if self.player.bought_currency < self.amount:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, You do not have enough tokens to play.", ephemeral=True)

        win_rate = determine_normal_win_rate(interaction.guild, self.normal_count)
        flip_result = random.choices(['h', 't'], weights=[win_rate, 1 - win_rate])[0]
        self.message = interaction.message

        if flip_result == 'h':
            coin_result = 'Head'
            coin_image = 'https://cdn.discordapp.com/emojis/773954685404446792.gif?v=1'
        else:
            coin_result = 'Tail'
            coin_image = 'https://cdn.discordapp.com/emojis/773954682350600224.gif?v=1'

        if 'h' == flip_result:
            won_amount = self.amount * self.guild.victory_profit
            self.won_pool += won_amount
            self.player.won_credit_transaction(won_amount)
            embed = discord.Embed(title=f"The coin landed on {coin_result}.",
                                  description=f"{self.ctx.author.mention} used **{self.amount:,} Tokens** "
                                              f"and won **{self.guild.victory_profit * self.amount:,} Tokens**",
                                  colour=functions.embedColour(self.ctx.guild.id))
            embed.add_field(name="Winning Pool", value=f"{self.won_pool:,} Tokens")
            embed.add_field(name="Bought Tokens Balance", value=f"{self.player.bought_currency:,} Tokens")
            embed.add_field(name="Won Tokens Balance", value=f"{self.player.won_currency:,} Tokens")
            embed.set_image(url=coin_image)

        else:
            self.player.bought_credit_transaction(-self.amount)
            embed = discord.Embed(title=f"The coin landed on {coin_result}.",
                                  description=f"{self.ctx.author.mention} bet **{self.amount:,} Tokens** and lost them all.",
                                  colour=functions.embedColour(self.ctx.guild.id))
            embed.add_field(name="Winning Pool", value=f"{self.won_pool:,} Tokens")
            embed.add_field(name="Bought Tokens Balance", value=f"{self.player.bought_currency:,} Tokens")
            embed.add_field(name="Won Tokens Balance", value=f"{self.player.won_currency:,} Tokens")
            embed.set_image(url=coin_image)
        self.normal_count += 1
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="Tails", emoji="<a:GoldCoins:861479450017660958>")
    async def tails(self, button: discord.ui.Button, interaction: discord.Interaction):

        if self.player.bought_currency < self.amount:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, You do not have enough tokens to play.", ephemeral=True)

        win_rate = determine_normal_win_rate(interaction.guild, self.normal_count)
        flip_result = random.choices(['h', 't'], weights=[1 - win_rate, win_rate])[0]
        self.message = interaction.message

        if flip_result == 'h':
            coin_result = 'Head'
            coin_image = 'https://cdn.discordapp.com/emojis/773954685404446792.gif?v=1'
        else:
            coin_result = 'Tail'
            coin_image = 'https://cdn.discordapp.com/emojis/773954682350600224.gif?v=1'

        if 't' == flip_result:
            won_amount = self.amount * self.guild.victory_profit
            self.won_pool += won_amount
            self.player.won_credit_transaction(won_amount)
            embed = discord.Embed(title=f"The coin landed on {coin_result}.",
                                  description=f"{self.ctx.author.mention} used **{self.amount:,} Tokens** "
                                              f"and won **{self.guild.victory_profit * self.amount:,} Tokens**",
                                  colour=functions.embedColour(self.ctx.guild.id))
            embed.add_field(name="Winning Pool", value=f"{self.won_pool:,} Tokens")
            embed.add_field(name="Bought Tokens Balance", value=f"{self.player.bought_currency:,} Tokens")
            embed.add_field(name="Won Tokens Balance", value=f"{self.player.won_currency:,} Tokens")
            embed.set_image(url=coin_image)

        else:
            self.player.bought_credit_transaction(-self.amount)
            embed = discord.Embed(title=f"The coin landed on {coin_result}.",
                                  description=f"{self.ctx.author.mention} bet **{self.amount:,} Tokens** and lost them all.",
                                  colour=functions.embedColour(self.ctx.guild.id))
            embed.add_field(name="Winning Pool", value=f"{self.won_pool:,} Tokens")
            embed.add_field(name="Bought Tokens Balance", value=f"{self.player.bought_currency:,} Tokens")
            embed.add_field(name="Won Tokens Balance", value=f"{self.player.won_currency:,} Tokens")
            embed.set_image(url=coin_image)
        self.normal_count += 1
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="All-Or-Nothing Heads", emoji="<a:GoldCoins:861479450017660958>")
    async def aon_heads(self, button: discord.ui.Button, interaction: discord.Interaction):

        if not self.won_pool:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, You do not have any winning pool tokens to play.", ephemeral=True)

        win_rate = determine_aon_win_rate(interaction.guild, self.aon_count)
        flip_result = random.choices(['h', 't'], weights=[1 - win_rate, win_rate])[0]
        self.message = interaction.message

        if flip_result == 'h':
            coin_result = 'Head'
            coin_image = 'https://cdn.discordapp.com/emojis/773954685404446792.gif?v=1'
        else:
            coin_result = 'Tail'
            coin_image = 'https://cdn.discordapp.com/emojis/773954682350600224.gif?v=1'

        if 'h' == flip_result:
            won_amount = self.won_pool * self.guild.victory_profit
            self.won_pool += won_amount
            self.player.won_credit_transaction(won_amount)
            embed = discord.Embed(title=f"The coin landed on {coin_result}.",
                                  description=f"{self.ctx.author.mention} used all the **{self.won_pool:,} Tokens** in their winning pool "
                                              f"and won **{self.guild.victory_profit * self.won_pool:,} Tokens**",
                                  colour=functions.embedColour(self.ctx.guild.id))
            embed.add_field(name="Winning Pool", value=f"{self.won_pool:,} Tokens")
            embed.add_field(name="Bought Tokens Balance", value=f"{self.player.bought_currency:,} Tokens")
            embed.add_field(name="Won Tokens Balance", value=f"{self.player.won_currency:,} Tokens")
            embed.set_image(url=coin_image)

        else:
            self.player.won_credit_transaction(-self.won_pool)
            embed = discord.Embed(title=f"The coin landed on {coin_result}.",
                                  description=f"{self.ctx.author.mention} bet **{self.won_pool:,} Tokens** and lost all their winning pool earnings..",
                                  colour=functions.embedColour(self.ctx.guild.id))
            self.won_pool = 0
            embed.add_field(name="Winning Pool", value=f"{self.won_pool:,} Tokens")
            embed.add_field(name="Bought Tokens Balance", value=f"{self.player.bought_currency:,} Tokens")
            embed.add_field(name="Won Tokens Balance", value=f"{self.player.won_currency:,} Tokens")
            embed.set_image(url=coin_image)
        self.aon_count += 1
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="All-Or-Nothing Tails", emoji="<a:GoldCoins:861479450017660958>")
    async def aon_tails(self, button: discord.ui.Button, interaction: discord.Interaction):

        if not self.won_pool:
            return await interaction.response.send_message(
                f"{interaction.user.mention}, You do not have any winning pool tokens to play.", ephemeral=True)

        win_rate = determine_aon_win_rate(interaction.guild, self.aon_count)
        flip_result = random.choices(['h', 't'], weights=[1 - win_rate, win_rate])[0]
        self.message = interaction.message

        if flip_result == 'h':
            coin_result = 'Head'
            coin_image = 'https://cdn.discordapp.com/emojis/773954685404446792.gif?v=1'
        else:
            coin_result = 'Tail'
            coin_image = 'https://cdn.discordapp.com/emojis/773954682350600224.gif?v=1'

        if 't' == flip_result:
            won_amount = self.won_pool * self.guild.victory_profit
            self.won_pool += won_amount
            self.player.won_credit_transaction(won_amount)
            embed = discord.Embed(title=f"The coin landed on {coin_result}.",
                                  description=f"{self.ctx.author.mention} used all the **{self.won_pool:,} Tokens** in their winning pool "
                                              f"and won **{self.guild.victory_profit * self.won_pool:,} Tokens**",
                                  colour=functions.embedColour(self.ctx.guild.id))
            embed.add_field(name="Winning Pool", value=f"{self.won_pool:,} Tokens")
            embed.add_field(name="Bought Tokens Balance", value=f"{self.player.bought_currency:,} Tokens")
            embed.add_field(name="Won Tokens Balance", value=f"{self.player.won_currency:,} Tokens")
            embed.set_image(url=coin_image)

        else:
            self.player.won_credit_transaction(-self.won_pool)
            embed = discord.Embed(title=f"The coin landed on {coin_result}.",
                                  description=f"{self.ctx.author.mention} bet **{self.won_pool:,} Tokens** and lost all their winning pool earnings..",
                                  colour=functions.embedColour(self.ctx.guild.id))
            self.won_pool = 0
            embed.add_field(name="Winning Pool", value=f"{self.won_pool:,} Tokens")
            embed.add_field(name="Bought Tokens Balance", value=f"{self.player.bought_currency:,} Tokens")
            embed.add_field(name="Won Tokens Balance", value=f"{self.player.won_currency:,} Tokens")
            embed.set_image(url=coin_image)
        self.aon_count += 1
        await interaction.message.edit(embed=embed)

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, emoji="❎")
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):

        self.clear_items()
        self.add_item(item=discord.ui.Button(emoji="❎", label="Exited From Game",
                                             style=discord.ButtonStyle.red, disabled=True))
        await self.message.edit(content=f"{self.member.mention}, game has been successfully closed.", view=self)
        self.stop()


class Games(commands.Cog, name="🎲 Games"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Checks your inventory bag.",
                      description="bag**\n\nChecks your inventory bag.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def bag(self, ctx):
        player_object = Player(ctx.author.id)
        user_inventory = player_object.get_full_inventory()

        length_record = []

        for id, qty in user_inventory:
            item_type_name = ItemType(id).get_item_name()
            length_desc = len(f"{qty:4,} | {item_type_name}")
            length_record.append(length_desc)

        description = f'```yaml\nQty. | Item           \n{max(length_record) * "="}\n'

        for id, qty in user_inventory:
            item_type_name = ItemType(id).get_item_name()
            description += f"{qty:4,} | " + item_type_name + '\n'

        description += '```'
        embed = discord.Embed(title=f"{ctx.author}'s Inventory Bag", description=description)
        await ctx.send(embed=embed)

    @commands.command(brief="Checks your current tokens balance.",
                      description="balance**\n\nChecks your current tokens balance.")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def balance(self, ctx):
        player_object = Player(ctx.author.id)
        won_currency = player_object.get_won_currency()
        bought_currency = player_object.get_bought_currency()

        embed = discord.Embed(title=f"{ctx.author}'s Wallet")
        embed.add_field(name="Won Tokens", value=f"{won_currency:,} Tokens")
        embed.add_field(name="Bought Tokens", value=f"{bought_currency:,} Tokens")
        await ctx.send(embed=embed)

    @commands.command(brief="Toss a coin and bet a fixed amount each round.",
                      description="toss [Amount]**\n\nToss a coin and bet a fixed amount each round.")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def toss(self, ctx, amount: float):
        player_object = Player(ctx.author.id)
        won_currency = player_object.get_won_currency()
        bought_currency = player_object.get_bought_currency()

        if bought_currency < amount:
            return await ctx.send(f"{ctx.author.mention}, You do not have enough tokens to play.")

        guild_object = Guild(ctx.guild.id)
        view = CoinToss(ctx, amount, player_object, guild_object)
        view.message = await ctx.send(
            "Click on the button below to start your coin toss. You can play as many times as you want!",
            view=view)
        await view.wait()


def setup(bot):
    bot.add_cog(Games(bot))
