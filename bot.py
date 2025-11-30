import discord
from discord.ext import commands, tasks
import aiohttp
import requests
import datetime
from discord import app_commands
import pytz
from dotenv import load_dotenv
import os
import csv
from utils import get_user_problem_status,get_problems
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID")) 
BOT_TOKEN= os.getenv("ACCESS_TOKEN")
CHAT_ID = os.getenv("GROUP_ID")
TIMEZONE = "Asia/Kolkata"  

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

CF_API_URL = "https://codeforces.com/api/contest.list"




async def get_upcoming_contests():
    """Fetch contests occurring within the next 3 days."""
    async with aiohttp.ClientSession() as session:
        async with session.get(CF_API_URL) as resp:
            data = await resp.json()

    now = datetime.datetime.utcnow()
    soon = now + datetime.timedelta(days=3)

    upcoming = []
    for contest in data["result"]:
        if contest["phase"] != "BEFORE":
            continue
        
        start = datetime.datetime.utcfromtimestamp(contest["startTimeSeconds"])

        if now <= start <= soon:
            upcoming.append({
                "name": contest["name"],
                "start": start,
                "duration": contest["durationSeconds"] // 3600
            })

    return upcoming


async def send_daily_notification():
    """Build and send the notification message."""
    contests = await get_upcoming_contests()

    if not contests:
        return "No contests in the next 3 days 💤"

    lines = ["📢 **Upcoming Codeforces Contests (Next 3 Days)**\n"]
    for c in contests:
        start_local = c["start"].replace(tzinfo=pytz.utc).astimezone(pytz.timezone(TIMEZONE))
        lines.append(
            f"🔸 **{c['name']}**\n"
            f"🕒 Starts: {start_local.strftime('%Y-%m-%d %H:%M %Z')}\n"
            f"⏳ Duration: {c['duration']} hrs\n"
        )

    return "\n".join(lines)
async def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

# === Daily Task ===
@tasks.loop(hours=1)
async def daily_task():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz)
    channel = bot.get_channel(CHANNEL_ID)
    if now.hour == 10:
        message = await send_daily_notification()
        if channel:
            await channel.send(message)
        await send_telegram_message(BOT_TOKEN, CHAT_ID, message)


@daily_task.before_loop
async def before_daily():
    await bot.wait_until_ready()
    print("Daily task is running...")
    for guild in bot.guilds:
        print("Connected guild:", guild.name)
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()   
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(e)
    daily_task.start()

@bot.command()
async def test(ctx):
    msg = await send_daily_notification()
    await ctx.send(msg)
async def userinfo(username: str):
    url = f"https://codeforces.com/api/user.info?handles={username}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
    if data["status"] != "OK":
        return None
    return data["result"][0]
@bot.tree.command(name="user", description="get-the-info-of-a-user")
@app_commands.describe(username="Codeforces username")
async def user(interaction: discord.Interaction, username: str):
    await interaction.response.send_message("Fetching user info...")
    user_data = await userinfo(username)
    if not user_data:
        await interaction.edit_original_response(content="User not found.")
        return
    else:
        await interaction.edit_original_response(content=f"User: {user_data['handle']} {","+user_data["organisation"] if user_data["organisation"] else "" },\nRating: {user_data.get('rating', 'Unrated')}\nMax Rating: {user_data.get('maxRating', 'Unrated')}\nRank: {user_data.get('rank', 'Unranked')}\nMax Rank: {user_data.get('maxRank', 'Unranked')}")
@bot.tree.command(name="problems", description="Find Some rated problems")
@app_commands.describe(rating="Problem rating", number="Number of problems",username="Your Codeforces username")
async def problems(interaction: discord.Interaction, rating: int, number: int, username: str):
    await interaction.response.send_message("Fetching problems...")
    solved_file = "solved.csv"
    await get_user_problem_status(username)
    problem_links = await get_problems(rating, number, solved_file,handle=username)
    if not problem_links:
        await interaction.edit_original_response(content="No unsolved problems found with the specified rating.")
        return
    response = "Here are some problems for you:\n" + "\n".join(problem_links)
    await interaction.edit_original_response(content=response)
bot.run(TOKEN)
