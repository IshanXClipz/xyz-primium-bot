import os
import json
import threading
from flask import Flask
import telebot
from telebot import types
import firebase_admin
from firebase_admin import credentials, db

# --- FLASK KEEP-ALIVE SERVER (For UptimeRobot 24/7) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- CONFIGURATION & ENVIRONMENT VARIABLES ---
BOT_TOKEN = os.environ.get('BOT_TOKEN')
FIREBASE_URL = os.environ.get('FIREBASE_URL')
FIREBASE_CREDS_STR = os.environ.get('FIREBASE_CREDS')

if not BOT_TOKEN or not FIREBASE_URL or not FIREBASE_CREDS_STR:
    print("❌ Error: Missing Environment Variables!")
    exit(1)

# Initialize Firebase
try:
    creds_dict = json.loads(FIREBASE_CREDS_STR)
    cred = credentials.Certificate(creds_dict)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            'databaseURL': FIREBASE_URL
        })
    print("🔥 Firebase Connected Successfully!")
except Exception as e:
    print(f"❌ Firebase Connection Error: {e}")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Admin Username Configuration
ADMIN_USERNAME = "ISHAN_XYZ"

def is_admin(username):
    if not username:
        return False
    return username.strip().lstrip('@').lower() == ADMIN_USERNAME.lower()

# --- BOT COMMANDS & HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    username = user.username if user.username else "NoUsername"
    
    # Save/Check user in Firebase
    ref = db.reference('users/' + str(user.id))
    user_data = ref.get()
    
    if not user_data:
        ref.set({
            'user_id': user.id,
            'username': username,
            'ic_balance': 5.4,
            'referred_by': None
        })
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    b1 = types.InlineKeyboardButton("📦 Products", callback_data="products")
    b2 = types.InlineKeyboardButton("💰 My Wallet", callback_data="wallet")
    b3 = types.InlineKeyboardButton("🎁 Referral / Promo", callback_data="referral")
    b4 = types.InlineKeyboardButton("📞 Support", url="https://t.me/ISHAN_XYZ")
    markup.add(b1, b2, b3, b4)
    
    welcome_text = (
        "🤖 **XYZ PREMIUM BOT** 🤖\n\n"
        "🔥 **PREMIUM DIGITAL BOT** 🔥\n\n"
        "📦 Premium Projects & Files\n"
        "⚡ Fast & Instant Delivery\n"
        "🟢 24/7 Hours Online Active\n"
        "💵 Easy & Secure Payment\n"
        "💰 Affordable Prices\n\n"
        f"Welcome @{username}! Choose an option below 👇"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    
    if call.data == "wallet":
        ref = db.reference('users/' + str(user_id))
        user_data = ref.get()
        balance = user_data.get('ic_balance', 0.0) if user_data else 0.0
        
        text = f"💰 **Your Wallet Balance**\n\n💎 IC Balance: `{balance} IC`\n💳 Exchange Rate: ₹1 INR = 1.2 IC"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        
    elif call.data == "referral":
        promo_code = f"XYZ{user_id}"
        text = (
            "🎁 **Referral & Promo Program**\n\n"
            "Share your exclusive Promo Code with friends to earn instant IC bonuses!\n\n"
            f"🏷️ **Your Promo Code:** `{promo_code}`\n\n"
            "✨ Welcome Bonus: +5.4 IC\n"
            "🚀 Instant Referral Bonus: +6.0 IC"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        
    elif call.data == "products":
        text = "📦 **Available Premium Products & Files**\n\nSelect a category or item to purchase:"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="back_home"))
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        
    elif call.data == "back_home":
        user = call.from_user
        username = user.username if user.username else "User"
        markup = types.InlineKeyboardMarkup(row_width=2)
        b1 = types.InlineKeyboardButton("📦 Products", callback_data="products")
        b2 = types.InlineKeyboardButton("💰 My Wallet", callback_data="wallet")
        b3 = types.InlineKeyboardButton("🎁 Referral / Promo", callback_data="referral")
        b4 = types.InlineKeyboardButton("📞 Support", url="https://t.me/ISHAN_XYZ")
        markup.add(b1, b2, b3, b4)
        
        welcome_text = f"🤖 **XYZ PREMIUM BOT** 🤖\n\nWelcome back, @{username}! Choose an option below 👇"
        bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['ic', 'deduct', 'minus'])
def admin_ic_handler(message):
    user = message.from_user
    if not is_admin(user.username):
        bot.reply_to(message, "❌ You are not authorized to use admin commands!")
        return
        
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "⚠️ Usage: `/deduct <user_id> <amount>` or `/ic <user_id> <amount>`", parse_mode="Markdown")
        return
        
    target_user_id = parts[1]
    try:
        amount = float(parts[2])
    except ValueError:
        bot.reply_to(message, "⚠️ Invalid amount specified!")
        return
        
    ref = db.reference('users/' + str(target_user_id))
    user_data = ref.get()
    
    if not user_data:
        bot.reply_to(message, "❌ User not found in database!")
        return
        
    current_balance = user_data.get('ic_balance', 0.0)
    
    if parts[0].lower() in ['/deduct', '/minus']:
        new_balance = max(0.0, current_balance - amount)
        action_type = "Deducted"
    else:
        new_balance = current_balance + amount
        action_type = "Added"
        
    ref.update({'ic_balance': new_balance})
    bot.reply_to(message, f"✅ Successfully {action_type} {amount} IC. New Balance for {target_user_id}: `{new_balance} IC`", parse_mode="Markdown")

# --- MAIN ENTRY POINT ---
if __name__ == '__main__':
    keep_alive()
    print("🚀 Bot is polling live...")
    bot.infinity_polling(skip_pending=True)
 {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        return bot.reply_to(message, f"❌ User {target_username} not found in registered users!")

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(max(0.0, current_bal - amount), 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ DEDUCTION SUCCESSFUL!\n\n👤 User: {target_username}\n➖ Deducted: {amount} IC\n💰 Remaining Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['totalic', 'sentic'])
def admin_totalic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    total_sent = sum(float(val) for val in db.get("user_balances", {}).values())
    bot.reply_to(message, f"📈 **TOTAL IC SENT TO USERS:** {total_sent:.1f} IC", parse_mode='Markdown')

@bot.message_handler(commands=['icuse'])
def admin_icuse_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    total = db.get("total_earnings", 0.0)
    bot.reply_to(message, f"📉 TOTAL IC SPENT BY USERS: {total:.1f} IC")

@bot.message_handler(commands=['upload'])
def admin_upload_start(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    msg = bot.reply_to(message, "📦 Enter Category:\n\nOptions: Projects, Files, or ModApks")
    bot.register_next_step_handler(msg, process_upload_category)

def process_upload_category(message):
    cat = message.text.strip()
    if cat not in ["Projects", "Files", "ModApks"]:
        msg = bot.reply_to(message, "⚠️ Invalid Category! Send Projects, Files, or ModApks:")
        bot.register_next_step_handler(msg, process_upload_category)
        return
    upload_temp[message.from_user.id] = {"category": cat}
    msg = bot.reply_to(message, f"✅ Category set to {cat}.\n\n👉 Now enter Item Name:")
    bot.register_next_step_handler(msg, process_upload_name)

def process_upload_name(message):
    name = message.text.strip()
    upload_temp[message.from_user.id]["name"] = name
    msg = bot.reply_to(message, "👉 Now enter Price in IC (e.g., 10.0):")
    bot.register_next_step_handler(msg, process_upload_price)

def process_upload_price(message):
    try:
        price = float(message.text.strip())
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Invalid Price! Enter a valid number:")
        bot.register_next_step_handler(msg, process_upload_price)
        return
    upload_temp[message.from_user.id]["price"] = price
    msg = bot.reply_to(message, "👉 Now send the Telegram File_ID or Download Link/Text to be delivered upon purchase:")
    bot.register_next_step_handler(msg, process_upload_file)

def process_upload_file(message):
    file_id = message.text.strip() if message.text else (message.document.file_id if message.document else None)
    if not file_id:
        msg = bot.reply_to(message, "⚠️ Invalid input! Please send File_ID or text link:")
        bot.register_next_step_handler(msg, process_upload_file)
        return

    data = upload_temp[message.from_user.id]
    cat = data["category"]
    cat_key = "projects" if cat == "Projects" else ("files" if cat == "Files" else "mod_apks")
    
    item_id = str(len(db.get(cat_key, [])) + 1)
    new_item = {
        "id": item_id,
        "name": data["name"],
        "price": data["price"],
        "file_id": file_id
    }
    
    db.setdefault(cat_key, []).append(new_item)
    save_db()
    if message.from_user.id in upload_temp:
        del upload_temp[message.from_user.id]
    
    bot.reply_to(message, f"🎉 Successfully Uploaded!\n\n📦 Category: {cat}\n📛 Name: {new_item['name']}\n💰 Pri    "main_title": (
            "💎 VIP PROJECTS\n"
            "⚙️ VIP CONFIGS\n"
            "⚡ INSTANT DELIVERY\n"
            "🔒 SECURE PAYMENTS\n\n"
            "────────────────────────\n\n"
            "👤 USERNAME : {username}\n"
            "🆔 ID : {user_id}\n"
            "💰 BALANCE : {balance:.1f} IC\n"
            "🔱 EXCHANGE RATE : ₹1 INR = 1.2 IC\n"
            "💵 RATES: ₹10 = 12.0 IC | ₹20 = 24.0 IC\n\n"
            "────────────────────────\n\n"
            "🚀 SHURU KORTE BUY PROJECT BA CONFIG TAP KORUN!"
        ),
        "btn_buy_proj": "⭐ BUY PROJECT",
        "btn_buy_files": "⭐ BUY CONFIG",
        "btn_buy_mods": "⭐ BUY MOD APK'S",
        "btn_add_bal": "💳 ADD BALANCE",
        "btn_referral": "🎁 REFER & EARN",
        "btn_orders": "📦 YOUR ORDERS",
        "btn_channel": "📢 OFFICIAL CHANNEL",
        "btn_support": "📞 CUSTOMER SUPPORT",
        "btn_back": "⬅️ Main Menu te Phire Jan",
        "no_items": "⚠️ Ekhon kono {category} available nei.",
        "no_orders": "📦 Apni ekhono kono item korenni.",
        "orders_title": "📦 APNAR KHAREDA ORDERS:\nJekono somoy re-download korar jonno nicher button e tap korun!",
        "item_not_found": "❌ Item paoya jayni!",
        "not_enough_ic": "⚠️ Apnar kache porjapt IC balance nei!\nProyojon: {price} IC | Apnar Balance: {balance:.1f} IC\n\nDoya kore ADD BALANCE option diye balance jog korun.",
        "buy_success": "🎉 PURCHASE SUCCESSFUL!\n\n📦 Item: {name}\n💰 Deducted: {price} IC\n📦 Baki Balance: {new_balance:.1f} IC\n\nApnar file niche pathano holo! (15 min pore auto-delete hobe)",
        "add_bal_text": "💳 ADD BALANCE (MINIMUM ₹10 INR)\n\n🔱 Exchange Rate: ₹1 INR = 1.2 IC\n💵 RATES:\n• ₹10 INR = 12.0 IC\n• ₹20 INR = 24.0 IC\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba UPI ID te payment korun (Min ₹10).\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "support_text": "📞 CUSTOMER SUPPORT\n\nApnar kono prosno thakle ba payment/product niye sahajjo lagle nicher admin er sathe jogajog korun:\n\n👉 Admin Username: @{admin}",
        "channel_text": "📢 OFFICIAL CHANNEL\n\nRegular update, free config ebong notun project pete amader official channel join korun:\n\n👉 Channel Link: {channel}",
        "btn_chat_admin": "💬 Admin er sathe kotha bolun",
        "btn_visit_channel": "📢 Channel Visit korun",
        "pay_title": "💳 PAYMENT CHECKOUT (FAMPAY)\n\n📦 Item: {name}\n💰 Amount to Pay: {price} IC (₹{inr_price} INR)\n\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba FamPay ID te payment korun.\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "btn_send_ss": "📞 SEND PAYMENT SCREENSHOT TO ADMIN"
    }
}

