from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, 
                          MessageHandler, filters, CallbackContext)
import logging
import json
import os
import time 
import datetime
import json
from datetime import datetime
import csv
from telegram.ext import ContextTypes

REFERRAL_FILE = "referral_data.json"
WINNER_CSV_DIR = "winners"

DATA_FILE = "data.json"
ADMIN_ID = "2005048275"  # ✅ अपना Admin ID डालें
ADMIN_IDS = ["2005048275"]  # Add at top with other constants

# ✅ Load and Save JSON Data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ✅ Bot Token
TOKEN = "7213154954:AAGMlbCC6jeEbjGvdGhCsAktwuwujQcW9hE"

# ✅ Telegram Channels
CHANNELS = ["profitpaisaa", "visalearning", "esyloot", "profitroz"]

# ✅ Set Up Logging
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ Check if User is in All Channels
async def is_user_in_all_channels(user_id, application):
    for channel in CHANNELS:
        try:
            chat_member = await application.bot.get_chat_member(f"@{channel}", user_id)
            if chat_member.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            logger.error(f"Error checking {channel}: {e}")
            return False
    return True

# ✅ Start Command
# ✅ Start Command
async def start(update: Update, context: CallbackContext):
    user_id = str(update.message.chat.id)
    data = load_data()

    # ✅ Extract Referral ID from link
    args = context.args
    referrer_id = args[0] if args else None  

    # अगर user पहले से data में नहीं है तो नया entry बनाओ
    if user_id not in data:
        data[user_id] = {"balance": 0.50, "referrals": [], "last_bonus": 0, "referral_log": []}

        # ✅ Referrer का data जोड़ो
        if referrer_id and referrer_id != user_id:
            if referrer_id not in data:
                data[referrer_id] = {"balance": 0.50, "referrals": []}  # fallback in case referrer is new
            data[referrer_id]["balance"] += 0.50
            if user_id not in data[referrer_id]["referrals"]:
                data[referrer_id]["referrals"].append(user_id)
            data[referrer_id].setdefault("referral_log", [])
            data[referrer_id]["referral_log"].append(time.time())

        save_data(data)

    if not await is_user_in_all_channels(user_id, context.application):
        await send_join_message(update)
    else:
        await show_main_menu(update, context)


