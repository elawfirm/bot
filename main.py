import telebot
from flask import Flask, request, render_template_string
import os
from werkzeug.middleware.proxy_fix import ProxyFix

# تنظیم متغیرهای محیطی
TOKEN = os.environ.get('TELEGRAM_TOKEN', '8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8')
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7549512366'))
ADMIN_PASS = os.environ.get('ADMIN_PASS', 'admin123')  # بهتر است رمز قوی‌تری تنظیم شود

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)  # برای پشتیبانی از پراکسی‌های Render

user_data = {}
user_states = {}

# تنظیم Webhook فقط یک بار
def set_webhook():
    webhook_url = os.environ.get('WEBHOOK_URL', 'https://bot-ll15.onrender.com/') + TOKEN
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    print(f"Webhook set to {webhook_url}")

@app.route('/' + TOKEN, methods=['POST'])
def get_message():
    try:
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print(f"Error processing update: {e}")
        return "Error", 500

@app.route("/")
def webhook():
    set_webhook()
    return "Webhook set!", 200

@app.route("/panel")
def admin_panel():
    password = request.args.get("pass")
    if password != ADMIN_PASS:
        return "Unauthorized", 401
    html = "<h2>📋 لیست کاربران:</h2>"
    for uid, data in user_data.items():
        # جلوگیری از XSS
        safe_name = data.get('name', '').replace('<', '&lt;').replace('>', '&gt;')
        safe_phone = data.get('phone', '').replace('<', '&lt;').replace('>', '&gt;')
        html += f"<p><b>{uid}</b>: Name: {safe_name}, Phone: {safe_phone}</p>"
    return render_template_string(html)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        markup = telebot.types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        button = telebot.types.KeyboardButton(text="📞 ارسال شماره تماس", request_contact=True)
        markup.add(button)
        bot.send_message(message.chat.id, "سلام! لطفاً شماره تماس‌تان را ارسال کنید:", reply_markup=markup)
        user_states[message.chat.id] = "wait_contact"
    except Exception as e:
        print(f"Error in send_welcome: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

@bot.message_handler(content_types=['contact'])
def get_contact(message):
    try:
        if user_states.get(message.chat.id) == "wait_contact":
            user_data[message.chat.id] = {"phone": message.contact.phone_number}
            bot.send_message(message.chat.id, "✅ شماره دریافت شد. حالا نام کامل خود را وارد کنید.")
            user_states[message.chat.id] = "wait_name"
            bot.send_message(ADMIN_ID, f"📞 مخاطب جدید: {message.contact.phone_number}")
        else:
            bot.send_message(message.chat.id, "لطفاً ابتدا دستور /start را اجرا کنید.")
    except Exception as e:
        print(f"Error in get_contact: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == "wait_name")
def get_name(message):
    try:
        if not message.text:
            bot.send_message(message.chat.id, "لطفاً یک نام معتبر وارد کنید.")
            return
        user_data[message.chat.id]["name"] = message.text
        bot.send_message(message.chat.id, "✅ ثبت شد. منتظر تماس کارشناسان باشید.")
        bot.send_message(ADMIN_ID, f"👤 نام کاربر: {message.text}\n📞 شماره: {user_data[message.chat.id]['phone']}")
        user_states.pop(message.chat.id, None)  # پاک کردن حالت کاربر
    except Exception as e:
        print(f"Error in get_name: {e}")
        bot.send_message(message.chat.id, "خطایی رخ داد. لطفاً دوباره امتحان کنید.")

if __name__ == "__main__":
    # تنظیم Webhook هنگام شروع
    set_webhook()
    # استفاده از پورت تخصیص‌یافته توسط Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host="0.0.0.0", port=port)