def get_lang(user_id):
    return db.get("user_languages", {}).get(str(user_id), "EN")

def is_admin(user):
    if not user.username:
        return False
    return user.username.replace('@', '').strip().lower() == ADMIN_USERNAME.replace('@', '').strip().lower()

def is_banned(user):
    username = f"@{user.username}" if user.username else ""
    user_id = user.id
    banned_list = db.get("banned_users", [])
    return (username.lower() in [str(b).lower() for b in banned_list]) or (user_id in banned_list) or (str(user_id) in banned_list)

def schedule_file_deletion(chat_id, message_id):
    def delete_msg():
        time.sleep(900)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    threading.Thread(target=delete_msg, daemon=True).start()

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['toggle_bot'])
def admin_toggle_bot_command(message):
    global is_bot_active
    if not is_admin(message.from_user):
        return bot.reply_to(message, f"❌ Access Denied! Admin username is set to @{ADMIN_USERNAME}.")
    is_bot_active = not is_bot_active
    status = "ONLINE & ACTIVE ✅" if is_bot_active else "OFFLINE / MAINTENANCE ❌"
    bot.reply_to(message, f"🤖 Bot Status updated: {status}")

@bot.message_handler(commands=['ic'])
def admin_ic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /ic @username amount\nExample: /ic @BRUTALMOON 12.2")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format! Enter numbers only.")
    
    target_user_key = None
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        target_user_key = target_username.lower()
        db.setdefault("registered_users", {})[target_user_key] = target_username

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(current_bal + amount, 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ SUCCESS!\n\n👤 User: {target_username}\n➕ Added: {amount} IC\n💰 Total Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['deduct', 'minus'])
def admin_deduct_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /deduct @username amount\nExample: /deduct @BRUTALMOON 10.0")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format!")
    
    target_user_key = None
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        return bot.reply_to(message, f"❌ User {target_username} not found in registered users!")

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(max(0.0, current_bal - amount), 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ DEDUCTION SUCCESSFUL!\n\n👤 User: {target_username}\n➖ Deducted: {amount} IC\n💰 Remaining Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['totalic', 'sentic'])
def admin_totalic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    total_sent = sum(float(val) for val in db.get("user_balances", {}).values())
    bot.reply_to(message, f"📈 **TOTAL IC SENT TO USERS:** {total_sent:.1f} IC", parse_mode='Markdown')

@bot.message_handler(commands=['icuse'])
def admin_icuse_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    total = db.get("total_earnings", 0.0)
    bot.reply_to(message, f"📉 TOTAL IC SPENT BY USERS: {total:.1f} IC")

@bot.message_handler(commands=['upload'])
def admin_upload_start(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    msg = bot.reply_to(message, "📦 Enter Category:\n\nOptions: Projects, Files, or ModApks")
    bot.register_next_step_handler(msg, process_upload_category)

def process_upload_category(message):
    cat = message.text.strip()
    if cat not in ["Projects", "Files", "ModApks"]:
        msg = bot.reply_to(message, "⚠️ Invalid Category! Send Projects, Files, or ModApks:")
        bot.register_next_step_handler(msg, process_upload_category)
        return
    upload_temp[message.from_user.id] = {"category": cat}
    msg = bot.reply_to(message, f"✅ Category set to {cat}.\n\n👉 Now enter Item Name:")
    bot.register_next_step_handler(msg, process_upload_name)

def process_upload_name(message):
    name = message.text.strip()
    upload_temp[message.from_user.id]["name"] = name
    msg = bot.reply_to(message, "👉 Now enter Price in IC (e.g., 10.0):")
    bot.register_next_step_handler(msg, process_upload_price)

def process_upload_price(message):
    try:
        price = float(message.text.strip())
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Invalid Price! Enter a valid number:")
        bot.register_next_step_handler(msg, process_upload_price)
        return
    upload_temp[message.from_user.id]["price"] = price
    msg = bot.reply_to(message, "👉 Now send the Telegram File_ID or Download Link/Text to be delivered upon purchase:")
    bot.register_next_step_handler(msg, process_upload_file)

def process_upload_file(message):
    file_id = message.text.strip() if message.text else (message.document.file_id if message.document else None)
    if not file_id:
        msg = bot.reply_to(message, "⚠️ Invalid input! Please send File_ID or text link:")
        bot.register_next_step_handler(msg, process_upload_file)
        return

    data = upload_temp[message.from_user.id]
    cat = data["category"]
    cat_key = "projects" if cat == "Projects" else ("files" if cat == "Files" else "mod_apks")
    
    item_id = str(len(db.get(cat_key, [])) + 1)
    new_item = {
        "id": item_id,
        "name": data["name"],
        "price": data["price"],
        "file_id": file_id
    }
    
    db.setdefault(cat_key, []).append(new_item)
    save_db()
    if message.from_user.id in upload_temp:
        del upload_temp[message.from_user.id]
    
    bot.reply_to(message, f"🎉 Successfully Uploaded!\n\n📦 Category: {cat}\n📛 Name: {new_item['name']}\n💰 Prinel join karein:\n\n👉 Channel Link: {channel}",
        "btn_chat_admin": "💬 Admin se baat karein",
        "btn_visit_channel": "📢 Channel Dekhein",
        "pay_title": "💳 PAYMENT CHECKOUT (FAMPAY)\n\n📦 Item: {name}\n💰 Amount to Pay: {price} IC (₹{inr_price} INR)\n\n📱 FamPay UPI ID: {upi}\n\n👉 Upar diya gaya QR code scan karein ya FamPay ID par payment karein.\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "btn_send_ss": "📞 SEND PAYMENT SCREENSHOT TO ADMIN"
    },
    "BN": {
        "welcome": "👋 Swagotom {name}!\n\n🌐 Bhasha নির্বাচন korun:\n\n🔹 English for E\n🔸 Hindi for H\n🔸 Bengali for B",
        "lang_set": "✅ Bangla (Banglish) bhasha set hoye geche!",
        "ask_promo": "🎁 6-Digit Promo Code dain (ba 'SKIP' likhun):",
        "invalid_promo": "❌ Bhul Promo Code! Sothik 6-digit code dain ba 'SKIP' likhun:",
        "promo_applied": "🎉 Promo code apply hoye geche! Apni +5.4 IC Welcome Bonus peyechen!",
        "ask_username": "👋 Login korar jonno apnar Telegram username '@' diye shuru kore pathan:",
        "invalid_username": "⚠️ Username obosshoi '@' diye shuru hote hobe (jemon: @yourname):",
        "mismatch_username": "❌ Fake Login Detected!\n\nApnar deoya username ({input_user}) apnar asol Telegram username (@{real_user}) er sathe match korche na. Doya kore apnar nijer username dain!",
        "no_tg_username": "⚠️ Apnar Telegram account e kono username set kora nei!\n\nProthome Telegram Settings e giye username set korun, tarpor login korun.",
        "login_success": "✅ {username} hisebe safolyo bhabe login hoyeche!",
        "main_title": (
            "💎 VIP PROJECTS\n"
            "⚙️ VIP CONFIGS\n"
            "⚡ INSTANT DELIVERY\n"
            "🔒 SECURE PAYMENTS\n\n"
            "────────────────────────\n\n"
            "👤 USERNAME : {username}\n"
            "🆔 ID : {user_id}\n"
            "💰 BALANCE : {balance:.1f} IC\n"
            "🔱 EXCHANGE RATE : ₹1 INR = 1.2 IC\n"
            "💵 RATES: ₹10 = 12.0 IC | ₹20 = 24.0 IC\n\n"
            "────────────────────────\n\n"
            "🚀 SHURU KORTE BUY PROJECT BA CONFIG TAP KORUN!"
        ),
        "btn_buy_proj": "⭐ BUY PROJECT",
        "btn_buy_files": "⭐ BUY CONFIG",
        "btn_buy_mods": "⭐ BUY MOD APK'S",
        "btn_add_bal": "💳 ADD BALANCE",
        "btn_referral": "🎁 REFER & EARN",
        "btn_orders": "📦 YOUR ORDERS",
        "btn_channel": "📢 OFFICIAL CHANNEL",
        "btn_support": "📞 CUSTOMER SUPPORT",
        "btn_back": "⬅️ Main Menu te Phire Jan",
        "no_items": "⚠️ Ekhon kono {category} available nei.",
        "no_orders": "📦 Apni ekhono kono item korenni.",
        "orders_title": "📦 APNAR KHAREDA ORDERS:\nJekono somoy re-download korar jonno nicher button e tap korun!",
        "item_not_found": "❌ Item paoya jayni!",
        "not_enough_ic": "⚠️ Apnar kache porjapt IC balance nei!\nProyojon: {price} IC | Apnar Balance: {balance:.1f} IC\n\nDoya kore ADD BALANCE option diye balance jog korun.",
        "buy_success": "🎉 PURCHASE SUCCESSFUL!\n\n📦 Item: {name}\n💰 Deducted: {price} IC\n📦 Baki Balance: {new_balance:.1f} IC\n\nApnar file niche pathano holo! (15 min pore auto-delete hobe)",
        "add_bal_text": "💳 ADD BALANCE (MINIMUM ₹10 INR)\n\n🔱 Exchange Rate: ₹1 INR = 1.2 IC\n💵 RATES:\n• ₹10 INR = 12.0 IC\n• ₹20 INR = 24.0 IC\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba UPI ID te payment korun (Min ₹10).\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "support_text": "📞 CUSTOMER SUPPORT\n\nApnar kono prosno thakle ba payment/product niye sahajjo lagle nicher admin er sathe jogajog korun:\n\n👉 Admin Username: @{admin}",
        "channel_text": "📢 OFFICIAL CHANNEL\n\nRegular update, free config ebong notun project pete amader official channel join korun:\n\n👉 Channel Link: {channel}",
        "btn_chat_admin": "💬 Admin er sathe kotha bolun",
        "btn_visit_channel": "📢 Channel Visit korun",
        "pay_title": "💳 PAYMENT CHECKOUT (FAMPAY)\n\n📦 Item: {name}\n💰 Amount to Pay: {price} IC (₹{inr_price} INR)\n\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba FamPay ID te payment korun.\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "btn_send_ss": "📞 SEND PAYMENT SCREENSHOT TO ADMIN"
    }
}

