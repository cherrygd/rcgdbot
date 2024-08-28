import os
import discord
import asyncio
import json

from discord.ext import commands
from dotenv import load_dotenv


load_dotenv()

INTENTS = discord.Intents.all()
BOT_ACTIVITY = discord.Game("Отправь мне уровень ;)")
BOT_STATUS = discord.Status.online

bot = commands.Bot(
    command_prefix="!",
    intents=INTENTS,
    application_id=os.getenv("APP_ID"),
    help_command=None,
    sync_commands=True,
)


@bot.event
async def on_ready():
    print("Бот запущен")
    await bot.change_presence(status=BOT_STATUS, activity=BOT_ACTIVITY)


@bot.event
async def on_guild_join(guild: discord.Guild):
    try:
        lmt = await bot.tree.sync()
        await print(f"[Новый гилд: {guild.id}] Синхронизированно {len(lmt)} комманды!")
    except Exception as e:
        print(e)


@bot.command()
@commands.has_permissions(administrator=True)
async def sync(ctx: commands.Context) -> None:
    try:
        lmt = await bot.tree.sync()
        print(bot.cogs)
        await ctx.send(f"Синхронизированно {len(lmt)} комманды!")
    except Exception as e:
        print(e)


async def setup():
    print("Загрузка...")
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")


async def main_f():
    await setup()
    await bot.start(os.getenv("TOKEN"))


asyncio.run(main_f())
