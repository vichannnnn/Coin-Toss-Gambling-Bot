from discord.ext import commands
import discord
import sqlite3
from Database import Database
import json

conn = sqlite3.connect('bot.db', timeout=5.0)
c = conn.cursor()
conn.row_factory = sqlite3.Row

c.execute(
    '''CREATE TABLE IF NOT EXISTS userProfile (
    userID INT PRIMARY KEY, 
    wonCurrency LIST DEFAULT 0,
    boughtCurrency FLOAT DEFAULT 0
    ) ''')

c.execute(
    '''CREATE TABLE IF NOT EXISTS guildProfile (
    guildID INT PRIMARY KEY, 
    coinFlipWin TEXT DEFAULT "[0.45, 0.40, 0.35, 0.29]",
    allOrNothingWin TEXT DEFAULT "[0.35, 0.29, 0.15]",
    coinFlipSpecial FLOAT DEFAULT 0.001,
    victoryProfit FLOAT DEFAULT 2.0
    ) ''')


def create_member_profile(member: discord.Member):
    try:
        Database.execute('INSERT INTO userProfile (userID) VALUES (?) ', member.id)

    except sqlite3.IntegrityError:
        print(f"Member: {member} already has a database profile created.")

    item_list = [i[0] for i in Database.get('SELECT itemTypeID FROM shopItems')]
    for id in item_list:
        try:
            Database.execute('INSERT INTO userInventory (userID, typeID) VALUES (?, ?) ', member.id, id)

        except sqlite3.IntegrityError:
            print(f"Member: {member} already has a Item ID: {id} created.")


def create_guild_profile(guild: discord.Guild):
    try:
        Database.execute('INSERT INTO guildProfile (guildID) VALUES (?) ', guild.id)

    except sqlite3.IntegrityError:
        print(f"Guild: {guild} already has a database profile created.")

    try:
        Database.execute('INSERT INTO shopsettings (guildID) VALUES (?) ', guild.id)

    except sqlite3.IntegrityError:
        print(f"Guild: {guild} already has a shop profile created.")


class Player:
    def __init__(self, user: int):
        self.inventory = None
        self.bought_currency = None
        self.won_currency = None
        self.user = user
        self.count = [i[0] for i in Database.get('SELECT COUNT(*) FROM userProfile WHERE userID = ? ', self.user)][0]

    def get_won_currency(self):
        self.won_currency = [i[0] for i in Database.get(
            'SELECT wonCurrency FROM userProfile WHERE userID = ? ', self.user)][0] if self.count else None
        return self.won_currency

    def get_bought_currency(self):
        self.bought_currency = [i[0] for i in Database.get(
            'SELECT boughtCurrency FROM userProfile WHERE userID = ? ', self.user)][0] if self.count else None
        return self.bought_currency

    def bought_credit_transaction(self, amount: int):
        self.bought_currency = self.get_bought_currency()
        self.bought_currency += amount
        Database.execute('UPDATE userProfile SET boughtCurrency = ? WHERE userID = ? ', self.bought_currency, self.user)
        return self.bought_currency

    def won_credit_transaction(self, amount: int):
        self.won_currency = self.get_won_currency()
        self.won_currency += amount
        Database.execute('UPDATE userProfile SET wonCurrency = ? WHERE userID = ? ', self.won_currency, self.user)
        return self.won_currency

    def get_full_inventory(self):
        self.inventory = [i for i in Database.get('SELECT typeID, itemQuantity FROM userInventory WHERE userID = ? ',
                                                  self.user)] if self.count else None
        return self.inventory

    def get_item(self, id: int):
        quantity = [i[0] for i in
                    Database.get('SELECT itemQuantity FROM userInventory WHERE userID = ? AND typeID = ? ',
                                 self.user, id)][0] if self.count else None
        return quantity

    def inventory_transaction(self, id: int, amount: int):
        quantity = int(self.get_item(id))
        quantity += amount
        Database.execute('UPDATE userInventory SET itemQuantity = ? WHERE userID = ? AND typeID = ? ', quantity,
                         self.user, id)
        return quantity


class Guild:
    def __init__(self, guild):
        self.shop_title = None
        self.shop_description = None
        self.shop_thank_you_message = None
        self.victory_profit = None
        self.coin_flip_special_odds = None
        self.coin_flip_win_odds = None
        self.all_or_nothing_win_odds = None
        self.guild = guild
        self.count = \
            [i[0] for i in Database.get('SELECT COUNT(*) FROM guildProfile WHERE guildID = ? ', self.guild)][0]

    def get_shop(self):
        self.shop_title, self.shop_description, self.shop_thank_you_message = [i for i in Database.get(
            'SELECT name, description, thankyoumessage FROM shopsettings WHERE guildID = ? ', self.guild)][0] if self.count else None
        return self.shop_title, self.shop_description, self.shop_thank_you_message

    def get_coin_flip_win_odds(self):
        win_odds = \
            [i[0] for i in Database.get('SELECT coinFlipWin FROM guildProfile WHERE guildID = ? ', self.guild)][
                0] if self.count else None

        self.coin_flip_win_odds = json.loads(win_odds)
        return self.coin_flip_win_odds

    def get_all_or_nothing_win_odds(self):
        win_odds = \
            [i[0] for i in Database.get('SELECT allOrNothingWin FROM guildProfile WHERE guildID = ? ', self.guild)][
                0] if self.count else None

        self.all_or_nothing_win_odds = json.loads(win_odds)
        return self.all_or_nothing_win_odds

    def get_coin_flip_special_odds(self):
        self.coin_flip_special_odds = \
            [i[0] for i in Database.get('SELECT coinFlipSpecial FROM guildProfile WHERE guildID = ? ', self.guild)][
                0] if self.count else None

        return self.coin_flip_special_odds

    def get_profit(self):
        self.victory_profit = \
            [i[0] for i in Database.get('SELECT victoryProfit FROM guildProfile WHERE guildID = ? ', self.guild)][
                0] if self.count else None

        return self.victory_profit


class BalanceHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        guild_database = [i[0] for i in Database.get(' SELECT guildID FROM guildProfile ')]

        if guild.id not in guild_database:
            create_guild_profile(guild)

        user_database = [i[0] for i in Database.get(' SELECT userID FROM userProfile ')]

        for member in guild.members:
            if member.id not in user_database:
                create_member_profile(member)

    @commands.Cog.listener()
    async def on_ready(self):

        user_database = [i[0] for i in Database.get(' SELECT userID FROM userProfile ')]

        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id not in user_database:
                    create_member_profile(member)

        guild_database = [i[0] for i in Database.get(' SELECT guildID FROM guildProfile ')]

        for guild in self.bot.guilds:
            if guild.id not in guild_database:
                create_guild_profile(guild)

    @commands.Cog.listener()
    async def on_member_join(self, member):

        user_database = [i[0] for i in Database.get(' SELECT userID FROM userProfile ')]

        if member.id not in user_database:
            create_member_profile(member)


def setup(bot):
    bot.add_cog(BalanceHandler(bot))
