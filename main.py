import telebot
from telebot import types
from flask import Flask, request

API_TOKEN = '8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8'
ADMIN_ID = 7549512366

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_data = {}

# مرحله اول: دریافت شماره تماس
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = types.KeyboardButton("📞 ارسال شماره تماس", request_contact=True)
    markup.add(button)
    bot.send_message(message.chat.id, "لطفاً شماره تماس خود را وارد نمایید یا از دکمه زیر استفاده کنید:", reply_markup=markup)
    user_data[message.chat.id] = {'step': 'phone'}

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    chat_id = message.chat.id
    if chat_id in user_data and user_data[chat_id]['step'] == 'phone':
        user_data[chat_id]['phone'] = message.contact.phone_number
        user_data[chat_id]['step'] = 'name'
        bot.send_message(chat_id, "لطفاً نام و نام خانوادگی خود را وارد نمایید:", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.chat.id in user_data and user_data[m.chat.id]['step'] == 'name')
def get_name(message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text
    user_data[chat_id]['step'] = 'problem'
    markup = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "لطفاً مشکل خود را به‌صورت *متن یا ویس* ارسال نمایید:", parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(content_types=['voice'])
def get_voice(message):
    chat_id = message.chat.id
    if chat_id in user_data and user_data[chat_id]['step'] == 'problem':
        voice = message.voice.file_id
        user_data[chat_id]['step'] = 'done'
        caption = f"📞 تماس: {user_data[chat_id].get('phone')}
👤 نام: {user_data[chat_id].get('name')}"
        bot.send_voice(ADMIN_ID, voice, caption=caption)
        send_done_message(chat_id)

@bot.message_handler(func=lambda m: m.chat.id in user_data and user_data[m.chat.id]['step'] == 'problem')
def get_problem_text(message):
    chat_id = message.chat.id
    user_data[chat_id]['step'] = 'done'
    text = f"📞 تماس: {user_data[chat_id].get('phone')}
👤 نام: {user_data[chat_id].get('name')}
📝 مشکل:
{message.text}"
    bot.send_message(ADMIN_ID, text)
    send_done_message(chat_id)

def send_done_message(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔁 شروع مجدد"))
    bot.send_message(chat_id,
        "✅ اطلاعات شما با موفقیت ثبت شد.
"
        "کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت.

"
        "☎️ برای مشاوره فوری:
"
        "09001003914",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: m.text == "🔁 شروع مجدد")
def restart(message):
    start(message)

@app.route('/', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return 'OK'

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running.'

bot.remove_webhook()
bot.set_webhook(url='https://bot-ltl5.onrender.com/')