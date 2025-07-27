import telebot
from flask import Flask, request, render_template_string

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_data = {}
user_states = {}

# تایمرها (خاموش: برای نسخه ساده)
# می‌توان با APScheduler اضافه کرد

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://bot-ll15.onrender.com/" + TOKEN)
    return "Webhook set!", 200

@app.route("/panel")
def admin_panel():
    password = request.args.get("pass")
    if password != "admin123":
        return "Unauthorized", 401
    html = "<h2>📋 لیست کاربران:</h2>"
    for uid, data in user_data.items():
        html += f"<p><b>{uid}</b>: {data}</p>"
    return render_template_string(html)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button = telebot.types.KeyboardButton(text="📞 ارسال شماره تماس", request_contact=True)
    markup.add(button)
    bot.send_message(message.chat.id, "سلام! لطفاً شماره تماس‌تان را ارسال کنید:", reply_markup=markup)
    user_states[message.chat.id] = "wait_contact"

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    if user_states.get(message.chat.id) == "wait_contact":
        user_data[message.chat.id] = {"phone": message.contact.phone_number}
        bot.send_message(message.chat.id, "✅ شماره دریافت شد. حالا نام کامل خود را وارد کنید.")
        user_states[message.chat.id] = "wait_name"
        bot.send_message(ADMIN_ID, f"📞 مخاطب جدید: {message.contact.phone_number}")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == "wait_name")
def get_name(message):
    user_data[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "✅ ثبت شد. منتظر تماس کارشناسان باشید.")
    bot.send_message(ADMIN_ID, f"👤 {message.text} نام کاربر
📞 {user_data[message.chat.id]['phone']}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)