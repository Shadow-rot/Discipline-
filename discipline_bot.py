import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from tinydb import TinyDB, Query

API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_BOT_TOKEN"

app = Client("discipline_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
db = TinyDB("streaks.json")
User = Query()

discipline_notes = """
**DISCIPLINED PROGRAMMER’S NOTES**

1. **Code Every Day**
> No excuses. One line is better than none. Momentum builds mastery.

2. **Write Clean Code**
> If it looks ugly, it probably is. Revisit, refactor, and respect the reader (including future-you).

3. **No Copy-Paste Without Understanding**
> You’re here to create, not just glue stackoverflow snippets.

4. **One Problem At A Time**
> Multitasking is a lie. Focus is your weapon—use it.

5. **Read Docs Before Asking**
> 90% of your questions are answered in the docs.

6. **Push to Git Daily**
> Small, consistent commits. Build it like a habit.

7. **Learn Something New Every Week**
> A new library, algorithm, or concept.

8. **Test Your Code**
> If it breaks in production, that’s your fault.

9. **Stop Comparing**
> Someone else’s repo isn’t your benchmark.

10. **Discipline Over Motivation**
> Motivation fades. Systems win. Stay sharp.
"""

# Replace with your chat IDs
PRIVATE_USER_ID = 123456789  
GROUP_ID = -1001234567890

# Store check-ins
check_ins = {}

def reset_check_ins():
    global check_ins
    check_ins = {}

def get_user_data(uid):
    user = db.get(User.id == uid)
    if not user:
        db.insert({"id": uid, "streak": 0, "last_check": None})
        return db.get(User.id == uid)
    return user

def update_streak(uid):
    user = get_user_data(uid)
    today = datetime.utcnow().date()
    last_check = user.get("last_check")

    if last_check == str(today):
        return  # already checked in today

    yesterday = today - timedelta(days=1)
    if last_check == str(yesterday):
        user["streak"] += 1
    else:
        user["streak"] = 1

    user["last_check"] = str(today)
    db.update(user, User.id == uid)

async def send_notes():
    await app.send_message(PRIVATE_USER_ID, discipline_notes)
    await app.send_message(GROUP_ID, discipline_notes)

async def send_reminder():
    for uid in [PRIVATE_USER_ID, GROUP_ID]:
        user = get_user_data(uid)
        today = str(datetime.utcnow().date())
        if user.get("last_check") != today:
            await app.send_message(uid, "**You haven't done your discipline check today. No excuses. Do it now with `/done`.**")

@app.on_message(filters.command("done"))
async def mark_done(client, message: Message):
    uid = message.from_user.id
    update_streak(uid)
    user = get_user_data(uid)
    await message.reply_text(f"**Check-in complete. Current streak: {user['streak']} days. Discipline wins.**")

@app.on_message(filters.private & ~filters.command("done"))
async def warn_private(client, message: Message):
    uid = message.from_user.id
    user = get_user_data(uid)
    today = str(datetime.utcnow().date())
    if user.get("last_check") != today:
        await message.reply_text("**You haven’t done `/done` today. Don't talk. Go read your notes.**")

@app.on_message(filters.group & ~filters.command("done"))
async def warn_group(client, message: Message):
    uid = message.from_user.id
    user = get_user_data(uid)
    today = str(datetime.utcnow().date())
    if user.get("last_check") != today:
        await message.reply_text(f"{message.from_user.first_name}, stop chatting. Do your `/done` first.")

async def start():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_notes, 'cron', hour=7, minute=0)
    for h in range(9, 24, 2):  # Reminder every 2 hours from 9 AM to 11 PM
        scheduler.add_job(send_reminder, 'cron', hour=h, minute=0)
    scheduler.start()
    await app.start()
    print("Discipline Bot is running.")
    await idle()
    await app.stop()

from pyrogram.idle import idle
asyncio.run(start())
