import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request
import os

API_TOKEN = '8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8'
ADMIN_ID = 7549512366
WEBHOOK_URL = 'https://bot-ltl5.onrender.com/webhook'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_state = {}
user_data = {}

# مرحله 1: درخواست شماره تماس
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = 'awaiting_contact'
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = KeyboardButton("📞 ارسال شماره تماس", request_contact=True)
    markup.add(button)
    bot.send_message(user_id, "لطفاً شماره تماس خود را وارد کنید یا از دکمه زیر استفاده نمایید:", reply_markup=markup)

# دریافت شماره تماس
@bot.message_handler(content_types=['contact'])
def get_contact(message):
    user_id = message.chat.id
    if user_state.get(user_id) == 'awaiting_contact':
        phone = message.contact.phone_number
        user_data[user_id] = {'phone': phone}
        user_state[user_id] = 'awaiting_name'
        bot.send_message(user_id, "✅ شماره شما ثبت شد.\n\nلطفاً نام و نام خانوادگی خود را ارسال کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())

# دریافت نام و نام خانوادگی
@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == 'awaiting_name')
def get_name(message):
    user_id = message.chat.id
    user_data[user_id]['name'] = message.text
    user_state[user_id] = 'awaiting_problem'
    bot.send_message(user_id, "📝 لطفاً مشکل خود را با نوشتن یا ارسال ویس توضیح دهید:")

# دریافت مشکل (متن یا ویس)
@bot.message_handler(content_types=['text', 'voice'])
def get_problem(message):
    user_id = message.chat.id
    if user_state.get(user_id) == 'awaiting_problem':
        contact = user_data[user_id].get('phone', 'ثبت نشده')
        name = user_data[user_id].get('name', 'ثبت نشده')

        if message.content_type == 'voice':
            file_id = message.voice.file_id
            bot.send_voice(ADMIN_ID, file_id, caption=f"📞 شماره: {contact}\n👤 نام: {name}\n🎙 کاربر یک ویس ارسال کرد.")
        else:
            bot.send_message(ADMIN_ID, f"📞 شماره: {contact}\n👤 نام: {name}\n📌 مشکل: {message.text}")

        bot.send_message(user_id, "✅ اطلاعات شما با موفقیت ثبت شد. تیم حقوقی به‌زودی با شما تماس خواهد گرفت.")

        # دکمه شروع مجدد
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("🔁 شروع مجدد"))
        bot.send_message(user_id, "برای ارسال درخواست جدید، روی دکمه زیر بزنید:", reply_markup=markup)
        user_state[user_id] = 'done'

# هندلر شروع مجدد
@bot.message_handler(func=lambda m: m.text == "🔁 شروع مجدد")
def restart(message):
    start(message)

# ────────────── Flask Webhook ────────────── #
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Invalid request', 403

@app.route('/')
def index():
    return 'ربات حقوقی فعال است ✅'

# تنظیم خودکار Webhook
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

if __name__ == '__main__':
    set_webhook()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
