
import telebot
from flask import Flask, request, render_template_string

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

user_data = {}

# پیغام شروع
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_data[chat_id] = {'step': 'name'}
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    button = telebot.types.KeyboardButton("📞 ارسال شماره تماس", request_contact=True)
    markup.add(button)
    bot.send_message(chat_id, "سلام 👋 به ربات حقوقی خوش اومدی. لطفا نام کاملت رو وارد کن:", reply_markup=markup)
    bot.send_message(ADMIN_ID, f"کاربر جدید شروع کرد: {message.from_user.first_name}")

# دریافت پیام کاربر و هدایت مرحله‌ای
@bot.message_handler(func=lambda m: True, content_types=['text', 'contact', 'voice'])
def messages(message):
    chat_id = message.chat.id

    if chat_id not in user_data:
        user_data[chat_id] = {'step': 'name'}
        bot.send_message(chat_id, "لطفا /start را بزنید.")
        return

    step = user_data[chat_id]['step']

    if message.content_type == 'contact':
        user_data[chat_id]['contact'] = message.contact.phone_number
        bot.send_message(chat_id, "لطفا مشکلت را به صورت صوتی یا متنی بنویس:")
        user_data[chat_id]['step'] = 'problem'
        return

    if message.content_type == 'voice':
        file_id = message.voice.file_id
        bot.send_message(ADMIN_ID, f"ویس از {message.from_user.first_name}")
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.send_message(chat_id, "ویس شما ارسال شد ✅")
        return

    if step == 'name':
        user_data[chat_id]['name'] = message.text
        bot.send_message(chat_id, "لطفا شماره تماست را با زدن دکمه زیر ارسال کن.")
        user_data[chat_id]['step'] = 'contact'
        return

    if step == 'problem':
        user_data[chat_id]['problem'] = message.text
        bot.send_message(chat_id, "✅ اطلاعات شما ثبت شد. منتظر پاسخ باشید.")
        info = user_data[chat_id]
        bot.send_message(ADMIN_ID, f"📩 اطلاعات جدید:
👤 نام: {info.get('name')}
📞 شماره: {info.get('contact')}
📝 مشکل: {info.get('problem')}")
        user_data.pop(chat_id)

# پنل ساده با رمز عبور
@app.route("/panel")
def panel():
    if request.args.get("pass") != "admin123":
        return "⛔️ دسترسی غیرمجاز"
    return render_template_string("""
        <h2>🟢 ربات فعال است</h2>
        <p>برای دریافت اطلاعات کاربران به تلگرام ادمین بروید.</p>
    """)

# ست کردن webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "ok", 200

# اجرای اولیه
if __name__ == "__main__":
    import os
    bot.remove_webhook()
    bot.set_webhook(url=f"https://bot-l1l5.onrender.com/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
