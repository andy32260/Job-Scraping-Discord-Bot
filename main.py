import discord
from discord.ext import commands
import os
from database import DatabaseManager
from components import RapidAPIJobScraper
from dotenv import load_dotenv
from commands import setup_commands


load_dotenv()
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

recent_jobs = []
db = DatabaseManager()

white = 0xffffff
red = 0xff0000
green = 0x00ff00

job_scraper = RapidAPIJobScraper(os.getenv('RAPIDAPI_KEY'))

setup_commands(bot, db, job_scraper, recent_jobs, (red, white, green))


@bot.event
async def on_ready():
    print(f'{bot.user} is ready')


if __name__ == "__main__":
    discord_token = os.getenv('DISCORD_TOKEN')
    rapidapi_key = os.getenv('RAPIDAPI_KEY')

    if not discord_token:
        print("DISCORD_TOKEN not found in environment variables")
        exit(1)
    if not rapidapi_key:
        print("RAPIDAPI_KEY not found in environment variables")
        exit(1)

    print("Starting Job Search Bot")
    bot.run(discord_token)