import telebot
from telebot import types
from flask import Flask, request
import os

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://bot-ltl5.onrender.com/webhook"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_data = {}

# مرحله شروع
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("ارسال شماره تماس 📱", request_contact=True)
    markup.add(button)
    bot.send_message(cid, """سلام و وقت شما بخیر 👋 ⚖️

ما در خدمت شما برای حل مسائل حقوقی هستیم 📜
لطفاً شماره تماس خود را وارد کنید یا از دکمه زیر استفاده نمایید:""", reply_markup=markup)

# دریافت شماره تماس
@bot.message_handler(content_types=['contact'])
def get_contact(message):
    cid = message.chat.id
    phone = message.contact.phone_number
    user_data[cid]["phone"] = phone
    bot.send_message(cid, """✅ شماره تماس با موفقیت ثبت شد ⚖️

لطفاً نام و نام خانوادگی خود را وارد نمایید 📝""", reply_markup=types.ReplyKeyboardRemove())

# دریافت نام و نام خانوادگی
@bot.message_handler(func=lambda m: "phone" in user_data.get(m.chat.id, {}) and "name" not in user_data.get(m.chat.id, {}))
def get_name(message):
    cid = message.chat.id
    user_data[cid]["name"] = message.text
    bot.send_message(cid, "لطفاً مشکل حقوقی خود را به صورت *متنی* یا *ویس* ارسال نمایید 📜 🧑‍⚖️", parse_mode="Markdown")

# دریافت ویس
@bot.message_handler(content_types=['voice'])
def get_voice(message):
    cid = message.chat.id
    file_id = message.voice.file_id
    name = user_data[cid].get("name", "نامشخص")
    phone = user_data[cid].get("phone", "نامشخص")
    caption = f"🧾 اطلاعات کاربر:\n👤 نام: {name}\n📱 شماره تماس: {phone}"
    bot.send_voice(ADMIN_ID, file_id, caption=caption)
    send_thanks(cid)

# دریافت پیام متنی
@bot.message_handler(func=lambda m: True)
def get_text(message):
    cid = message.chat.id
    if "phone" in user_data.get(cid, {}) and "name" in user_data[cid]:
        user_data[cid]["issue"] = message.text
        name = user_data[cid].get("name", "نامشخص")
        phone = user_data[cid].get("phone", "نامشخص")
        issue = user_data[cid].get("issue", "")
        msg = f"🧾 اطلاعات کاربر:\n👤 نام: {name}\n📱 شماره تماس: {phone}\n📝 مشکل:\n{issue}"
        bot.send_message(ADMIN_ID, msg)
        send_thanks(cid)

def send_thanks(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔁 شروع مجدد", callback_data="restart"))
    bot.send_message(cid, """✅ اطلاعات شما با موفقیت ثبت شد ⚖️

📞 کارشناسان ما در اسرع وقت با شما تماس می‌گیرند 📞

☎️ برای مشاوره فوری:
09001003914""", reply_markup=markup)

# پردازش Callback Query برای دکمه شروع مجدد
@bot.callback_query_handler(func=lambda call: call.data == "restart")
def process_restart(call):
    cid = call.message.chat.id
    if cid in user_data:
        del user_data[cid]  # حذف کامل داده‌های قبلی
    user_data[cid] = {}  # ایجاد دیکشنری خالی جدید
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("ارسال شماره تماس 📱", request_contact=True)
    markup.add(button)
    bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text="🔄 روند با موفقیت ریست شد! ⚖️ لطفاً از نو شروع کنید.")
    bot.send_message(cid, """سلام و وقت شما بخیر 👋 ⚖️

ما در خدمت شما برای حل مسائل حقوقی هستیم 📜
لطفاً شماره تماس خود را وارد کنید یا از دکمه زیر استفاده نمایید:""", reply_markup=markup)

# ریست روند با دستور /restart
@bot.message_handler(commands=['restart'])
def restart_command(message):
    cid = message.chat.id
    if cid in user_data:
        del user_data[cid]  # حذف کامل داده‌های قبلی
    user_data[cid] = {}  # ایجاد دیکشنری خالی جدید
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("ارسال شماره تماس 📱", request_contact=True)
    markup.add(button)
    bot.send_message(cid, "🔄 روند با موفقیت ریست شد! ⚖️ لطفاً از نو شروع کنید.", reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(cid, """سلام و وقت شما بخیر 👋 ⚖️

ما در خدمت شما برای حل مسائل حقوقی هستیم 📜
لطفاً شماره تماس خود را وارد کنید یا از دکمه زیر استفاده نمایید:""", reply_markup=markup)

# پیکربندی webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "", 403

@app.route("/")
def index():
    return "ربات حقوقی فعال است ⚖️"

import telebot.apihelper
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