def get_lang(user_id):
    return db.get("user_languages", {}).get(str(user_id), "EN")

def is_admin(user):
    if not user.username:
        return False
    return user.username.replace('@', '').strip().lower() == ADMIN_USERNAME.replace('@', '').strip().lower()

def is_banned(user):
    username = f"@{user.username}" if user.username else ""
    user_id = user.id
    banned_list = db.get("banned_users", [])
    return (username.lower() in [str(b).lower() for b in banned_list]) or (user_id in banned_list) or (str(user_id) in banned_list)

def schedule_file_deletion(chat_id, message_id):
    def delete_msg():
        time.sleep(900)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    threading.Thread(target=delete_msg, daemon=True).start()

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['toggle_bot'])
def admin_toggle_bot_command(message):
    global is_bot_active
    if not is_admin(message.from_user):
        return bot.reply_to(message, f"❌ Access Denied! Admin username is set to @{ADMIN_USERNAME}.")
    is_bot_active = not is_bot_active
    status = "ONLINE & ACTIVE ✅" if is_bot_active else "OFFLINE / MAINTENANCE ❌"
    bot.reply_to(message, f"🤖 Bot Status updated: {status}")

@bot.message_handler(commands=['ic'])
def admin_ic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /ic @username amount\nExample: /ic @BRUTALMOON 12.2")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format! Enter numbers only.")
    
    target_user_key = None
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        target_user_key = target_username.lower()
        db.setdefault("registered_users", {})[target_user_key] = target_username

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(current_bal + amount, 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ SUCCESS!\n\n👤 User: {target_username}\n➕ Added: {amount} IC\n💰 Total Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['deduct', 'minus'])
def admin_deduct_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /deduct @username amount\nExample: /deduct @BRUTALMOON 10.0")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format!")
    
    target_user_key = None
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        return bot.reply_to(message, f"❌ User {target_username} not found in registered users!")

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(max(0.0, current_bal - amount), 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ DEDUCTION SUCCESSFUL!\n\n👤 User: {target_username}\n➖ Deducted: {amount} IC\n💰 Remaining Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['totalic', 'sentic'])
def admin_totalic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    total_sent = sum(float(val) for val in db.get("user_balances", {}).values())
    bot.reply_to(message, f"📈 **TOTAL IC SENT TO USERS:** {total_sent:.1f} IC", parse_mode='Markdown')

@bot.message_handler(commands=['icuse'])
def admin_icuse_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    total = db.get("total_earnings", 0.0)
    bot.reply_to(message, f"📉 TOTAL IC SPENT BY USERS: {total:.1f} IC")

@bot.message_handler(commands=['upload'])
def admin_upload_start(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    msg = bot.reply_to(message, "📦 Enter Category:\n\nOptions: Projects, Files, or ModApks")
    bot.register_next_step_handler(msg, process_upload_category)

def process_upload_category(message):
    cat = message.text.strip()
    if cat not in ["Projects", "Files", "ModApks"]:
        msg = bot.reply_to(message, "⚠️ Invalid Category! Send Projects, Files, or ModApks:")
        bot.register_next_step_handler(msg, process_upload_category)
        return
    upload_temp[message.from_user.id] = {"category": cat}
    msg = bot.reply_to(message, f"✅ Category set to {cat}.\n\n👉 Now enter Item Name:")
    bot.register_next_step_handler(msg, process_upload_name)

def process_upload_name(message):
    name = message.text.strip()
    upload_temp[message.from_user.id]["name"] = nagla (Banglish) bhasha set hoye geche!",
        "ask_promo": "🎁 6-Digit Promo Code dain (ba 'SKIP' likhun):",
        "invalid_promo": "❌ Bhul Promo Code! Sothik 6-digit code dain ba 'SKIP' likhun:",
        "promo_applied": "🎉 Promo code apply hoye geche! Apni +5.4 IC Welcome Bonus peyechen!",
        "ask_username": "👋 Login korar jonno apnar Telegram username '@' diye shuru kore pathan:",
        "invalid_username": "⚠️ Username obosshoi '@' diye shuru hote hobe (jemon: @yourname):",
        "login_success": "✅ {username} hisebe safolyo bhabe login hoyeche!",
        "main_title": (
            "💎 VIP PROJECTS\n"
            "⚙️ VIP CONFIGS\n"
            "⚡ INSTANT DELIVERY\n"
            "🔒 SECURE PAYMENTS\n\n"
            "────────────────────────\n\n"
            "👤 USERNAME : {username}\n"
            "🆔 ID : {user_id}\n"
            "💰 BALANCE : {balance:.1f} IC\n"
            "🔱 EXCHANGE RATE : ₹1 INR = 1.2 IC\n"
            "💵 RATES: ₹10 = 12.0 IC | ₹20 = 24.0 IC\n\n"
            "────────────────────────\n\n"
            "🚀 SHURU KORTE BUY PROJECT BA CONFIG TAP KORUN!"
        ),
        "btn_buy_proj": "⭐ BUY PROJECT",
        "btn_buy_files": "⭐ BUY CONFIG",
        "btn_buy_mods": "⭐ BUY MOD APK'S",
        "btn_add_bal": "💳 ADD BALANCE",
        "btn_referral": "🎁 REFER & EARN",
        "btn_orders": "📦 YOUR ORDERS",
        "btn_channel": "📢 OFFICIAL CHANNEL",
        "btn_support": "📞 CUSTOMER SUPPORT",
        "btn_back": "⬅️ Main Menu te Phire Jan",
        "no_items": "⚠️ Ekhon kono {category} available nei.",
        "no_orders": "📦 Apni ekhono kono item korenni.",
        "orders_title": "📦 APNAR KHAREDA ORDERS:\nJekono somoy re-download korar jonno nicher button e tap korun!",
        "item_not_found": "❌ Item paoya jayni!",
        "not_enough_ic": "⚠️ Apnar kache porjapt IC balance nei!\nProyojon: {price} IC | Apnar Balance: {balance:.1f} IC\n\nDoya kore ADD BALANCE option diye balance jog korun.",
        "buy_success": "🎉 PURCHASE SUCCESSFUL!\n\n📦 Item: {name}\n💰 Deducted: {price} IC\n📦 Baki Balance: {new_balance:.1f} IC\n\nApnar file niche pathano holo! (15 min pore auto-delete hobe)",
        "add_bal_text": "💳 ADD BALANCE (MINIMUM ₹10 INR)\n\n🔱 Exchange Rate: ₹1 INR = 1.2 IC\n💵 RATES:\n• ₹10 INR = 12.0 IC\n• ₹20 INR = 24.0 IC\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba UPI ID te payment korun (Min ₹10).\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "support_text": "📞 CUSTOMER SUPPORT\n\nApnar kono prosno thakle ba payment/product niye sahajjo lagle nicher admin er sathe jogajog korun:\n\n👉 Admin Username: @{admin}",
        "channel_text": "📢 OFFICIAL CHANNEL\n\nRegular update, free config ebong notun project pete amader official channel join korun:\n\n👉 Channel Link: {channel}",
        "btn_chat_admin": "💬 Admin er sathe kotha bolun",
        "btn_visit_channel": "📢 Channel Visit korun",
        "pay_title": "💳 PAYMENT CHECKOUT (FAMPAY)\n\n📦 Item: {name}\n💰 Amount to Pay: {price} IC (₹{inr_price} INR)\n\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba FamPay ID te payment korun.\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "btn_send_ss": "📞 SEND PAYMENT SCREENSHOT TO ADMIN"
    }
}

