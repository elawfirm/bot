import telebot
from flask import Flask, request
import os

TOKEN = os.getenv("TOKEN", "8010785406:AAFPInJ3QQmyNti9KwDxj075iOmVUhZJ364")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot-ltl5.onrender.com/webhook")
ADMIN_ID = 7549512366

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {}
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("⚖️ مشاوره حقوقی تخصصی", callback_data="legal"),
               telebot.types.InlineKeyboardButton("🔒 مشاوره کیفری", callback_data="criminal"))
    bot.send_message(cid, "⚖️ *خوش آمدید به elawfirm!* 📜\nما با تخصص بالا در کنار شما هستیم.\nلطفاً نوع مشاوره را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["legal", "criminal"])
def process_consultation_type(call):
    cid = call.message.chat.id
    print(f"Debug: Received callback data: {call.data} for chat {cid}")
    user_data[cid] = {"type": call.data, "step": "phone"}
    bot.answer_callback_query(call.id)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(telebot.types.KeyboardButton("📱 ارسال شماره"))
    bot.send_message(cid, "📞 لطفاً شماره تماس خود را وارد کنید یا دکمه زیر را بزنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'], func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone")
def handle_contact(message):
    cid = message.chat.id
    print(f"Debug: Received contact for chat {cid}, step: {user_data.get(cid, {}).get('step')}, phone: {message.contact.phone_number}")
    phone = message.contact.phone_number
    user_data[cid]["phone"] = phone
    user_data[cid]["step"] = "name"
    bot.send_message(cid, "✅ شماره شما ثبت شد. 📝 لطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone" and message.content_type == "text")
def handle_phone_text(message):
    cid = message.chat.id
    print(f"Debug: Received phone text for chat {cid}, phone: {message.text}")
    user_data[cid]["phone"] = message.text.strip()
    user_data[cid]["step"] = "name"
    bot.send_message(cid, "✅ شماره شما ثبت شد. 📝 لطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "name")
def handle_name(message):
    cid = message.chat.id
    user_data[cid]["name"] = message.text.strip()
    user_data[cid]["step"] = "details"
    if user_data[cid]["type"] == "legal":
        send_legal_questions(cid)
    else:
        send_criminal_questions(cid)

def send_legal_questions(cid):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🏛️ قراردادهای تجاری", callback_data="legal_contract"),
               telebot.types.InlineKeyboardButton("⚖️ دعاوی ملکی پیشرفته", callback_data="legal_property"))
    bot.send_message(cid, "🏛️ *مشاوره حقوقی تخصصی:* ⚖️\nلطفاً حوزه موردنظر را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["legal_contract", "legal_property"])
def process_legal_details(call):
    cid = call.message.chat.id
    user_data[cid]["details"] = call.data.replace("legal_", "")
    bot.answer_callback_query(call.id)
    bot.send_message(cid, "📝 لطفاً جزئیات دقیق (موضوع، مبلغ، طرفین، اسناد مرتبط) را وارد کنید:", parse_mode="Markdown")

def send_criminal_questions(cid):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🔍 جرایم مالی", callback_data="criminal_finance"),
               telebot.types.InlineKeyboardButton("🚨 جرایم خشونت‌آمیز", callback_data="criminal_violence"))
    bot.send_message(cid, "🔒 *مشاوره کیفری:* ⚖️\nلطفاً نوع جرم را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["criminal_finance", "criminal_violence"])
def process_criminal_details(call):
    cid = call.message.chat.id
    user_data[cid]["details"] = call.data.replace("criminal_", "")
    bot.answer_callback_query(call.id)
    bot.send_message(cid, "📝 لطفاً جزئیات (تاریخ، محل وقوع، افراد درگیر، مدارک) را وارد کنید:", parse_mode="Markdown")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "details")
def handle_details(message):
    cid = message.chat.id
    user_data[cid]["details"] = message.text
    name = user_data[cid].get("name", "نام ناشناخته")
    phone = user_data[cid].get("phone", "شماره ناشناخته")
    consultation_type = "مشاوره حقوقی تخصصی" if user_data[cid]["type"] == "legal" else "مشاوره کیفری"
    bot.send_message(ADMIN_ID, f"🔔 *درخواست جدید elawfirm:* ⚖️\n👤 {name}\n📱 {phone}\n🌐 {consultation_type}\n📝 {user_data[cid]['details']}", parse_mode="Markdown")
    bot.send_message(cid, "🎉 *درخواست شما با موفقیت ثبت شد!* ✅\n📞 تیم elawfirm در اسرع وقت تماس می‌گیرد.", parse_mode="Markdown")
    del user_data[cid]

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "", 403

import telebot.apihelper
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
