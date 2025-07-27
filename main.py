from flask import Flask, request
import telebot
import threading
import time

API_TOKEN = '8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8'
ADMIN_ID = 7549512366

bot = telebot.TeleBot(API_TOKEN, threaded=True)
app = Flask(__name__)

user_states = {}
user_data = {}

TIMEOUT_SECONDS = 120
RESET_SECONDS = 300

def timeout_checker(chat_id, step):
    time.sleep(TIMEOUT_SECONDS)
    if user_states.get(chat_id) == step:
        bot.send_message(chat_id, "⏳ هنوز پاسخی دریافت نکردیم. لطفاً ادامه بده.")

    time.sleep(RESET_SECONDS - TIMEOUT_SECONDS)
    if user_states.get(chat_id) == step:
        bot.send_message(chat_id, "❗️مشاوره لغو شد. لطفاً مجدد شروع کن", reply_markup=start_markup())
        user_states.pop(chat_id, None)
        user_data.pop(chat_id, None)

def start_markup():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = telebot.types.KeyboardButton("بزن بریم 😍✅", request_contact=False)
    markup.add(btn)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام عزیزم ممنون از اعتمادتون 🌟
هلدینگ حقوقی الای در خدمت شماست.
برای رزرو مشاوره حقوقی لطفاً روی دکمه زیر بزنید.", reply_markup=start_markup())

@bot.message_handler(func=lambda m: m.text == "بزن بریم 😍✅")
def ask_phone(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn = telebot.types.KeyboardButton("📞 ارسال شماره تماس", request_contact=True)
    markup.add(btn)
    bot.send_message(message.chat.id, "شماره تماس‌تون رو لطفاً ارسال کنید:", reply_markup=markup)
    user_states[message.chat.id] = "awaiting_phone"
    threading.Thread(target=timeout_checker, args=(message.chat.id, "awaiting_phone")).start()

@bot.message_handler(content_types=['contact'])
def save_contact(message):
    if user_states.get(message.chat.id) == "awaiting_phone":
        user_data[message.chat.id] = {"phone": message.contact.phone_number}
        bot.send_message(message.chat.id, "نام و نام خانوادگی‌تون رو وارد کنید:")
        user_states[message.chat.id] = "awaiting_name"
        threading.Thread(target=timeout_checker, args=(message.chat.id, "awaiting_name")).start()

@bot.message_handler(func=lambda m: user_states.get(m.chat.id) == "awaiting_name")
def save_name(message):
    user_data[message.chat.id]["name"] = message.text
    bot.send_message(message.chat.id, "لطفاً مشکل خود را به‌صورت ویس یا پیام متنی بفرستید.")
    user_states[message.chat.id] = "awaiting_problem"
    threading.Thread(target=timeout_checker, args=(message.chat.id, "awaiting_problem")).start()

@bot.message_handler(content_types=['voice', 'text'])
def save_problem(message):
    if user_states.get(message.chat.id) == "awaiting_problem":
        user_data[message.chat.id]["problem"] = message.voice.file_id if message.content_type == 'voice' else message.text

        # ارسال برای ادمین
        info = user_data[message.chat.id]
        bot.send_message(ADMIN_ID, f"📥 درخواست جدید:

👤 نام: {info['name']}
📞 شماره: {info['phone']}")
        if "problem" in info:
            if message.content_type == 'voice':
                bot.send_voice(ADMIN_ID, info["problem"])
            else:
                bot.send_message(ADMIN_ID, f"📝 مشکل:
{info['problem']}")

        bot.send_message(message.chat.id, "✅ اطلاعات شما ثبت شد.
مشاورین ما در اسرع وقت تماس می‌گیرند.
در صورت نیاز فوری: 09001003914")
        user_states.pop(message.chat.id, None)
        user_data.pop(message.chat.id, None)

# Flask route for webhook (Render will call this)
@app.route(f"/{API_TOKEN}", methods=["POST"])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return '', 200

@app.route('/')
def home():
    return "ربات مشاوره حقوقی فعال است."

def run():
    bot.remove_webhook()
    bot.set_webhook(url=f"https://bot-llf5.onrender.com/{API_TOKEN}")
    app.run(host="0.0.0.0", port=10000)

if __name__ == "__main__":
    run()