def get_lang(user_id):
    return db.get("user_languages", {}).get(str(user_id), "EN")

def is_admin(user):
    if not user.username:
        return False
    return user.username.replace('@', '').strip().lower() == ADMIN_USERNAME.replace('@', '').strip().lower()

def is_banned(user):
    username = f"@{user.username}" if user.username else ""
    user_id = user.id
    banned_list = db.get("banned_users", [])
    return (username.lower() in [str(b).lower() for b in banned_list]) or (user_id in banned_list) or (str(user_id) in banned_list)

def schedule_file_deletion(chat_id, message_id):
    def delete_msg():
        time.sleep(900)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    threading.Thread(target=delete_msg, daemon=True).start()

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['toggle_bot'])
def admin_toggle_bot_command(message):
    global is_bot_active
    if not is_admin(message.from_user):
        return bot.reply_to(message, f"❌ Access Denied! Admin username is set to @{ADMIN_USERNAME}.")
    is_bot_active = not is_bot_active
    status = "ONLINE & ACTIVE ✅" if is_bot_active else "OFFLINE / MAINTENANCE ❌"
    bot.reply_to(message, f"🤖 Bot Status updated: {status}")

@bot.message_handler(commands=['ic'])
def admin_ic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /ic @username amount\nExample: /ic @BRUTALMOON 12.2")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format! Enter numbers only.")
    
    target_user_key = None
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        target_user_key = target_username.lower()
        db.setdefault("registered_users", {})[target_user_key] = target_username

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(current_bal + amount, 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ SUCCESS!\n\n👤 User: {target_username}\n➕ Added: {amount} IC\n💰 Total Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['deduct', 'minus'])
def admin_deduct_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /deduct @username amount\nExample: /deduct @BRUTALMOON 10.0")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format!")
    
    target_user_key = None
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        return bot.reply_to(message, f"❌ User {target_username} not found in registered users!")

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(max(0.0, current_bal - amount), 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ DEDUCTION SUCCESSFUL!\n\n👤 User: {target_username}\n➖ Deducted: {amount} IC\n💰 Remaining Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['totalic', 'sentic'])
def admin_totalic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    total_sent = sum(float(val) for val in db.get("user_balances", {}).values())
    bot.reply_to(message, f"📈 **TOTAL IC SENT TO USERS:** {total_sent:.1f} IC", parse_mode='Markdown')

@bot.message_handler(commands=['icuse'])
def admin_icuse_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    total = db.get("total_earnings", 0.0)
    bot.reply_to(message, f"📉 TOTAL IC SPENT BY USERS: {total:.1f} IC")

@bot.message_handler(commands=['upload'])
def admin_upload_start(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ Access Denied!")
    msg = bot.reply_to(message, "📦 Enter Category:\n\nOptions: Projects, Files, or ModApks")
    bot.register_next_step_handler(msg, process_upload_category)

def process_upload_category(message):
    cat = message.text.strip()
    if cat not in ["Projects", "Files", "ModApks"]:
        msg = bot.reply_to(message, "⚠️ Invalid Category! Send Projects, Files, or ModApks:")
        bot.register_next_step_handler(msg, process_upload_category)
        return
    upload_temp[message.from_user.id] = {"category": cat}
    msg = bot.reply_to(message, f"✅ Category set to {cat}.\n\n👉 Now enter Item Name:")
    bot.register_next_step_handler(msg, process_upload_name)

def process_upload_name(message):
    name = message.text.strip()
    upload_temp[message.from_user.id]["name"] = name
    msg = bot.reply_to(message, "👉 Now enter Price in IC (e.g., 10.0):")
    bot.register_next_step_handler(msg, process_upload_price)

def process_upload_price(message):
    try:
        price = float(message.text.strip())
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Invalid Price! Enter a valid number:")
        bot.register_next_step_handler(msg, process_upload_price)
        return
    upload_temp[message.from_user.id]["price"] = price
    msg = bot.reply_to(message, "👉 Now send the Telegram File_ID or Download Link/Text to be delivered upon purchase:")
    bot.register_next_step_handler(msg, process_upload_file)

def process_upload_file(message):
    file_id = message.text.strip() if message.text else (message.document.file_id if message.document else None)
    if not file_id:
        msg = bot.reply_to(message, "⚠️ Invalid input! Please send File_ID or text link:")
        bot.register_next_step_handler(msg, process_upload_file)
        return

    data = upload_temp[message.from_user.id]
    cat ,
        "ask_promo": "🎁 6-Digit Promo Code dain (ba 'SKIP' likhun):",
        "invalid_promo": "❌ Bhul Promo Code! Sothik 6-digit code dain ba 'SKIP' likhun:",
        "promo_applied": "🎉 Promo code apply hoye geche! Apni +5.4 IC Welcome Bonus peyechen!",
        "ask_username": "👋 Login korar jonno apnar Telegram username '@' diye shuru kore pathan:",
        "invalid_username": "⚠️ Username obosshoi '@' diye shuru hote hobe (jemon: @yourname):",
        "login_success": "✅ {username} hisebe safolyo bhabe login hoyeche!",
        "main_title": (
            "💎 VIP PROJECTS\n"
            "⚙️ VIP CONFIGS\n"
            "⚡ INSTANT DELIVERY\n"
            "🔒 SECURE PAYMENTS\n\n"
            "────────────────────────\n\n"
            "👤 USERNAME : {username}\n"
            "🆔 ID : {user_id}\n"
            "💰 BALANCE : {balance:.1f} IC\n"
            "🔱 EXCHANGE RATE : ₹1 INR = 1.2 IC\n"
            "💵 RATES: ₹10 = 12.0 IC | ₹20 = 24.0 IC\n\n"
            "────────────────────────\n\n"
            "🚀 SHURU KORTE BUY PROJECT BA CONFIG TAP KORUN!"
        ),
        "btn_buy_proj": "⭐ BUY PROJECT",
        "btn_buy_files": "⭐ BUY CONFIG",
        "btn_buy_mods": "⭐ BUY MOD APK'S",
        "btn_add_bal": "💳 ADD BALANCE",
        "btn_referral": "🎁 REFER & EARN",
        "btn_orders": "📦 YOUR ORDERS",
        "btn_channel": "📢 OFFICIAL CHANNEL",
        "btn_support": "📞 CUSTOMER SUPPORT",
        "btn_back": "⬅️ Main Menu te Phire Jan",
        "no_items": "⚠️ Ekhon kono {category} available nei.",
        "no_orders": "📦 Apni ekhono kono item korenni.",
        "orders_title": "📦 APNAR KHAREDA ORDERS:\nJekono somoy re-download korar jonno nicher button e tap korun!",
        "item_not_found": "❌ Item paoya jayni!",
        "not_enough_ic": "⚠️ Apnar kache porjapt IC balance nei!\nProyojon: {price} IC | Apnar Balance: {balance:.1f} IC\n\nDoya kore ADD BALANCE option diye balance jog korun.",
        "buy_success": "🎉 PURCHASE SUCCESSFUL!\n\n📦 Item: {name}\n💰 Deducted: {price} IC\n📦 Baki Balance: {new_balance:.1f} IC\n\nApnar file niche pathano holo! (15 min pore auto-delete hobe)",
        "add_bal_text": "💳 ADD BALANCE (MINIMUM ₹10 INR)\n\n🔱 Exchange Rate: ₹1 INR = 1.2 IC\n💵 RATES:\n• ₹10 INR = 12.0 IC\n• ₹20 INR = 24.0 IC\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba UPI ID te payment korun (Min ₹10).\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "support_text": "📞 CUSTOMER SUPPORT\n\nApnar kono prosno thakle ba payment/product niye sahajjo lagle nicher admin er sathe jogajog korun:\n\n👉 Admin Username: @{admin}",
        "channel_text": "📢 OFFICIAL CHANNEL\n\nRegular update, free config ebong notun project pete amader official channel join korun:\n\n👉 Channel Link: {channel}",
        "btn_chat_admin": "💬 Admin er sathe kotha bolun",
        "btn_visit_channel": "📢 Channel Visit korun",
        "pay_title": "💳 PAYMENT CHECKOUT (FAMPAY)\n\n📦 Item: {name}\n💰 Amount to Pay: {price} IC (₹{inr_price} INR)\n\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba FamPay ID te payment korun.\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "btn_send_ss": "📞 SEND PAYMENT SCREENSHOT TO ADMIN"
    }
}

def get_lang(user_id):
    return db.get("user_languages", {}).get(str(user_id), "EN")

def is_admin(user):
    return user.username == ADMIN_USERNAME

def is_banned(user):
    username = f"@{user.username}" if user.username else ""
    user_id = user.id
    banned_list = db.get("banned_users", [])
    return (username.lower() in [str(b).lower() for b in banned_list]) or (user_id in banned_list) or (str(user_id) in banned_list)

def schedule_file_deletion(chat_id, message_id):
    def delete_msg():
        time.sleep(900)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    threading.Thread(target=delete_msg, daemon=True).start()

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['toggle_bot'])
def admin_toggle_bot_command(message):
    global is_bot_active
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    is_bot_active = not is_bot_active
    status = "ONLINE & ACTIVE ✅" if is_bot_active else "OFFLINE / MAINTENANCE ❌"
    bot.reply_to(message, f"🤖 Bot Status has been toggled to: {status}")

@bot.message_handler(commands=['ic'])
def admin_ic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /ic @username amount\nExample: /ic @BRUTALMOON 12.2")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format! Enter numbers only.")
    
    target_user_key = None
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        target_user_key = target_username.lower()
        db.setdefault("registered_users", {})[target_user_key] = target_username

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(current_bal + amount, 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ SUCCESS!\n\n👤 User: {target_username}\n➕ Added: {amount} IC\n💰 Total Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['deduct', 'minus'])
def admin_deduct_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /deduct @username amount\nExample: /deduct @BRUTALMOON 10.0")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format! Enter numbers only.")
    
    target_user_key = None
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        return bot.reply_to(message, f"❌ User {target_username} not found in database registered users!")

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(max(0.0, current_bal - amount), 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ DEDUCTED SUCCESSFUL!\n\n👤 User: {target_username}\n➖ Minus: {amount} IC\n💰 Remaining Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['totalic', 'sentic'])
def admin_totalic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    total_sent = sum(float(val) for val in db.get("user_balances", {}).values())
    bot.reply_to(message, f"📈 **TOTAL IC SENT TO USERS:** {total_sent:.1f} IC", parse_mode='Markdown')

