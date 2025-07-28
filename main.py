import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, Message
from flask import Flask, request

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://bot-ltl5.onrender.com/webhook"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_data = {}

@bot.message_handler(commands=['start'])
def start(message: Message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📱 ارسال شماره تماس", request_contact=True))
    bot.send_message(chat_id, "لطفاً شماره تماس خود را وارد کنید یا از دکمه زیر استفاده نمایید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message: Message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    user_data[chat_id]['phone'] = phone
    bot.send_message(chat_id, "✅ شماره تماس ثبت شد.

لطفاً نام و نام خانوادگی خود را وارد نمایید.", reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda msg: 'phone' in user_data.get(msg.chat.id, {}) and 'name' not in user_data[msg.chat.id])
def handle_name(message: Message):
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text
    bot.send_message(chat_id, "✅ نام ثبت شد.

لطفاً مشکل خود را به صورت متن یا ویس ارسال کنید.")

@bot.message_handler(content_types=['text', 'voice'])
def handle_problem(message: Message):
    chat_id = message.chat.id
    if chat_id not in user_data or 'name' not in user_data[chat_id]:
        bot.send_message(chat_id, "لطفاً ابتدا از /start شروع کنید.")
        return

    name = user_data[chat_id]['name']
    phone = user_data[chat_id]['phone']

    caption = f"📥 درخواست جدید:
👤 نام: {name}
📱 شماره: {phone}"

    if message.content_type == 'text':
        caption += f"
📝 توضیح: {message.text}"
        bot.send_message(ADMIN_ID, caption)
    elif message.content_type == 'voice':
        bot.send_voice(ADMIN_ID, message.voice.file_id, caption=caption)

    bot.send_message(chat_id, "✅ اطلاعات شما با موفقیت ثبت شد.
کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت.

☎️ برای مشاوره فوری:
09001003914", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("🔄 شروع مجدد"))

    user_data.pop(chat_id, None)

@bot.message_handler(func=lambda msg: msg.text == "🔄 شروع مجدد")
def restart(message: Message):
    start(message)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return '', 403

@app.route('/')
def index():
    return "Bot is running."

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
