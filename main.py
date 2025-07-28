import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 7549512366

user_data = {}

@bot.message_handler(commands=["start", "restart"])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {}
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    button = KeyboardButton("📱 ارسال شماره تماس", request_contact=True)
    markup.add(button)
    bot.send_message(chat_id, "👋 سلام!
برای شروع لطفاً شماره تماس خود را وارد کنید یا از دکمه زیر استفاده کنید:", reply_markup=markup)

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    chat_id = message.chat.id
    phone_number = message.contact.phone_number
    user_data[chat_id]["phone"] = phone_number
    bot.send_message(chat_id, "🧑‍💼 لطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: "phone" in user_data.get(m.chat.id, {}) and "name" not in user_data[m.chat.id], content_types=["text"])
def name_handler(message):
    chat_id = message.chat.id
    name = message.text.strip()
    user_data[chat_id]["name"] = name
    bot.send_message(chat_id, "📝 لطفاً مشکل خود را به صورت متن یا ویس ارسال کنید:")

@bot.message_handler(func=lambda m: "name" in user_data.get(m.chat.id, {}), content_types=["text", "voice"])
def issue_handler(message):
    chat_id = message.chat.id
    info = user_data.get(chat_id, {})
    name = info.get("name", "نامشخص")
    phone = info.get("phone", "نامشخص")
    
    if message.content_type == "text":
        complaint = message.text.strip()
        text = f"📥 درخواست مشاوره جدید

👤 نام: {name}
📞 شماره تماس: {phone}
📝 شرح مشکل: {complaint}"
        bot.send_message(ADMIN_ID, text)
    elif message.content_type == "voice":
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        text = f"📥 درخواست مشاوره جدید

👤 نام: {name}
📞 شماره تماس: {phone}
🎤 کاربر یک ویس ارسال کرد."
        bot.send_message(ADMIN_ID, text)
    
    user_data.pop(chat_id, None)
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("/restart"))
    bot.send_message(chat_id, "✅ اطلاعات شما با موفقیت ثبت شد.
کارشناسان ما در اسرع وقت با شما تماس می‌گیرند.

☎️ برای مشاوره فوری: 09001003914", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(message.chat.id, "لطفاً از دکمه‌ها یا دستور /start استفاده کنید.")

# Auto webhook setup
from flask import Flask, request
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def index():
    return "Bot is running", 200

if __name__ == "__main__":
    import telebot
    bot.remove_webhook()
    bot.set_webhook(url="https://bot-ltl5.onrender.com/webhook")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))