@bot.message_handler(commands=['icuse'])
def admin_icuse_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    total = db.get("total_earnings", 0.0)
    bot.reply_to(message, f"📉 TOTAL IC SPENT BY USERS: {total:.1f} IC")

@bot.message_handler(commands=['upload'])
def admin_upload_start(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    msg = bot.reply_to(message, "📦 Enter Category:\n\nOptions: Projects, Files, or ModApks")
    bot.register_next_step_handler(msg, process_upload_category)

def process_upload_category(message):
    cat = message.text.strip()
    if cat not in ["Projects", "Files", "ModApks"]:
        msg = bot.reply_to(message, "⚠️ Invalid Category! Send Projects, Files, or ModApks:")
        bot.register_next_step_handler(msg, process_upload_category)
        return
    upload_temp[message.from_user.id] = {"category": cat}
    msg = bot.reply_to(message, f"✅ Category set to {cat}.\n\n👉 Now enter Item Name:")
    bot.register_next_step_handler(msg, process_upload_name)

def process_upload_name(message):
    name = message.text.strip()
    upload_temp[message.from_user.id]["name"] = name
    msg = bot.reply_to(message, "👉 Now enter Price in IC (e.g., 10.0):")
    bot.register_next_step_handler(msg, process_upload_price)

def process_upload_price(message):
    try:
        price = float(message.text.strip())
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Invalid Price! Enter a valid number:")
        bot.register_next_step_handler(msg, process_upload_price)
        return
    upload_temp[message.from_user.id]["price"] = price
    msg = bot.reply_to(message, "👉 Now send the Telegram File_ID or Download Link/Text to be delivered upon purchase:")
    bot.register_next_step_handler(msg, process_upload_file)

def process_upload_file(message):
    file_id = message.text.strip() if message.text else (message.document.file_id if message.document else None)
    if not file_id:
        msg = bot.reply_to(message, "⚠️ Invalid input! Please send File_ID or text link:")
        bot.register_next_step_handler(msg, process_upload_file)
        return

    data = upload_temp[message.from_user.id]
    cat = data["category"]
    cat_key = "projects" if cat == "Projects" else ("files" if cat == "Files" else "moe (jemon: @yourname):",
        "login_success": "✅ {username} hisebe safolyo bhabe login hoyeche!",
        "main_title": (
            "💎 VIP PROJECTS\n"
            "⚙️ VIP CONFIGS\n"
            "⚡ INSTANT DELIVERY\n"
            "🔒 SECURE PAYMENTS\n\n"
            "────────────────────────\n\n"
            "👤 USERNAME : {username}\n"
            "🆔 ID : {user_id}\n"
            "💰 BALANCE : {balance:.1f} IC\n"
            "🔱 EXCHANGE RATE : ₹1 INR = 1.2 IC\n"
            "💵 RATES: ₹10 = 12.0 IC | ₹20 = 24.0 IC\n\n"
            "────────────────────────\n\n"
            "🚀 SHURU KORTE BUY PROJECT BA CONFIG TAP KORUN!"
        ),
        "btn_buy_proj": "⭐ BUY PROJECT",
        "btn_buy_files": "⭐ BUY CONFIG",
        "btn_buy_mods": "⭐ BUY MOD APK'S",
        "btn_add_bal": "💳 ADD BALANCE",
        "btn_referral": "🎁 REFER & EARN",
        "btn_orders": "📦 YOUR ORDERS",
        "btn_channel": "📢 OFFICIAL CHANNEL",
        "btn_support": "📞 CUSTOMER SUPPORT",
        "btn_back": "⬅️ Main Menu te Phire Jan",
        "no_items": "⚠️ Ekhon kono {category} available nei.",
        "no_orders": "📦 Apni ekhono kono item korenni.",
        "orders_title": "📦 APNAR KHAREDA ORDERS:\nJekono somoy re-download korar jonno nicher button e tap korun!",
        "item_not_found": "❌ Item paoya jayni!",
        "not_enough_ic": "⚠️ Apnar kache porjapt IC balance nei!\nProyojon: {price} IC | Apnar Balance: {balance:.1f} IC\n\nDoya kore ADD BALANCE option diye balance jog korun.",
        "buy_success": "🎉 PURCHASE SUCCESSFUL!\n\n📦 Item: {name}\n💰 Deducted: {price} IC\n📦 Baki Balance: {new_balance:.1f} IC\n\nApnar file niche pathano holo! (15 min pore auto-delete hobe)",
        "add_bal_text": "💳 ADD BALANCE (MINIMUM ₹10 INR)\n\n🔱 Exchange Rate: ₹1 INR = 1.2 IC\n💵 RATES:\n• ₹10 INR = 12.0 IC\n• ₹20 INR = 24.0 IC\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba UPI ID te payment korun (Min ₹10).\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "support_text": "📞 CUSTOMER SUPPORT\n\nApnar kono prosno thakle ba payment/product niye sahajjo lagle nicher admin er sathe jogajog korun:\n\n👉 Admin Username: @{admin}",
        "channel_text": "📢 OFFICIAL CHANNEL\n\nRegular update, free config ebong notun project pete amader official channel join korun:\n\n👉 Channel Link: {channel}",
        "btn_chat_admin": "💬 Admin er sathe kotha bolun",
        "btn_visit_channel": "📢 Channel Visit korun",
        "pay_title": "💳 PAYMENT CHECKOUT (FAMPAY)\n\n📦 Item: {name}\n💰 Amount to Pay: {price} IC (₹{inr_price} INR)\n\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba FamPay ID te payment korun.\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "btn_send_ss": "📞 SEND PAYMENT SCREENSHOT TO ADMIN"
    }
}

def get_lang(user_id):
    return db.get("user_languages", {}).get(str(user_id), "EN")

def is_admin(user):
    return user.username == ADMIN_USERNAME

def is_banned(user):
    username = f"@{user.username}" if user.username else ""
    user_id = user.id
    banned_list = db.get("banned_users", [])
    return (username.lower() in [str(b).lower() for b in banned_list]) or (user_id in banned_list) or (str(user_id) in banned_list)

def schedule_file_deletion(chat_id, message_id):
    def delete_msg():
        time.sleep(900)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    threading.Thread(target=delete_msg, daemon=True).start()

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['ic'])
def admin_ic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /ic @username amount\nExample: /ic @BRUTALMOON 12.2")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format! Enter numbers only.")
    
    target_user_key = None
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        target_user_key = target_username.lower()
        db.setdefault("registered_users", {})[target_user_key] = target_username

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(current_bal + amount, 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ SUCCESS!\n\n👤 User: {target_username}\n➕ Added: {amount} IC\n💰 Total Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['totalic', 'sentic'])
def admin_totalic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    total_sent = sum(float(val) for val in db.get("user_balances", {}).values())
    bot.reply_to(message, f"📈 **TOTAL IC SENT TO USERS:** {total_sent:.1f} IC", parse_mode='Markdown')

@bot.message_handler(commands=['icuse'])
def admin_icuse_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    total = db.get("total_earnings", 0.0)
    bot.reply_to(message, f"📉 TOTAL IC SPENT BY USERS: {total:.1f} IC")

