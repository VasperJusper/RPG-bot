import asyncio
import os
import openai
import validators

import discord
import random
from discord.ext import commands
import sqlite3
import logging

openai.api_key = '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'

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
con = sqlite3.connect(os.path.join('db', 'db.db'))
cur = con.cursor()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
dashes = ['\u2680', '\u2681', '\u2682', '\u2683', '\u2684', '\u2685']


class RandomThings(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.request = False
        self.ans = None
        self.theme = ''
        self.data = {}
        self.players = {}

    @commands.command(name='list')
    async def player_list(self, ctx):
        p = []
        for e in cur.execute("""SELECT * FROM player_info""").fetchall():
            p.append(f"**{e[1]}**;   ({', '.join(e[2].split('%'))});   ({', '.join(e[3].split('%'))})")
        await ctx.send("\n".join(p))

    @commands.command(name='rpghelp')
    async def rules_help(self, ctx):
        await ctx.send("Welcome to VasperJusper's RPG v 0.1!")
        await ctx.send("To play just type in some commands, here is the list of them:")
        await ctx.send("#start\n")

    @commands.command(name='player_image_set')
    async def change_image(self, ctx, player, url):
        player = " ".join(player.split('%'))
        if validators.url(url):
            cur.execute(f"""UPDATE player_info SET Image = '{url}' WHERE Name = '{player}'""")
            con.commit()
            await ctx.send(f"{player}'s image set.")
        else:
            await ctx.send("String you sent is not a link!")

    @commands.command(name='newHero')
    async def new_hero(self, ctx, name, g='m'):
        name = " ".join(name.split('%'))
        if self.request:
            await ctx.send('Select your option first!')
            return 0
        pr = ['insignificant', 'poor', 'questionable', 'average', 'decent', 'brilliant']
        s = ''
        if g == 'm':
            s = 'His'
        elif g == 'f':
            s = 'Her'
        else:
            print(1 / 0)
        strength, intellect, charisma = random.randint(1, 6), random.randint(1, 6), random.randint(1, 6)
        self.players[name] = [strength, intellect, charisma, g]
        self.request = True
        stats = '%'.join([str(strength), str(intellect), str(charisma)])
        command = f"INSERT INTO player_info(Name, Stats, Inventory) VALUES ('{name.lower()}', '{stats}', 'paper sword')"
        cur.execute(command)
        start_gear = cur.execute("""SELECT Name FROM items WHERE Start = 'True'""").fetchall()
        con.commit()
        out = [f"The **{name.upper()}** appears...",
               f"{s} strength was {pr[strength - 1]} ({strength})",
               f"{s} intellect was {pr[intellect - 1]} ({intellect})",
               f"And {s.lower()} charisma was {pr[charisma - 1]} ({charisma})", "",
               f"Select your starter item:", ', '.join(map(lambda x: x[0], start_gear))]
        await ctx.send("\n".join(out))

    @commands.command(name='image')
    async def image(self, ctx, name):
        if len(self.theme) > 0:
            response = openai.Image.create(
                prompt='realistic' + self.theme + " ".join(name.split('%')),
                n=1,
                size="512x512"
            )
        else:
            response = openai.Image.create(
                prompt='realistic' + " ".join(name.split('%')),
                n=1,
                size="512x512"
            )
        image_url = response['data'][0]['url']
        await ctx.send(image_url)

    @commands.command(name='select')
    async def select(self, num):
        self.ans = num

    @commands.command(name='theme')
    async def theme(self, ctx, theme):
        if theme.lower() == 'none':
            self.theme = ""
        else:
            self.theme = theme
        await ctx.send("Theme set to " + theme + ".")

    @commands.command(name='give')
    async def give_item(self, ctx, player, item):
        pass

    @commands.command(name='info')
    async def info(self, ctx, category, name):
        name = ' '.join(name.split('%'))
        if category == 'i':
            c = self.itemStatsGet(name)
            s = ''
            if len(c['stats']) > 1:
                s = f"Given stats: {', '.join(c['stats'])}\n"
            await ctx.send(f"**{name.lower().capitalize()}**, attack {c['attack']}, defence {c['defence']}.\n{s}"
                           f"Rarity: ***{c['rarity']}***.\n"
                           f"*{c['desc']}*")
            await self.image(ctx, name + ", " + c['desc'])
        elif category == 'p':
            c = cur.execute(f"""SELECT * FROM player_info WHERE Name = '{name.lower()}'""").fetchall()[0]
            s = ''
            if len(c[-1]) > 0:
                s = c[-1]
            stats = c[2].split('%')
            await ctx.send(f"**{name.capitalize()}**, strength {stats[0]},"
                           f" intellect {stats[1]}, charisma {stats[2]}.\n"
                           f"Inventory: ***{', '.join(c[3].split('%'))}***.\n"
                           f"{s}")

    def itemStatsGet(self, name):
        c = cur.execute(f"""SELECT * FROM items WHERE Name = '{name.lower()}'""").fetchall()[0]
        return {'attack': c[2], 'defence': c[3], 'stats': c[4].split('%'),
                'req': c[5].split('%'), 'rarity': c[7], 'desc': c[8]}


bot = commands.Bot(command_prefix='!', intents=intents)

TOKEN = "MTA4OTkwMzM3MTY1OTUyNjE5NA.Gp6plu.R9ufgniqHu4xXF2ojiUlxSlkNYN4L27lhTxdGY"


async def main():
    await bot.add_cog(RandomThings(bot))
    await bot.start(TOKEN)


asyncio.run(main())
