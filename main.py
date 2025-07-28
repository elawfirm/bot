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

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    user_state[user_id] = 'awaiting_contact'
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📞 ارسال شماره تماس", request_contact=True))
    bot.send_message(user_id,
                     "📞 لطفاً شماره تماس خود را وارد نمایید.

"
                     "✅ می‌توانید شماره را *تایپ کنید* یا برای راحتی بیشتر، از دکمه‌ی زیر استفاده نمایید:",
                     reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    user_id = message.chat.id
    if user_state.get(user_id) == 'awaiting_contact':
        phone = message.contact.phone_number
        user_data[user_id] = {'phone': phone}
        user_state[user_id] = 'awaiting_name'
        bot.send_message(user_id, "✍️ لطفاً نام و نام خانوادگی خود را وارد نمایید:",
                         reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == 'awaiting_name')
def get_name(message):
    user_id = message.chat.id
    user_data[user_id]['name'] = message.text.strip()
    user_state[user_id] = 'awaiting_problem'
    bot.send_message(user_id, "📝 لطفاً مشکل حقوقی خود را توضیح دهید.
"
                              "می‌توانید *متن تایپ کنید* یا *ویس ارسال نمایید*.", parse_mode="Markdown")

@bot.message_handler(content_types=['text', 'voice'])
def get_problem(message):
    user_id = message.chat.id
    if user_state.get(user_id) == 'awaiting_problem':
        contact = user_data[user_id].get('phone', 'نامشخص')
        name = user_data[user_id].get('name', 'نامشخص')

        if message.content_type == 'voice':
            bot.send_voice(ADMIN_ID, message.voice.file_id,
                           caption=f"📞 شماره تماس: {contact}
👤 نام: {name}
🎙 ویس ارسالی از کاربر.")
        else:
            bot.send_message(ADMIN_ID, f"📞 شماره تماس: {contact}
👤 نام: {name}
📝 شرح مشکل:
{message.text}")

        bot.send_message(user_id,
                         "✅ اطلاعات شما با موفقیت ثبت شد.
"
                         "👩‍⚖️ کارشناسان حقوقی ما در اسرع وقت با شما تماس خواهند گرفت.

"
                         "☎️ نیاز به مشاوره فوری دارید؟
📞 09001003914", parse_mode="Markdown")

        markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(KeyboardButton("🔁 شروع مجدد"))
        bot.send_message(user_id, "برای ثبت درخواست جدید، روی دکمه زیر کلیک کنید:", reply_markup=markup)
        user_state[user_id] = 'done'

@bot.message_handler(func=lambda m: m.text == "🔁 شروع مجدد")
def restart(message):
    start(message)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/')
def index():
    return 'ربات فعال است ✅'

def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

if __name__ == '__main__':
    set_webhook()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
