import asyncio
import os

import aiohttp
import discord
from discord.ext import commands, tasks

TOKEN = os.environ["DISCORD_TOKEN"]
APP_ID = os.environ["APPLICATION_ID"]

initIntent = discord.Intents.default()
initIntent.members = True
initIntent.message_content = True

bot = commands.Bot(command_prefix='.',
                   intents=initIntent,
                   application_id=APP_ID
                   )


@bot.event
async def on_ready():  # On Ready Event

    await load_extensions()

    print(f'{bot.user} is connected to the following guild:\n')
    for guild in bot.guilds:  # Guilds
        print(
            f'{guild.name}(id: {guild.id})'
        )

    print(f'Listening for {bot.command_prefix}\n')

    game = discord.Activity(type=discord.ActivityType.listening, name=f'{bot.command_prefix}help for commands')
    await bot.change_presence(activity=game)


@bot.event
async def on_message(message):  # On Ready Event
    msg = message.content
    guild = message.guild
    if msg.startswith(bot.command_prefix):
        await bot.process_commands(message)

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):  # cut off the .py from the file name
            await bot.load_extension(f"cogs.{filename[:-3]}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong")


@bot.command()
async def dm(ctx):
    msg = await ctx.author.send(".ping")


bot.run(TOKEN)
