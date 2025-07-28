import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from flask import Flask, request

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://bot-ltl5.onrender.com/webhook"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
users = {}

@bot.message_handler(commands=["start"])
def start(message):
    cid = message.chat.id
    users[cid] = {}
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(KeyboardButton("📱 ارسال شماره تماس", request_contact=True))
    bot.send_message(cid, "👋 سلام و وقت شما بخیر

لطفاً شماره تماس خود را وارد کنید یا از دکمه زیر استفاده نمایید:", reply_markup=kb)

@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    cid = message.chat.id
    phone = message.contact.phone_number
    users[cid]["phone"] = phone
    bot.send_message(cid, "✅ شماره تماس با موفقیت ثبت شد.

لطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: m.chat.id in users and "phone" in users[m.chat.id] and "name" not in users[m.chat.id])
def handle_name(message):
    cid = message.chat.id
    users[cid]["name"] = message.text
    bot.send_message(cid, "✅ نام ثبت شد.

لطفاً مشکل خود را به صورت متن یا ویس ارسال نمایید:")

@bot.message_handler(content_types=["text", "voice"])
def handle_problem(message):
    cid = message.chat.id
    if cid not in users or "name" not in users[cid]:
        bot.send_message(cid, "❗ لطفاً ابتدا از /start شروع کنید.")
        return

    name = users[cid]["name"]
    phone = users[cid]["phone"]
    caption = f"📥 درخواست جدید:
👤 نام: {name}
📞 شماره: {phone}"

    if message.content_type == "text":
        problem = message.text
        caption += f"
📝 توضیح: {problem}"
        bot.send_message(ADMIN_ID, caption)
    elif message.content_type == "voice":
        bot.send_voice(ADMIN_ID, message.voice.file_id, caption=caption)

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🔁 شروع مجدد")
    bot.send_message(cid,
        "✅ اطلاعات شما با موفقیت ثبت شد.
"
        "کارشناسان ما در اسرع وقت با شما تماس خواهند گرفت.

"
        "☎️ برای مشاوره فوری:
09001003914",
        reply_markup=kb
    )

    users.pop(cid, None)

@bot.message_handler(func=lambda m: m.text == "🔁 شروع مجدد")
def restart(message):
    start(message)

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    return "Invalid request", 403

@app.route("/", methods=["GET"])
def index():
    return "Bot is online!", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
