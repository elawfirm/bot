
import telebot
import sqlite3
import os
from flask import Flask, request

TOKEN = '8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8'
ADMIN_ID = 7549512366
bot = telebot.TeleBot(TOKEN)

os.makedirs("voices", exist_ok=True)

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER, "
        "name TEXT, "
        "phone TEXT, "
        "problem TEXT, "
        "voice_file TEXT)"
    )
    conn.commit()
    conn.close()

init_db()

user_state = {}

def save_user(chat_id, name, phone, problem, voice_file):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (user_id, name, phone, problem, voice_file) VALUES (?, ?, ?, ?, ?)",
              (chat_id, name, phone, problem, voice_file))
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_state[chat_id] = {"step": "phone"}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    contact_btn = telebot.types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True)
    markup.add(contact_btn)
    bot.send_message(chat_id,
        "⚖️ *به هلدینگ حقوقی الای خوش آمدید.*\n"
        "برای رزرو وقت مشاوره مراحل زیر را کامل کنید.\n\n"
        "📱 لطفاً شماره تماس خود را ارسال کنید:",
        reply_markup=markup, parse_mode='Markdown'
    )

@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    user_state[chat_id] = {"phone": phone, "step": "name"}
    bot.send_message(chat_id, f"📞 شماره شما ثبت شد: {phone}\n👤 لطفاً نام و نام خانوادگی خود را وارد کنید:",
                     reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: True, content_types=['text','voice'])
def handle(message):
    chat_id = message.chat.id
    if chat_id not in user_state:
        bot.reply_to(message, "برای شروع روی /start بزنید.")
        return

    step = user_state[chat_id].get('step')

    if step == 'phone':
        phone = message.text
        user_state[chat_id]['phone'] = phone
        user_state[chat_id]['step'] = 'name'
        bot.send_message(chat_id, f"📞 شماره شما ثبت شد: {phone}\n👤 لطفاً نام و نام خانوادگی خود را وارد کنید:")

    elif step == 'name':
        user_state[chat_id]['name'] = message.text
        user_state[chat_id]['step'] = 'problem'
        bot.send_message(chat_id, "📝 لطفاً مشکل یا موضوع حقوقی خود را به صورت متن یا ویس ارسال کنید:")

    elif step == 'problem':
        voice_path = None
        if message.content_type == 'voice':
            file_info = bot.get_file(message.voice.file_id)
            voice_path = f"voices/{chat_id}_{message.voice.file_id}.ogg"
            downloaded = bot.download_file(file_info.file_path)
            with open(voice_path, 'wb') as f:
                f.write(downloaded)
            user_state[chat_id]['problem'] = "Voice Message"
        else:
            user_state[chat_id]['problem'] = message.text

        save_user(chat_id, user_state[chat_id]['name'], user_state[chat_id]['phone'],
                  user_state[chat_id]['problem'], voice_path)

        notify_msg = (
            "🔔 *درخواست جدید مشاوره*\n"
            f"👤 نام: {user_state[chat_id]['name']}\n"
            f"📞 شماره: {user_state[chat_id]['phone']}\n"
            f"📝 مشکل: {'ویس ارسال شد' if voice_path else user_state[chat_id]['problem']}"
        )
        bot.send_message(ADMIN_ID, notify_msg, parse_mode='Markdown')

        bot.send_message(chat_id,
            "✅ اطلاعات شما با موفقیت ثبت شد.\n"
            "کارشناسان ما در اسرع وقت با شما تماس می‌گیرند.\n\n"
            "☎️ برای مشاوره فوری: 09001003914",
            reply_markup=telebot.types.ReplyKeyboardRemove()
        )
        del user_state[chat_id]

app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200


@app.route('/')
def index():
    return "Legal Bot is running via webhook."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
