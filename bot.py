import discord
from discord.ext import commands, tasks
import aiohttp
import datetime
import pytz
from dotenv import load_dotenv
import os
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID")) 
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


# === Daily Task ===
@tasks.loop(hours=1)
async def daily_task():
    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz)
    # print("DEBUG: bot.guilds =", bot.guilds)
    # print("DEBUG: CHANNEL_ID =", CHANNEL_ID)
    channel = bot.get_channel(CHANNEL_ID)
    # print("DEBUG: channel =", channel)

    channel = bot.get_channel(CHANNEL_ID)
    # if channel: print("Channel Found")
    # Run at exactly 10:00 AM
    if now.hour == 10:
        
        if channel:
            message = await send_daily_notification()
            await channel.send(message)


@daily_task.before_loop
async def before_daily():
    await bot.wait_until_ready()
    print("Daily task is running...")
    for guild in bot.guilds:
        print("Connected guild:", guild.name)
    # for channel in bot.get_all_channels():
    #     print("FOUND CHANNEL:", channel.id, channel.name)




@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    daily_task.start()

@bot.command()
async def test(ctx):
    msg = await send_daily_notification()
    await ctx.send(msg)

bot.run(TOKEN)
