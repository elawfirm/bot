import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import os

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://bot-ltl5.onrender.com"

bot = telebot.TeleBot(TOKEN)
user_data = {}

# تنظیم webhook در شروع
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("📞 ارسال شماره تماس", request_contact=True))
    bot.send_message(chat_id, "لطفاً شماره تماس خود را وارد کنید یا روی دکمه زیر بزنید:", reply_markup=markup)

@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    user_data[chat_id]["phone"] = phone
    bot.send_message(chat_id, "✅ شماره تماس ثبت شد.

لطفاً نام و نام خانوادگی خود را وارد کنید:")
    
@bot.message_handler(func=lambda m: "phone" in user_data.get(m.chat.id, {}) and "name" not in user_data[m.chat.id])
def handle_name(message):
    chat_id = message.chat.id
    user_data[chat_id]["name"] = message.text
    bot.send_message(chat_id, "✅ نام ثبت شد.

لطفاً مشکل خود را به‌صورت ویس یا متن ارسال کنید.")

@bot.message_handler(content_types=["voice", "text"])
def handle_problem(message):
    chat_id = message.chat.id
    if chat_id not in user_data or "name" not in user_data[chat_id]:
        return
    
    phone = user_data[chat_id]["phone"]
    name = user_data[chat_id]["name"]
    
    caption = f"📥 درخواست جدید:

👤 نام: {name}
📞 شماره: {phone}"

    if message.voice:
        file_id = message.voice.file_id
        bot.send_voice(ADMIN_ID, file_id, caption=caption)
    else:
        problem = message.text
        full_message = f"{caption}
📝 مشکل:
{problem}"
        bot.send_message(ADMIN_ID, full_message)
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔄 شروع مجدد")
    bot.send_message(chat_id, "✅ اطلاعات شما با موفقیت ثبت شد.
کارشناسان ما در اسرع وقت با شما تماس می‌گیرند.

☎️ برای مشاوره فوری: 09001003914", reply_markup=markup)

    # پاکسازی اطلاعات
    user_data.pop(chat_id)

@bot.message_handler(func=lambda m: m.text == "🔄 شروع مجدد")
def restart(message):
    start(message)

# webhook setup (فقط بار اول روی Render اجرا شود)
import flask
app = flask.Flask(__name__)

@app.route('/', methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(flask.request.stream.read().decode("utf-8"))])
    return "OK", 200

@app.route('/', methods=["GET"])
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))