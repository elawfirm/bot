import telebot
from telebot import types
from flask import Flask, request

API_TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://bot-ltl5.onrender.com"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# استارت بات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    contact_btn = types.KeyboardButton("📞 ارسال شماره تماس", request_contact=True)
    markup.add(contact_btn)
    bot.send_message(message.chat.id, f"""سلام {message.from_user.first_name} عزیز 👋

به سامانه مشاوره حقوقی خوش آمدید.

لطفاً یکی از موارد زیر را برای شروع ارسال کنید:
📌 سوال حقوقی (به صورت متن یا ویس)
📞 و یا شماره تماس خود را برای مشاوره سریع‌تر ارسال نمایید.""", reply_markup=markup)

# دریافت شماره تماس
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    contact = message.contact
    info = f"""
📞 شماره تماس جدید:
👤 نام: {contact.first_name}
📱 شماره: {contact.phone_number}
🆔 یوزر: @{message.from_user.username if message.from_user.username else 'ندارد'}
"""
    bot.send_message(ADMIN_ID, info)
    bot.send_message(message.chat.id, "✅ شماره شما با موفقیت دریافت شد. کارشناسان ما به زودی با شما تماس می‌گیرند.")

# دریافت ویس
@bot.message_handler(content_types=['voice'])
def voice_handler(message):
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    bot.send_message(message.chat.id, "🎙 ویس شما دریافت شد. تیم ما بررسی خواهد کرد.")

# دریافت متن
@bot.message_handler(content_types=['text'])
def text_handler(message):
    msg = f"""
📩 پیام متنی جدید:
👤 {message.from_user.first_name}
🆔 @{message.from_user.username if message.from_user.username else 'ندارد'}
📝 متن: {message.text}
"""
    bot.send_message(ADMIN_ID, msg)
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ ما باشید.")

# Webhook route
@app.route('/', methods=['GET'])
def index():
    return "ربات حقوقی فعال است ✅"

@app.route('/webhook', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

# راه‌اندازی webhook
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL + "/webhook")

# اجرای برنامه Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
