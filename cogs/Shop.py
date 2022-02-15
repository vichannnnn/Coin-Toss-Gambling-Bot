import sqlite3
from discord.ext import commands
import cogs.colourEmbed as functions
import discord
from Database import Database
import math
from cogs.BalanceHandler import Player, Guild

conn = sqlite3.connect('bot.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row

c.execute(
    '''CREATE TABLE IF NOT EXISTS shopsettings (
    guildID INT PRIMARY KEY, 
    name TEXT DEFAULT "Token Shop", 
    description TEXT DEFAULT "Welcome to the shop.", 
    thankyoumessage TEXT DEFAULT "Thank you for your purchase."
    ) ''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS shopItems (
    itemID INT PRIMARY KEY,
    itemType TEXT,
    itemName TEXT,
    itemTypeID INT,
    itemQuantity INT,
    itemCost INT,
    UNIQUE(itemName)
    )''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS userInventory (
    userID INT,
    typeID INT,
    itemQuantity INT DEFAULT 0,
    UNIQUE(userID, typeID)
    )''')


def initialize_shop_items():
    defaultItems = ((1, 1, 'Orbs', 10, '10 Orbs', 12),
                    (2, 1, 'Orbs', 25, '25 Orbs', 35),
                    (3, 1, 'Orbs', 50, '50 Orbs', 70),
                    (4, 2, 'Hextech', 10, '10 Hextech', 8),
                    (5, 2, 'Hextech', 25, '25 Hextech', 28),
                    (6, 2, 'Hextech', 50, '50 Hextech', 55),
                    (7, 3, 'Masterwork', 10, '10 Masterwork', 12),
                    (8, 3, 'Masterwork', 25, '25 Masterwork', 32),
                    (9, 3, 'Masterwork', 50, '50 Masterwork', 63),
                    (10, 4, 'Skin', 1, '1 Skin', 22))

    for id, type_id, type, qty, name, cost in defaultItems:
        count = [i[0] for i in Database.get('SELECT COUNT(*) FROM shopItems WHERE itemID = ?', id)][0]

        if not count:
            Database.execute('INSERT INTO shopItems VALUES (?, ?, ?, ?, ?, ?) ', id, type, name, type_id, qty, cost)
            print(f"Initialized adding of {name} (ID: {id}) into the shop.")


initialize_shop_items()


class Item:
    def __init__(self, name):
        self.cost = None
        self.quantity = None
        self.type = None
        self.type_id = None
        self.id = None
        self.name = name
        self.count = [i[0] for i in Database.get('SELECT COUNT(*) FROM shopItems WHERE itemName = ? ', self.name)][0]

    def get_id(self):
        self.id = [i[0] for i in Database.get('SELECT itemID FROM shopItems WHERE itemName = ? ', self.name)][
            0] if self.count else None
        return self.id

    def get_type(self):
        self.type = [i[0] for i in Database.get('SELECT itemType FROM shopItems WHERE itemName = ? ', self.name)][
            0] if self.count else None
        return self.type

    def get_type_id(self):
        self.type_id = [i[0] for i in Database.get('SELECT itemTypeID FROM shopItems WHERE itemName = ? ', self.name)][
            0] if self.count else None
        return self.type_id

    def get_quantity(self):
        self.quantity = \
            [i[0] for i in Database.get('SELECT itemQuantity FROM shopItems WHERE itemName = ? ', self.name)][
                0] if self.count else None
        return self.quantity

    def get_cost(self):
        self.cost = [i[0] for i in Database.get('SELECT itemCost FROM shopItems WHERE itemName = ? ', self.name)][
            0] if self.count else None
        return self.cost


class ShopItem:
    def __init__(self, id):
        self.item = None
        self.name = None
        self.id = id
        self.count = [i[0] for i in Database.get('SELECT COUNT(*) FROM shopItems WHERE itemID = ? ', self.id)][0]

    def get_item(self):
        self.name = [i[0] for i in Database.get('SELECT itemName FROM shopItems WHERE itemID = ? ', self.id)][
            0] if self.count else None
        self.item = Item(self.name)
        return self.item

class ItemType:
    def __init__(self, type_id):
        self.name = None
        self.type_id = type_id
        self.count = [i[0] for i in Database.get('SELECT COUNT(*) FROM shopItems WHERE itemTypeID = ? ', self.type_id)][0]

    def get_item_name(self):
        self.name = [i[0] for i in Database.get('SELECT itemType FROM shopItems WHERE itemTypeID = ? ', self.type_id)][
            0] if self.count else None
        return self.name


class Choice(discord.ui.Select):
    def __init__(self, ctx, bot, placeholder, choices):
        self.ctx = ctx
        self.bot = bot
        options = []
        for id, name, cost in choices:
            options.append(discord.SelectOption(label=name))
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        labels = [i.label for i in self.options]
        idx = labels.index(self.values[0])
        name = str(self.options[idx].label)

        player_object = Player(interaction.user.id)
        item_object = Item(name)
        guild_object = Guild(interaction.guild_id)
        player_object.get_won_currency()
        item_object.get_cost()
        item_object.get_id()
        item_object.get_type_id()
        item_object.get_quantity()
        guild_object.get_shop()
        if player_object.won_currency - item_object.cost < 0:
            return await interaction.response.send_message(f"❌ Purchase is unsuccessful."
                                                           f"\n\nYou do not have sufficient balance to make this purchase."
                                                           f"\n\n**Your Balance:** {player_object.won_currency:,} Tokens"
                                                           f"\n\n**Item Cost:** {item_object.cost:,} Tokens",
                                                           ephemeral=True)

        description = f"{guild_object.shop_thank_you_message}\n\n**Balance:** {(player_object.won_currency - item_object.cost):,} Tokens"
        embed = discord.Embed(title=f"{name} Purchase Successful", description=description)

        player_object.inventory_transaction(item_object.type_id, item_object.quantity)
        player_object.won_credit_transaction(-item_object.cost)
        return await interaction.response.send_message(embed=embed, ephemeral=True)


class ShopMenu(discord.ui.View):
    def __init__(self, ctx, bot, data, title, description, item):
        super().__init__()
        self.message = None
        self.timeout = 60
        self.value = 1
        self.ctx = ctx
        self.data = data
        self.title = title
        self.description = description
        self.pages = math.ceil(len(self.data) / 4)
        self.item = item
        self.previous = item
        self.bot = bot
        self.add_item(self.item)

    async def interaction_check(self, interaction):
        self.message = interaction.message
        return interaction.user.id == self.ctx.author.id

    @discord.ui.button(label="Previous Page", emoji="⏪")
    async def left(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value -= 1
        if self.value <= 0 or self.value > self.pages:
            embed = discord.Embed(title=self.title, description=f"You have reached the end of the pages.")
            if self.ctx.guild.icon.url:
                embed.set_thumbnail(url=self.ctx.guild.icon.url)
            else:
                pass
            embed.set_footer(text=f"Press '⏩' to go back.", icon_url=self.ctx.author.display_avatar.url)

            if self.value < 0:
                self.value += 1
            await self.message.edit(embed=embed)

        else:
            every_page = [item for item in self.data[4 * (self.value - 1):self.value * 4]]
            item = Choice(self.ctx, self.bot, 'Select an item to purchase', [item for item in every_page])
            self.remove_item(self.previous)
            self.previous = item
            self.add_item(item)
            embed = discord.Embed(title=self.title, description=self.description)

            if self.ctx.guild.icon:
                embed.set_thumbnail(url=self.ctx.guild.icon.url)
            embed.set_footer(text=f"Page {self.value} of {self.pages}", icon_url=self.ctx.author.display_avatar.url)

            for id, name, cost in every_page:
                item_details = f"> Item ID: {id}"
                embed.add_field(name=f"{cost:,} Tokens • {name}", value=item_details, inline=False)
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Next Page", emoji="⏩")
    async def right(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value += 1

        if self.value > self.pages:
            embed = discord.Embed(title=self.title, description=f"You have reached the end of the pages.")
            if self.ctx.guild.icon:
                embed.set_thumbnail(url=self.ctx.guild.icon.url)
            embed.set_footer(text=f"Press '⏩' to go back.", icon_url=self.ctx.author.display_avatar.url)

            if self.value > self.pages + 1:
                self.value -= 1
            await self.message.edit(embed=embed)

        else:
            every_page = [item for item in self.data[4 * (self.value - 1):self.value * 4]]
            item = Choice(self.ctx, self.bot, 'Select an item to purchase', [item for item in every_page])
            self.remove_item(self.previous)
            self.previous = item
            self.add_item(item)
            embed = discord.Embed(title=self.title, description=self.description)

            if self.ctx.guild.icon:
                embed.set_thumbnail(url=self.ctx.guild.icon.url)
            embed.set_footer(text=f"Page {self.value} of {self.pages}", icon_url=self.ctx.author.display_avatar.url)

            for id, name, cost in every_page:
                item_details = f"> Item ID: {id}"
                embed.add_field(name=f"{cost:,} Tokens • {name}", value=item_details, inline=False)
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.red, emoji="❎")
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.clear_items()
        self.add_item(item=discord.ui.Button(emoji="❎", label="Shop Closed",
                                             style=discord.ButtonStyle.red, disabled=True))
        await self.message.edit(view=self)
        await interaction.response.send_message("Shop closed successfully. Interface will close in 5 seconds.",
                                                ephemeral=True)
        self.stop()

    async def on_timeout(self) -> None:
        self.clear_items()
        self.add_item(item=discord.ui.Button(emoji="❎", label="Shop Closed",
                                             style=discord.ButtonStyle.red, disabled=True))
        await self.message.edit(view=self)
        self.stop()


class ShopHandler(commands.Cog, name="🪙 Shop"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Type .shop to access shop and buy items",
                      description="shop**\n\nType .shop to access shop and buy items")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def shop(self, ctx):

        user_object = Player(ctx.author.id)

        if not user_object.count:
            return await functions.errorEmbedTemplate(ctx, f"You do not have an account.", ctx.author)

        guild_object = Guild(ctx.guild.id)
        title, desc, thank_you = guild_object.get_shop()
        shop_items = [i for i in Database.get(f'SELECT itemID, itemName, itemCost FROM shopItems')]

        if not shop_items:
            return await ctx.send("There are no items available in the shop yet.")

        pages = math.ceil(len(shop_items) / 4)
        i = 1
        every_page = [i for i in shop_items[4 * (i - 1):i * 4]]

        embed = discord.Embed(title=title, description=desc)
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text=f"Page {i} of {pages}", icon_url=ctx.author.display_avatar.url)

        for id, name, cost in every_page:
            item_details = f"> Item ID: {id}"
            embed.add_field(name=f"{cost:,} Tokens • {name}", value=item_details, inline=False)

        view = ShopMenu(ctx, self.bot, shop_items, title, desc,
                        Choice(ctx, self.bot, 'Select an item to buy', [item for item in every_page]))
        view.message = await ctx.send(embed=embed, view=view)


def setup(bot):
    bot.add_cog(ShopHandler(bot))
