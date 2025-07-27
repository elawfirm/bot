from flask import Flask, request, jsonify, render_template_string
import telebot
import threading

API_TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_data = {}

HTML_TEMPLATE = '''<!doctype html>
<title>پنل مدیریت</title>
<h2>لیست کاربران:</h2>
<ul>
{% for user_id, info in users.items() %}
  <li><b>{{ user_id }}</b>: {{ info }}</li>
{% endfor %}
</ul>
'''

@app.route('/')
def index():
    return 'ربات فعال است'

@app.route('/panel')
def panel():
    password = request.args.get("pass")
    if password == "admin123":
        return render_template_string(HTML_TEMPLATE, users=user_data)
    return "Access Denied"

@app.route(f"/{API_TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json()
    if json_data:
        update = telebot.types.Update.de_json(json_data)
        bot.process_new_updates([update])
    return jsonify({"ok": True})

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data[message.chat.id] = {"name": message.from_user.first_name}
    bot.send_message(message.chat.id, "سلام عزیزم! لطفاً شماره‌تماس‌ت رو بفرست 📞", reply_markup=request_contact_btn())
    bot.send_message(ADMIN_ID, f"🟢 کاربر جدید:\nنام: {message.from_user.first_name}\nآیدی: {message.chat.id}")

@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    if message.contact:
        user_data[message.chat.id]["phone"] = message.contact.phone_number
        bot.send_message(message.chat.id, "✅ شماره دریافت شد، مشکلت رو بفرست.")
        bot.send_message(ADMIN_ID, f"📞 شماره از {message.chat.id}: {message.contact.phone_number}")

@bot.message_handler(content_types=['text', 'voice'])
def text_handler(message):
    bot.send_message(ADMIN_ID, f"📩 پیام از {message.chat.id}: {message.text or 'ویس دریافت شد'}")
    bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)

def request_contact_btn():
    btn = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn.add(telebot.types.KeyboardButton("📞 ارسال شماره", request_contact=True))
    return btn

def run_bot():
    bot.remove_webhook()
    bot.set_webhook(url="https://bot-ll15.onrender.com/" + API_TOKEN)

threading.Thread(target=run_bot).start()