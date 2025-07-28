import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os
from flask import Flask, request

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://bot-ltl5.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_data = {}

def get_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🔁 شروع مجدد"))
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📞 ارسال شماره تماس", request_contact=True))
    bot.send_message(chat_id, "لطفاً شماره تماس خود را وارد نمایید یا از دکمه زیر استفاده کنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    chat_id = message.chat.id
    user_data[chat_id]['phone'] = message.contact.phone_number
    bot.send_message(chat_id, "لطفاً نام و نام خانوادگی خود را وارد نمایید:", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: 'phone' in user_data.get(m.chat.id, {}) and 'name' not in user_data[m.chat.id], content_types=['text'])
def handle_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text
    bot.send_message(chat_id, "✅ لطفاً مشکل خود را به صورت متن یا ویس ارسال نمایید.")

@bot.message_handler(content_types=['text', 'voice'])
def handle_problem(message):
    chat_id = message.chat.id
    data = user_data.get(chat_id, {})

    if 'phone' in data and 'name' in data:
        if message.content_type == 'voice':
            file_info = bot.get_file(message.voice.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            voice_path = f"/tmp/{message.voice.file_id}.ogg"
            with open(voice_path, 'wb') as f:
                f.write(downloaded_file)
            with open(voice_path, 'rb') as f:
                bot.send_voice(ADMIN_ID, f, caption=f"📥 تماس: {data['phone']}
👤 نام: {data['name']}")
        else:
            bot.send_message(ADMIN_ID, f"📥 تماس: {data['phone']}
👤 نام: {data['name']}
📝 مشکل:
{message.text}")

        bot.send_message(chat_id, "✅ اطلاعات شما با موفقیت ثبت شد.
کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت.

☎️ برای مشاوره فوری:
09001003914", reply_markup=get_main_menu())
        user_data.pop(chat_id, None)
    elif message.text == "🔁 شروع مجدد":
        start_handler(message)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
        return '', 200
    return 'ok', 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"{WEBHOOK_URL}/")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 10000)))