# ✅ Send Join Message with Buttons
async def send_join_message(update: Update):
    keyboard = []

    # Add 2 buttons per row
    for i in range(0, len(CHANNELS), 2):
        row = []
        for channel in CHANNELS[i:i+2]:
            row.append(InlineKeyboardButton("📲 Join Now", url=f"https://t.me/{channel}"))
        keyboard.append(row)

    # Add the final "I Joined" button
    keyboard.append([InlineKeyboardButton("✅ I Joined", callback_data="check_join")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🚨 To continue free Earning money, please join all the required channels.\n\nAfter joining, click *'I Joined'* to continue.",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )



# ✅ Check If User Joined the Channels
async def check_join(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id

    if await is_user_in_all_channels(user_id, context.application):
        await query.message.delete()  # ✅ पुराना मैसेज हटाएं
        await show_main_menu(update, context, query)  # ✅ Main Menu दिखाएं
    else:
        await query.answer("❌ You have not joined all channels. Please join first!", show_alert=True)


      
# ✅ Show Main Menu
# ✅ Show Main Menu (Fix for callback issue)
async def show_main_menu(update: Update, context: CallbackContext, query=None):
    keyboard = [
        [InlineKeyboardButton("💰 Balance", callback_data="balance"),
         InlineKeyboardButton("👥 Refer & Earn", callback_data="refer")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
         InlineKeyboardButton("🎁 Daily Bonus", callback_data="daily_bonus")],
        [InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")]

    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:  # ✅ If called from callback (I Joined)
        await query.message.reply_text("✅ Welcome! Choose an option:", reply_markup=reply_markup)
    else:  # ✅ If called from /start
        await update.message.reply_text("✅ Welcome! Choose an option:", reply_markup=reply_markup)


import csv
from io import StringIO
from telegram import InputFile

# ✅ Export all referral data to CSV and send to admin
async def export_referral_data(update: Update, context: CallbackContext):
    if str(update.message.chat.id) != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to export data!")
        return

    data = load_data()
    if not data:
        await update.message.reply_text("📂 No data to export!")
        return

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["User ID", "Balance", "Referral Count", "Referral IDs"])

    for user_id, info in data.items():
        referrals = info.get("referrals", [])
        writer.writerow([
            user_id,
            info.get("balance", 0),
            len(referrals),
            ", ".join(referrals)
        ])

    output.seek(0)
    csv_file = InputFile(output, filename="referral_data.csv")
    await context.bot.send_document(chat_id=ADMIN_ID, document=csv_file, caption="📊 Referral data exported!")





# ✅ Handle Button Clicks
async def handle_button_click(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == "balance":
        await check_balance(update, context)
    elif query.data == "refer":
        bot_username = context.application.bot.username
        referral_link = f"https://t.me/{bot_username}?start={query.from_user.id}"
        await query.message.reply_text(
            f"📢 *Share your referral link:*\n\n🔗 {referral_link}\n👥 Earn Upto ₹2 per invite!",
            parse_mode="Markdown"
        )
    elif query.data == "withdraw":
        await withdraw_request(update, context)
    elif query.data == "check_join":  # ✅ "I Joined" Button Fix
        await check_join(update, context)
    elif query.data == "daily_bonus":
        await handle_daily_bonus(update, context)
    elif query.data == "leaderboard":
        await show_leaderboard(update, context)



# ✅ Check Balance
async def check_balance(update: Update, context: CallbackContext):
    user_id = str(update.effective_chat.id)
    data = load_data()

    balance = data.get(user_id, {}).get("balance", 0)
    referrals = len(data.get(user_id, {}).get("referrals", []))

    await update.effective_message.reply_text(
        f"💰 Your Balance: ₹{balance}\n"
        f"👥 Total Referrals: {referrals}\n"
        f"💸 Minimum Withdrawal: ₹3",
        parse_mode="Markdown"
    )

# ✅ Handle Withdraw Request
async def withdraw_request(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)
    data = load_data()

    if data.get(user_id, {}).get("balance", 0) >= 3:
        await query.answer()
        await query.message.reply_text("💸 Please send your *UPI ID*:", parse_mode="Markdown")
        context.user_data["awaiting_upi"] = True
    else:
        await query.answer()
        await query.message.reply_text("❌ *You need at least ₹3 to withdraw.*", parse_mode="Markdown")

# ✅ Handle Text Messages
# ✅ Handle Text Messages (Merged)
async def handle_message(update: Update, context: CallbackContext):
    if not update.message:
        return  
    user_id = str(update.message.chat.id)
    message = update.message.text.strip()
    data = load_data()

    # ✅ Admin is sending broadcast
    if context.user_data.get("awaiting_broadcast") and user_id == ADMIN_ID:
        context.user_data["awaiting_broadcast"] = False
        sent_count = 0

        for uid in data.keys():
            try:
                if update.message.text:
                    await context.bot.send_message(chat_id=uid, text=message)
                elif update.message.photo:
                    await context.bot.send_photo(chat_id=uid, photo=update.message.photo[-1].file_id, caption=update.message.caption or "")
                elif update.message.video:
                    await context.bot.send_video(chat_id=uid, video=update.message.video.file_id, caption=update.message.caption or "")
                else:
                    continue
                sent_count += 1
            except Exception as e:
                logging.warning(f"Failed to send to {uid}: {e}")

        await update.message.reply_text(f"✅ Broadcast sent to {sent_count} users!")
        return


    # ✅ UPI Withdrawal - Step 1: UPI ID
    if context.user_data.get("awaiting_upi"):
        context.user_data["upi_id"] = message
        context.user_data["awaiting_upi"] = False
        context.user_data["awaiting_amount"] = True
        await update.message.reply_text(
            "✅ *UPI ID saved!* Now enter the amount you want to withdraw (Minimum ₹3):",
            parse_mode="Markdown"
        )
        return

    # ✅ UPI Withdrawal - Step 2: Amount
    if context.user_data.get("awaiting_amount"):
        if not message.isdigit():
            await update.message.reply_text("❌ Please enter a valid amount.")
            return

        amount = int(message)
        if amount < 3:
            await update.message.reply_text("❌ Minimum withdrawal is ₹3.")
            return

        if data.get(user_id, {}).get("balance", 0) >= amount:
            data[user_id]["balance"] -= amount
            save_data(data)

            upi_id = context.user_data.get("upi_id")

            # ✅ Send to Admin
            admin_msg = (
                f"🆕 *New Withdrawal Request!*\n\n"
                f"👤 User ID: `{user_id}`\n"
                f"💰 Amount: ₹{amount}\n"
                f"💳 UPI ID: `{upi_id}`"
            )
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")

            await update.message.reply_text(
                f"✅ *Withdrawal request submitted!*\n\n"
                f"📌 *Details:*\n"
                f"💰 Amount: ₹{amount}\n"
                f"💳 UPI ID: `{upi_id}`\n"
                "⏳ Please wait while the admin processes your request.",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ *You don't have enough balance to withdraw!*", parse_mode="Markdown")

        context.user_data["awaiting_amount"] = False
        return

    # ❓ Default Fallback Response
    await update.message.reply_text("🤖 Please use the buttons to navigate the bot.")


# ✅ Show Referral Stats (Admin Only)
# ✅ Admin Command to Check Referrals (Full Stats)
async def show_referral_details(update: Update, context: CallbackContext):
    if str(update.message.chat.id) != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to view this data!")
        return

    data = load_data()

    if not data:
        await update.message.reply_text("📊 No referrals yet!", parse_mode="Markdown")
        return

    messages = []
    current_msg = "📊 *Referral Stats:*\n\n"

    for user_id, info in data.items():
        count = len(info.get("referrals", []))
        line = f"👤 User `{user_id}` → {count} referrals\n"
        
        if len(current_msg) + len(line) > 4000:
            messages.append(current_msg)
            current_msg = ""

        current_msg += line

    messages.append(current_msg)

    for msg in messages:
        await update.message.reply_text(msg, parse_mode="Markdown")

# ✅ Admin Broadcast Command
async def broadcast_command(update: Update, context: CallbackContext):
    if str(update.message.chat.id) != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to broadcast!")
        return

    context.user_data["awaiting_broadcast"] = True
    await update.message.reply_text("📢 Please send the *message* you want to broadcast to all users:", parse_mode="Markdown")


async def show_leaderboard(update: Update, context: CallbackContext):
    data = load_data()
    rewards = load_rewards()
    now = time.time()
    daily_counts = []

    for user_id, info in data.items():
        logs = info.get("referral_log", [])
        today_refs = [t for t in logs if now - t <= 86400]
        count = len(today_refs)
        if count > 0:
            daily_counts.append((user_id, count))

    daily_counts.sort(key=lambda x: x[1], reverse=True)

    if not daily_counts:
        await update.effective_message.reply_text("📊 No referrals yet today!")
        return

    message = "🏆 *Daily Leaderboard (24 hrs)*\n\n"
    for rank, (uid, count) in enumerate(daily_counts[:len(rewards)], start=1):
        reward = rewards[rank - 1] if rank <= len(rewards) else 0
        message += f"{rank}. 👤 `{uid}` → {count} invites — 💰 ₹{reward}\n"

    await update.effective_message.reply_text(message, parse_mode="Markdown")





REWARDS_FILE = "rewards.json"

def load_rewards():
    if not os.path.exists(REWARDS_FILE):
        return [10, 5, 2]  # default rewards
    with open(REWARDS_FILE, "r") as f:
        return json.load(f)

def save_rewards(rewards):
    with open(REWARDS_FILE, "w") as f:
        json.dump(rewards, f)

async def set_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.id) != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this.")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: /setrewards 10 5 2")
        return

    try:
        rewards = list(map(int, context.args))
        save_rewards(rewards)
        await update.message.reply_text(f"✅ Rewards updated: {rewards}")
    except:
        await update.message.reply_text("❌ Invalid format! Use /setrewards 10 5 2")




# ✅ Handle Daily Bonus
async def handle_daily_bonus(update: Update, context: CallbackContext):
    user_id = str(update.effective_chat.id)
    data = load_data()
    user_data = data.get(user_id)

    if not user_data:
        await update.callback_query.message.reply_text("❌ Please use /start first.")
        return

    now = time.time()
    last_claim = user_data.get("last_bonus", 0)

    if now - last_claim >= 86400:  # 24 hours
        bonus = 0.25  # Daily Bonus amount
        user_data["balance"] += bonus
        user_data["last_bonus"] = now
        save_data(data)

        await update.callback_query.message.reply_text(f"🎉 You've received ₹{bonus} Daily Bonus!")
    else:
        remaining = int((86400 - (now - last_claim)) // 3600)
        await update.callback_query.message.reply_text(
            f"⏳ You have already claimed your bonus today.\nCome back in {remaining} hours!"
        )



# Global variable to store rewards
daily_rewards = {}  # Example: {1: 10, 2: 5, 3: 3}





async def process_daily_rewards(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime('%Y-%m-%d')

    # Load referrals
    try:
        with open(REFERRAL_FILE, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    # Calculate leaderboard
    leaderboard = []
    for user_id, user_data in data.items():
        count = user_data.get("referrals", {}).get(today, 0)
        if count > 0:
            leaderboard.append((user_id, user_data.get("name", "User"), count))

    leaderboard.sort(key=lambda x: x[2], reverse=True)

    # Assign rewards based on rank
    winners = []
    for idx, (user_id, name, count) in enumerate(leaderboard[:len(daily_rewards)]):
        rank = idx + 1
        reward = daily_rewards.get(rank, 0)
        data[user_id]["balance"] = data[user_id].get("balance", 0) + reward
        winners.append({
            "rank": rank,
            "user_id": user_id,
            "name": name,
            "referrals": count,
            "reward": reward
        })

    # Save updated balances
    with open(REFERRAL_FILE, "w") as f:
        json.dump(data, f, indent=2)

    # Save winners CSV
    import os
    os.makedirs(WINNER_CSV_DIR, exist_ok=True)
    csv_filename = f"{WINNER_CSV_DIR}/daily_winners_{today}.csv"
    with open(csv_filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["rank", "user_id", "name", "referrals", "reward"])
        writer.writeheader()
        writer.writerows(winners)

    # Broadcast winners
    if winners:
        text = "🏆 *Today's Top Referrers*\n\n"
        for w in winners:
            text += f"{w['rank']}. {w['name']} - {w['referrals']} refs - ₹{w['reward']}\n"
        await context.bot.send_message(chat_id=BROADCAST_CHANNEL_ID, text=text, parse_mode="Markdown")
    else:
        await context.bot.send_message(chat_id=BROADCAST_CHANNEL_ID, text="📊 No referrals today.")



from apscheduler.schedulers.asyncio import AsyncIOScheduler
application = Application.builder().token("7213154954:AAGMlbCC6jeEbjGvdGhCsAktwuwujQcW9hE").build()

scheduler = AsyncIOScheduler()
scheduler.add_job(process_daily_rewards, 'cron', hour=0, minute=0, args=[application.bot])


async def start_scheduler(app: Application):
    scheduler.start()
    logging.info("Scheduler started")

# Register post init hook
application.post_init = start_scheduler


from telegram.constants import ParseMode

async def top_referrals(update: Update, context: CallbackContext):
    users = load_users()
    rewards = load_rewards()  # e.g., [10, 5, 2]

    # Get top 3 users based on referrals in last 24 hours
    top_users = sorted(
        [(uid, data.get("referrals_today", 0)) for uid, data in users.items()],
        key=lambda x: x[1],
        reverse=True
    )[:3]

    if not top_users or all(refs == 0 for _, refs in top_users):
        await update.message.reply_text("❌ No referrals in the last 24 hours.")
        return

    msg = "🏆 <b>Top 3 Referrers (Last 24 Hours)</b>\n\n"
    medals = ["🥇", "🥈", "🥉"]

    for i, (user_id, invites) in enumerate(top_users):
        try:
            user = await context.bot.get_chat(user_id)
            mention = f"@{user.username}" if user.username else user.first_name
        except:
            mention = f"<code>{user_id}</code>"

        reward = rewards[i] if i < len(rewards) else 0
        msg += f"{medals[i]} {mention} - {invites} invites - ₹{reward}\n"

    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)


# ✅ Main Function
def main():
    app = Application.builder().token(TOKEN).build()
    
    # ✅ Register Command and CallbackQuery Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("referrals", show_referral_details))
    app.add_handler(CommandHandler("export", export_referral_data))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(CommandHandler("setrewards", set_rewards))
    application.add_handler(CommandHandler("topreferrals", top_referrals))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))  # ✅ Moved above app.run_polling()
    app.add_handler(CallbackQueryHandler(handle_button_click))
    
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    app.run_polling()

if __name__ == "__main__":
    main()
