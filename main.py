import telebot
from flask import Flask, request
import os

TOKEN = os.getenv("TOKEN", "8010785406:AAFPInJ3QQmyNti9KwDxj075iOmVUhZJ364")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot-ltl5.onrender.com/webhook")
ADMIN_ID = 7549512366

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {}
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("⚖️ مشاوره حقوقی", callback_data="legal"),
               telebot.types.InlineKeyboardButton("🌐 مهاجرت", callback_data="migration"))
    bot.send_message(cid, "⚖️ *خوش آمدید به elawfirm!* 📜\nلطفاً نوع مشاوره را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

# (بقیه handlerها مثل کد قبلی)

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "", 403

import telebot.apihelper
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