@bot.message_handler(commands=['upload'])
def admin_upload_start(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    msg = bot.reply_to(message, "📦 Enter Category:\n\nOptions: Projects, Files, or ModApks")
    bot.register_next_step_handler(msg, process_upload_category)

def process_upload_category(message):
    cat = message.text.strip()
    if cat not in ["Projects", "Files", "ModApks"]:
        msg = bot.reply_to(message, "⚠️ Invalid Category! Send Projects, Files, or ModApks:")
        bot.register_next_step_handler(msg, process_upload_category)
        return
    upload_temp[message.from_user.id] = {"category": cat}
    msg = bot.reply_to(message, f"✅ Category set to {cat}.\n\n👉 Now enter Item Name:")
    bot.register_next_step_handler(msg, process_upload_name)

def process_upload_name(message):
    name = message.text.strip()
    upload_temp[message.from_user.id]["name"] = name
    msg = bot.reply_to(message, "👉 Now enter Price in IC (e.g., 10.0):")
    bot.register_next_step_handler(msg, process_upload_price)

def process_upload_price(message):
    try:
        price = float(message.text.strip())
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Invalid Price! Enter a valid number:")
        bot.register_next_step_handler(msg, process_upload_price)
        return
    upload_temp[message.from_user.id]["price"] = price
    msg = bot.reply_to(message, "👉 Now send the Telegram File_ID or Download Link/Text to be delivered upon purchase:")
    bot.register_next_step_handler(msg, process_upload_file)

def process_upload_file(message):
    file_id = message.text.strip() if message.text else (message.document.file_id if message.document else None)
    if not file_id:
        msg = bot.reply_to(message, "⚠️ Invalid input! Please send File_ID or text link:")
        bot.register_next_step_handler(msg, process_upload_file)
        return

    data = upload_temp[message.from_user.id]
    cat = data["category"]
    cat_key = "projects" if cat == "Projects" else ("files" if cat == "Files" else "mod_apks")
    
    item_id = str(len(db.get(cat_key, [])) + 1)
    new_item = {
        "id": item_id,
        "name": data["name"],
        "price": data["price"],
        "file_id": file_id
    }
    
    db.setdefault(cat_key, []).append(new_item)
    save_db()
    if message.from_user.id in upload_temp:
        del upload_temp[message.from_user.id]
    
    bot.reply_to(message, f"🎉 Successfully Uploaded!\n\n📦 Category: {cat}\n📛 Name: {new_item['name']}\n💰 Price: {data['price']} IC\n📄 File Attached!")

@bot.message_handler(commands=['delete'])
def admin_delete_start(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    text = "🗑 CURRENT AVAILABLE ITEMS:\n\n"
    has_items = False
    for cat_name, cat_key in [("Projects", "projects"), ("Files", "files"), ("ModApks", "mod_apks")]:
        items = db.get(cat_key, [])
        if items:
            has_items = True
            text += f"📂 {cat_name}:\n"
            for item in items:
                text += f"• {item['name']} ({item['price']} IC)\n"
            text += "\n"
    if not has_items:
        return bot.reply_to(message, "⚠️ No items available in database to delete!")
    msg = bot.reply_to(message, text + "👉 Send the exact NAME of the Project / File / ModApk to delete:")
    bot.register_next_step_handler(msg, process_delete_item_by_name)

def process_delete_item_by_name(message):
    item_name = message.text.strip()
    deleted_item = None
    for cat_key in ["projects", "files", "mod_apks"]:
        for item in list(db.get(cat_key, [])):
            if item["name"].lower() == item_name.lower():
                deleted_item = item["name"]
                db[cat_key].remove(item)
                break
        if deleted_item:
            break
    if deleted_item:
        save_db()
        bot.reply_to(message, f"✅ {deleted_item} has been deleted successfully from database!")
    else:
        bot.reply_to(message, f"❌ Item named {item_name} not found!")

@bot.message_handler(commands=['ban'])
def admin_ban_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    parts = message.text.strip().split()
    if len(parnno apnar Telegram username '@' diye shuru kore pathan:",
        "invalid_username": "⚠️ Username obosshoi '@' diye shuru hote hobe (jemon: @yourname):",
        "login_success": "✅ {username} hisebe safolyo bhabe login hoyeche!",
        "main_title": (
            "💎 VIP PROJECTS\n"
            "⚙️ VIP CONFIGS\n"
            "⚡ INSTANT DELIVERY\n"
            "🔒 SECURE PAYMENTS\n\n"
            "────────────────────────\n\n"
            "👤 USERNAME : {username}\n"
            "🆔 ID : {user_id}\n"
            "💰 BALANCE : {balance:.1f} IC\n"
            "🔱 EXCHANGE RATE : ₹1 INR = 1.2 IC\n"
            "💵 RATES: ₹10 = 12.0 IC | ₹20 = 24.0 IC\n\n"
            "────────────────────────\n\n"
            "🚀 SHURU KORTE BUY PROJECT BA CONFIG TAP KORUN!"
        ),
        "btn_buy_proj": "⭐ BUY PROJECT",
        "btn_buy_files": "⭐ BUY CONFIG",
        "btn_buy_mods": "⭐ BUY MOD APK'S",
        "btn_add_bal": "💳 ADD BALANCE",
        "btn_referral": "🎁 REFER & EARN",
        "btn_orders": "📦 YOUR ORDERS",
        "btn_channel": "📢 OFFICIAL CHANNEL",
        "btn_support": "📞 CUSTOMER SUPPORT",
        "btn_back": "⬅️ Main Menu te Phire Jan",
        "no_items": "⚠️ Ekhon kono {category} available nei.",
        "no_orders": "📦 Apni ekhono kono item korenni.",
        "orders_title": "📦 APNAR KHAREDA ORDERS:\nJekono somoy re-download korar jonno nicher button e tap korun!",
        "item_not_found": "❌ Item paoya jayni!",
        "not_enough_ic": "⚠️ Apnar kache porjapt IC balance nei!\nProyojon: {price} IC | Apnar Balance: {balance:.1f} IC\n\nDoya kore ADD BALANCE option diye balance jog korun.",
        "buy_success": "🎉 PURCHASE SUCCESSFUL!\n\n📦 Item: {name}\n💰 Deducted: {price} IC\n📦 Baki Balance: {new_balance:.1f} IC\n\nApnar file niche pathano holo! (15 min pore auto-delete hobe)",
        "add_bal_text": "💳 ADD BALANCE (MINIMUM ₹10 INR)\n\n🔱 Exchange Rate: ₹1 INR = 1.2 IC\n💵 RATES:\n• ₹10 INR = 12.0 IC\n• ₹20 INR = 24.0 IC\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba UPI ID te payment korun (Min ₹10).\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "support_text": "📞 CUSTOMER SUPPORT\n\nApnar kono prosno thakle ba payment/product niye sahajjo lagle nicher admin er sathe jogajog korun:\n\n👉 Admin Username: @{admin}",
        "channel_text": "📢 OFFICIAL CHANNEL\n\nRegular update, free config ebong notun project pete amader official channel join korun:\n\n👉 Channel Link: {channel}",
        "btn_chat_admin": "💬 Admin er sathe kotha bolun",
        "btn_visit_channel": "📢 Channel Visit korun",
        "pay_title": "💳 PAYMENT CHECKOUT (FAMPAY)\n\n📦 Item: {name}\n💰 Amount to Pay: {price} IC (₹{inr_price} INR)\n\n📱 FamPay UPI ID: {upi}\n\n👉 Uporer QR code scan korun athoba FamPay ID te payment korun.\nAfter payment, send payment screenshot to admin for ic balance top-up!",
        "btn_send_ss": "📞 SEND PAYMENT SCREENSHOT TO ADMIN"
    }
}

def get_lang(user_id):
    return db.get("user_languages", {}).get(str(user_id), "EN")

def is_admin(user):
    return user.username == ADMIN_USERNAME

def is_banned(user):
    username = f"@{user.username}" if user.username else ""
    user_id = user.id
    banned_list = db.get("banned_users", [])
    return (username.lower() in [str(b).lower() for b in banned_list]) or (user_id in banned_list) or (str(user_id) in banned_list)

def schedule_file_deletion(chat_id, message_id):
    def delete_msg():
        time.sleep(900)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
    threading.Thread(target=delete_msg, daemon=True).start()

# --- ADMIN COMMANDS ---

@bot.message_handler(commands=['ic'])
def admin_ic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    parts = message.text.strip().split()
    if len(parts) != 3:
        return bot.reply_to(message, "⚠️ Usage: /ic @username amount\nExample: /ic @BRUTALMOON 12.2")
    
    target_username = parts[1].strip()
    if not target_username.startswith('@'):
        target_username = '@' + target_username
        
    try:
        amount = float(parts[2])
    except ValueError:
        return bot.reply_to(message, "⚠️ Invalid amount format! Enter numbers only.")
    
    target_user_key = None
    
    for uid, uname in db.get("registered_users", {}).items():
        if uname.lower() == target_username.lower():
            target_user_key = uid
            break
            
    if not target_user_key:
        target_user_key = target_username.lower()
        db.setdefault("registered_users", {})[target_user_key] = target_username

    current_bal = float(db.get("user_balances", {}).get(target_user_key, 0.0))
    new_bal = round(current_bal + amount, 1)
    
    db.setdefault("user_balances", {})[target_user_key] = new_bal
    save_db()
    
    reply_text = f"✅ SUCCESS!\n\n👤 User: {target_username}\n➕ Added: {amount} IC\n💰 Total Balance: {new_bal:.1f} IC"
    bot.reply_to(message, reply_text)

@bot.message_handler(commands=['totalic', 'sentic'])
def admin_totalic_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    total_sent = sum(float(val) for val in db.get("user_balances", {}).values())
    bot.reply_to(message, f"📈 **TOTAL IC SENT TO USERS:** {total_sent:.1f} IC", parse_mode='Markdown')

@bot.message_handler(commands=['icuse'])
def admin_icuse_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    total = db.get("total_earnings", 0.0)
    bot.reply_to(message, f"📉 TOTAL IC SPENT BY USERS: {total:.1f} IC")

@bot.message_handler(commands=['upload'])
def admin_upload_start(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    msg = bot.reply_to(message, "📦 Enter Category:\n\nOptions: Projects, Files, or ModApks")
    bot.register_next_step_handler(msg, process_upload_category)

def process_upload_category(message):
    cat = message.text.strip()
    if cat not in ["Projects", "Files", "ModApks"]:
        msg = bot.reply_to(message, "⚠️ Invalid Category! Send Projects, Files, or ModApks:")
        bot.register_next_step_handler(msg, process_upload_category)
        return
    
    upload_temp[message.from_user.id] = {"category": cat}
    msg = bot.reply_to(message, f"✅ Category set to {cat}.\n\n👉 Now enter Item Name:")
    bot.register_next_step_handler(msg, process_upload_name)

def process_upload_name(message):
    name = message.text.strip()
    upload_temp[message.from_user.id]["name"] = name
    msg = bot.reply_to(message, "👉 Now enter Price in IC (e.g., 10.0):")
    bot.register_next_step_handler(msg, process_upload_price)

def process_upload_price(message):
    try:
        price = float(message.text.strip())
    except ValueError:
        msg = bot.reply_to(message, "⚠️ Invalid Price! Enter a valid number:")
        bot.register_next_step_handler(msg, process_upload_price)
        return
    
    upload_temp[message.from_user.id]["price"] = price
    msg = bot.reply_to(message, "👉 Now send the Telegram File_ID or Download Link/Text to be delivered upon purchase:")
    bot.register_next_step_handler(msg, process_upload_file)

def process_upload_file(message):
    file_id = message.text.strip() if message.text else (message.document.file_id if message.document else None)
    
    if not file_id:
        msg = bot.reply_to(message, "⚠️ Invalid input! Please send File_ID or text link:")
        bot.register_next_step_handler(msg, process_upload_file)
        return

    data = upload_temp[message.from_user.id]
    cat = data["category"]
    cat_key = "projects" if cat == "Projects" else ("files" if cat == "Files" else "mod_apks")
    
    item_id = str(len(db[cat_key]) + 1)
    new_item = {
        "id": item_id,
        "name": data["name"],
        "price": data["price"],
        "file_id": file_id
    }
    
    db[cat_key].append(new_item)
    save_db()
    del upload_temp[message.from_user.id]
    
    bot.reply_to(message, f"🎉 Successfully Uploaded!\n\n📦 Category: {cat}\n📛 Name: {new_item['name']}\n💰 Price: {data['price']} IC\n📄 File Attached!")

@bot.message_handler(commands=['delete'])
def admin_delete_start(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    text = "🗑 CURRENT AVAILABLE ITEMS:\n\n"
    has_items = False
    
    for cat_name, cat_key in [("Projects", "projects"), ("Files", "files"), ("ModApks", "mod_apks")]:
        items = db.get(cat_key, [])
        if items:
            has_items = True
            text += f"📂 {cat_name}:\n"
            for item in items:
                text += f"• {item['name']} ({item['price']} IC)\n"
            text += "\n"
            
    if not has_items:
        return bot.reply_to(message, "⚠️ No items available in database to delete!")
        
    msg = bot.reply_to(message, text + "👉 Send the exact NAME of the Project / File / ModApk to delete:")
    bot.register_next_step_handler(msg, process_delete_item_by_name)

def process_delete_item_by_name(message):
    item_name = message.text.strip()
    deleted_item = None
    
    for cat_key in ["projects", "files", "mod_apks"]:
        for item in list(db[cat_key]):
            if item["name"].lower() == item_name.lower():
                deleted_item = item["name"]
                db[cat_key].remove(item)
                break
        if deleted_item:
            break
                
    if deleted_item:
        save_db()
        bot.reply_to(message, f"✅ {deleted_item} has been deleted successfully from database!")
    else:
        bot.reply_to(message, f"❌ Item named {item_name} not found!")

@bot.message_handler(commands=['ban'])
def admin_ban_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    parts = message.text.strip().split()
    if len(parts) != 2:
        return bot.reply_to(message, "⚠️ Usage: /ban @username or /ban user_id\nExample: /ban @BRUTALMOON")
    
    target = parts[1]
    if target not in db["banned_users"]:
        db["banned_users"].append(target)
        save_db()
        bot.reply_to(message, f"🚫 User {target} has been BANNED successfully!")
    else:
        bot.reply_to(message, f"⚠️ User {target} is already banned!")

@bot.message_handler(commands=['unban'])
def admin_unban_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    parts = message.text.strip().split()
    if len(parts) != 2:
        return bot.reply_to(message, "⚠️ Usage: /unban @username or /unban user_id\nExample: /unban @BRUTALMOON")
    
    target = parts[1]
    if target in db["banned_users"]:
        db["banned_users"].remove(target)
        save_db()
        bot.reply_to(message, f"✅ User {target} has been UNBANNED successfully!")
    else:
        bot.reply_to(message, f"⚠️ User {target} is not in banned list!")

@bot.message_handler(commands=['users'])
def admin_users_command(message):
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    count = len(db.get("registered_users", {}))
    bot.reply_to(message, f"👥 Total Registered Users: {count}")

@bot.message_handler(commands=['toggle_monetization'])
def admin_toggle_monetization(message):
    global is_monetization_on
    if not is_admin(message.from_user):
        return bot.reply_to(message, "❌ You are not authorized.")
    
    is_monetization_on = not is_monetization_on
    status = "ON ✅" if is_monetization_on else "OFF ❌"
    bot.reply_to(message, f"⚙️ Monetization is now: {status}")

# --- GENERAL USER HANDLERS ---

@bot.message_handler(content_types=['document', 'audio', 'video', 'photo'])
def get_file_id(message):
    if is_admin(message.from_user):
        file_id = None
        if message.document:
            file_id = message.document.file_id
        elif message.video:
            file_id = message.video.file_id
        elif message.audio:
            file_id = message.audio.file_id
        elif message.photo:
            file_id = message.photo[-1].file_id
        
        if file_id:
            bot.reply_to(message, f"📄 File ID:\n<code>{file_id}</code>", parse_mode='HTML')

@bot.message_handler(commands=['start'])
def start_handler(message):
    if is_banned(message.from_user):
        return bot.reply_to(message, "❌ You are banned from using this bot.")
    
    parts = message.text.strip().split()
    if len(parts) > 1:
        ref_code = parts[1].strip().upper()
        user_temp_ref[message.from_user.id] = ref_code

    msg_text = TEXTS["EN"]["welcome"].format(name=message.from_user.first_name)
    msg = bot.reply_to(message, msg_text)
    bot.register_next_step_handler(msg, process_language_choice)

def process_language_choice(message):
    if is_banned(message.from_user):
        return bot.reply_to(message, "❌ You are banned from using this bot.")
        
    user_id_str = str(message.from_user.id)
    choice = message.text.strip().upper()
    
    if choice == 'E':
        lang = "EN"
    elif choice == 'H':
        lang = "HI"
    elif choice == 'B':
        lang = "BN"
    else:
        msg = bot.reply_to(message, "⚠️ Invalid input! Please send:\n\nEnglish for E\nHindi for H\nBengali for B")
        bot.register_next_step_handler(msg, process_language_choice)
        return

    db["user_languages"][user_id_str] = lang
    save_db()
    
    bot.reply_to(message, TEXTS[lang]["lang_set"])

    if user_id_str not in db.get("registered_users", {}):
        passed_ref = user_temp_ref.get(message.from_user.id, "")
        if passed_ref:
            process_promo_code_input(message, passed_ref)
        else:
            msg = bot.reply_to(message, TEXTS[lang]["ask_promo"])
            bot.register_next_step_handler(msg, process_promo_step)
        return
    
    show_main_menu(message.chat.id, message.from_user.id)

def process_promo_step(message):
    input_text = message.text.strip()
    process_promo_code_input(message, input_text)

def process_promo_code_input(message, input_code):
    user_id_str = str(message.from_user.id)
    lang = get_lang(message.from_user.id)
    code = input_code.upper()

    if code == 'SKIP':
        msg = bot.reply_to(message, TEXTS[lang]["ask_username"])
        bot.register_next_step_handler(msg, save_username)
        return

    if len(code) == 6 and code in db.get("promo_code_map", {}):
        referrer_id = db["promo_code_map"][code]
        if referrer_id != user_id_str:
            db.setdefault("referred_by", {})[user_id_str] = referrer_id
            
            # New User gets +5.4 IC Bonus
            current_bal = float(db.get("user_balances", {}).get(user_id_str, 0.0))
            db.setdefault("user_balances", {})[user_id_str] = round(current_bal + 5.4, 1)
            
            # Referrer gets +6.0 IC Bonus for signup
            ref_bal = float(db.get("user_balances", {}).get(referrer_id, 0.0))
            db["user_balances"][referrer_id] = round(ref_bal + 6.0, 1)
            
            current_ref_earned = float(db.get("user_ref_earnings", {}).get(referrer_id, 0.0))
            db.setdefault("user_ref_earnings", {})[referrer_id] = round(current_ref_earned + 6.0, 1)

            save_db()
            bot.reply_to(message, TEXTS[lang]["promo_applied"])
            
            try:
                bot.send_message(int(referrer_id), "🎉 **REFERRAL BONUS!**\n\nA new user joined using your promo code/link! **+6.0 IC** has been added to your balance.")
            except Exception:
                pass
    else:
        msg = bot.reply_to(message, TEXTS[lang]["invalid_promo"])
        bot.register_next_step_handler(msg, process_promo_step)
        return

    msg = bot.reply_to(message, TEXTS[lang]["ask_username"])
    bot.register_next_step_handler(msg, save_username)

def save_username(message):
    if is_banned(message.from_user):
        return bot.reply_to(message, "❌ You are banned from using this bot.")
        
    user_id_str = str(message.from_user.id)
    lang = get_lang(message.from_user.id)
    username = message.text.strip()
    
    if not username.startswith('@'):
        msg = bot.reply_to(message, TEXTS[lang]["invalid_username"])
        bot.register_next_step_handler(msg, save_username)
        return
    
    db["registered_users"][user_id_str] = username
    if user_id_str not in db["user_balances"]:
        db["user_balances"][user_id_str] = 0.0
    save_db()
    
    bot.reply_to(message, TEXTS[lang]["login_success"].format(username=username))
    show_main_menu(message.chat.id, message.from_user.id)

def show_main_menu(chat_id, user_id, message_id=None):
    lang = get_lang(user_id)
    user_id_str = str(user_id)
    
    username = db.get("registered_users", {}).get(user_id_str)
    balance = 0.0
    
    if user_id_str in db.get("user_balances", {}):
        balance = float(db["user_balances"][user_id_str])
    elif username and username.lower() in db.get("user_balances", {}):
        balance = float(db["user_balances"][username.lower()])
        
    if not username:
        username = f"@{chat_id}" if chat_id else "@user"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(TEXTS[lang]["btn_buy_proj"], callback_data="menu_projects"),
        types.InlineKeyboardButton(TEXTS[lang]["btn_buy_files"], callback_data="menu_files"),
        types.InlineKeyboardButton(TEXTS[lang]["btn_buy_mods"], callback_data="menu_mods"),
        types.InlineKeyboardButton(TEXTS[lang]["btn_add_bal"], callback_data="menu_add_balance"),
        types.InlineKeyboardButton(TEXTS[lang]["btn_referral"], callback_data="menu_referral"),
        types.InlineKeyboardButton(TEXTS[lang]["btn_orders"], callback_data="menu_orders"),
        types.InlineKeyboardButton(TEXTS[lang]["btn_channel"], callback_data="menu_channel"),
        types.InlineKeyboardButton(TEXTS[lang]["btn_support"], callback_data="menu_support")
    )
    
    text = TEXTS[lang]["main_title"].format(username=username, user_id=user_id, balance=balance)
    
    if message_id:
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    user_id_str = str(user_id)
    message_id = call.message.message_id
    lang = get_lang(user_id)
    
    if is_banned(call.from_user):
        try:
            bot.answer_callback_query(call.id, "❌ You are banned!", show_alert=True)
        except Exception:
            pass
        return

    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    if call.data == "main_menu":
        show_main_menu(chat_id, user_id, message_id)
    elif call.data == "menu_projects":
        send_item_list(chat_id, user_id, message_id, "Projects", db.get("projects", []))
    elif call.data == "menu_files":
        send_item_list(chat_id, user_id, message_id, "Files", db.get("files", []))
    elif call.data == "menu_mods":
        send_item_list(chat_id, user_id, message_id, "ModApks", db.get("mod_apks", []))

    elif call.data == "menu_referral":
        if user_id_str not in db.get("user_promo_codes", {}):
            new_code = generate_promo_code()
            db.setdefault("user_promo_codes", {})[user_id_str] = new_code
            db.setdefault("promo_code_map", {})[new_code] = user_id_str
            save_db()
        
        user_code = db["user_promo_codes"][user_id_str]
        bot_username = bot.get_me().username
        ref_link = f"https://t.me/{bot_username}?start={user_code}"
        total_ref_earned = float(db.get("user_ref_earnings", {}).get(user_id_str, 0.0))
        
        ref_text = (
            f"🎁 **REFERRAL & PROMO PROGRAM**\n\n"
            f"🔑 **Your Custom Promo Code:** `{user_code}`\n"
            f"🔗 **Your Referral Link:** {ref_link}\n\n"
            f"💰 **Total Earned from Referrals:** `{total_ref_earned:.1f} IC`\n\n"
            f"📌 **How it works:**\n"
            f"1️⃣ Share your link or promo code with friends.\n"
            f"2️⃣ When they join using your code, they get **+5.4 IC Welcome Bonus** & you get **+6.0 IC Instant Bonus**.\n"
            f"3️⃣ When they make their **First Purchase**, you get an extra **+4.6 IC Bonus** directly in your account!"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu"))
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        bot.send_message(chat_id, ref_text, reply_markup=markup, parse_mode='Markdown')

    elif call.data == "menu_orders":
        orders = db.get("user_orders", {}).get(user_id_str, [])
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        if not orders:
            markup.add(types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu"))
            text = TEXTS[lang]["no_orders"]
        else:
            text = TEXTS[lang]["orders_title"] + "\n"
            for idx, order in enumerate(orders):
                markup.add(types.InlineKeyboardButton(f"📥 Download {order['name']}", callback_data=f"dl_order_{idx}"))
            markup.add(types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu"))
        
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        bot.send_message(chat_id, text, reply_markup=markup)

    elif call.data.startswith("dl_order_"):
        order_idx = int(call.data.split("_")[2])
        orders = db.get("user_orders", {}).get(user_id_str, [])
        
        if order_idx < len(orders):
            order = orders[order_idx]
            file_payload = order.get("file_id")
            if file_payload:
                try:
                    sent_msg = bot.send_document(chat_id, file_payload, caption=f"📦 Re-Delivered: {order['name']}\n⏱ (This file will auto-delete in 15 minutes)")
                    schedule_file_deletion(chat_id, sent_msg.message_id)
                except Exception:
                    sent_msg = bot.send_message(chat_id, f"🔗 Delivery Link / File:\n\n{file_payload}\n\n⏱ (This message will auto-delete in 15 minutes)")
                    schedule_file_deletion(chat_id, sent_msg.message_id)
            else:
                bot.answer_callback_query(call.id, "❌ File payload missing!", show_alert=True)

    elif call.data == "menu_add_balance":
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(TEXTS[lang]["btn_send_ss"], url=f"https://t.me/{ADMIN_USERNAME}"),
            types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu")
        )
        add_text = TEXTS[lang]["add_bal_text"].format(upi=UPI_ID)
        
        try:
            with open("qr.jpg", "rb") as photo:
                bot.send_photo(chat_id, photo, caption=add_text, reply_markup=markup)
        except Exception:
            bot.send_message(chat_id, add_text, reply_markup=markup)

    elif call.data == "menu_support":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(TEXTS[lang]["btn_chat_admin"], url=f"https://t.me/{ADMIN_USERNAME}"),
            types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu")
        )
        text = TEXTS[lang]["support_text"].format(admin=ADMIN_USERNAME)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        bot.send_message(chat_id, text, reply_markup=markup)

    elif call.data == "menu_channel":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton(TEXTS[lang]["btn_visit_channel"], url=CHANNEL_LINK),
            types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu")
        )
        text = TEXTS[lang]["channel_text"].format(channel=CHANNEL_LINK)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass
        bot.send_message(chat_id, text, reply_markup=markup)

    elif call.data.startswith("pay_"):
        parts = call.data.split("_")
        category = parts[1]
        item_id = parts[2]
        
        items_list = db["projects"] if category == "projects" else (db["files"] if category == "files" else db["mod_apks"])
        item = next((i for i in items_list if i["id"] == item_id), None)
        
        if not item:
            return bot.answer_callback_query(call.id, TEXTS[lang]["item_not_found"], show_alert=True)
            
        final_price_ic = float(item["price"])
        
        username = db.get("registered_users", {}).get(user_id_str)
        user_bal = 0.0
        
        if user_id_str in db.get("user_balances", {}):
            user_bal = float(db["user_balances"][user_id_str])
        elif username and username.lower() in db.get("user_balances", {}):
            user_bal = float(db["user_balances"][username.lower()])
            
        if user_bal >= final_price_ic:
            new_bal = round(user_bal - final_price_ic, 1)
            
            if user_id_str in db.get("user_balances", {}):
                db["user_balances"][user_id_str] = new_bal
            elif username and username.lower() in db.get("user_balances", {}):
                db["user_balances"][username.lower()] = new_bal
            else:
                db["user_balances"][user_id_str] = new_bal

            db["total_earnings"] = round(db.get("total_earnings", 0.0) + final_price_ic, 1)
            file_payload = item.get("file_id")
            
            db.setdefault("user_orders", {}).setdefault(user_id_str, []).append({
                "name": item["name"],
                "price": round(final_price_ic, 1),
                "file_id": file_payload
            })

            # Bonus on First Purchase for Referrer (+4.6 IC)
            if not db.get("has_purchased", {}).get(user_id_str, False):
                db.setdefault("has_purchased", {})[user_id_str] = True
                referrer_id = db.get("referred_by", {}).get(user_id_str)
                if referrer_id:
                    ref_bal = float(db.get("user_balances", {}).get(referrer_id, 0.0))
                    db["user_balances"][referrer_id] = round(ref_bal + 4.6, 1)
                    
                    current_ref_earned = float(db.get("user_ref_earnings", {}).get(referrer_id, 0.0))
                    db.setdefault("user_ref_earnings", {})[referrer_id] = round(current_ref_earned + 4.6, 1)

                    try:
                        bot.send_message(int(referrer_id), "🎉 **FIRST PURCHASE REFERRAL BONUS!**\n\nYour referred friend just made their first purchase! **+4.6 IC** has been added to your balance.")
                    except Exception:
                        pass

            save_db()
            
            success_msg = TEXTS[lang]["buy_success"].format(name=item['name'], price=round(final_price_ic, 1), new_balance=new_bal)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu"))
            
            try:
                bot.delete_message(chat_id, message_id)
            except Exception:
                pass
            bot.send_message(chat_id, success_msg, reply_markup=markup)
                
            if file_payload:
                try:
                    sent_msg = bot.send_document(chat_id, file_payload, caption=f"📦 Delivered: {item['name']}\n⏱ (This file will auto-delete in 15 minutes)")
                    schedule_file_deletion(chat_id, sent_msg.message_id)
                except Exception:
                    sent_msg = bot.send_message(chat_id, f"🔗 Delivery Link / File:\n\n{file_payload}\n\n⏱ (This message will auto-delete in 15 minutes)")
                    schedule_file_deletion(chat_id, sent_msg.message_id)
        else:
            try:
                bot.answer_callback_query(call.id, f"⚠️ Not enough IC balance! Need {round(final_price_ic, 1)} IC.", show_alert=True)
            except Exception:
                pass
                
            inr_equivalent = round(final_price_ic / 1.2, 2)
            pay_text = TEXTS[lang]["not_enough_ic"].format(price=round(final_price_ic, 1), balance=user_bal) + "\n\n" + TEXTS[lang]["pay_title"].format(
                name=item['name'],
                price=round(final_price_ic, 1),
                inr_price=inr_equivalent,
                upi=UPI_ID,
                admin=ADMIN_USERNAME
            )
            
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(TEXTS[lang]["btn_send_ss"], url=f"https://t.me/{ADMIN_USERNAME}"),
                types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu")
            )
            
            try:
                bot.delete_message(chat_id, message_id)
            except Exception:
                pass
                
            try:
                with open("qr.jpg", "rb") as photo:
                    bot.send_photo(chat_id, photo, caption=pay_text, reply_markup=markup)
            except Exception:
                bot.send_message(chat_id, pay_text, reply_markup=markup)

def send_item_list(chat_id, user_id, message_id, category_name, items):
    lang = get_lang(user_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    if not items:
        markup.add(types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu"))
        text = TEXTS[lang]["no_items"].format(category=category_name)
    else:
        text = f"🔸 AVAILABLE {category_name.upper()}:\n\n"
        for item in items:
            orig_price = float(item['price'])
            text += f"🔹 {item['name']} - {orig_price:.1f} IC\n"
            btn_label = f"⭐ Buy {item['name']} @ {orig_price:.1f} IC"
            cat_key = "projects" if category_name == "Projects" else ("files" if category_name == "Files" else "mods")
            markup.add(types.InlineKeyboardButton(btn_label, callback_data=f"pay_{cat_key}_{item['id']}"))
            
        markup.add(types.InlineKeyboardButton(TEXTS[lang]["btn_back"], callback_data="main_menu"))
        
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode='Markdown')

print("Bot updated & ready for Render 24/7 Hosting!")
bot.infinity_polling()
