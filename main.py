import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request

API_TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://bot-ltl5.onrender.com/webhook"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_data = {}

# مرحله اول: دریافت شماره تماس
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = KeyboardButton("📞 ارسال شماره تماس", request_contact=True)
    markup.add(btn)
    bot.send_message(
        chat_id,
        "📞 لطفاً شماره تماس خود را وارد نمایید.

"
        "✅ می‌توانید شماره را *تایپ کنید* یا برای راحتی بیشتر، از دکمه‌ی زیر استفاده نمایید:",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    user_data[chat_id] = {}

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    chat_id = message.chat.id
    contact = message.contact.phone_number
    user_data[chat_id]['phone'] = contact
    bot.send_message(chat_id, "✅ شماره تماس دریافت شد.

لطفا نام و نام خانوادگی خود را وارد کنید:")
    
@bot.message_handler(func=lambda message: message.chat.id in user_data and 'phone' in user_data[message.chat.id] and 'name' not in user_data[message.chat.id], content_types=['text'])
def get_name(message):
    chat_id = message.chat.id
    name = message.text
    user_data[chat_id]['name'] = name
    bot.send_message(chat_id, "✅ نام ثبت شد.

حالا لطفا مشکل خود را به صورت متن یا ویس ارسال کنید:")

@bot.message_handler(func=lambda message: message.chat.id in user_data and 'name' in user_data[message.chat.id], content_types=['text', 'voice'])
def get_problem(message):
    chat_id = message.chat.id
    data = user_data.get(chat_id, {})
    name = data.get('name', 'نامشخص')
    phone = data.get('phone', 'نامشخص')

    if message.content_type == 'text':
        problem = message.text
        bot.send_message(chat_id, "✅ مشکل شما ثبت شد. تیم ما بزودی با شما تماس خواهد گرفت.")
        bot.send_message(ADMIN_ID, f"📥 درخواست جدید:
👤 نام: {name}
📞 شماره: {phone}
📝 مشکل: {problem}")
    elif message.content_type == 'voice':
        file_id = message.voice.file_id
        bot.send_message(chat_id, "✅ ویس شما ثبت شد. تیم ما بزودی بررسی خواهد کرد.")
        bot.send_message(ADMIN_ID, f"📥 درخواست جدید:
👤 نام: {name}
📞 شماره: {phone}
🎙 ویس:")
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)

    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("🔁 شروع مجدد"))
    bot.send_message(chat_id, "برای شروع مجدد فرآیند، روی دکمه زیر کلیک کنید 👇", reply_markup=markup)
    user_data.pop(chat_id, None)
    

# Webhook route
@app.route("/webhook", methods=['POST'])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/')
def index():
    return 'Bot is running!'

if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
