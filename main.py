import telebot
from flask import Flask, request
import logging

# تنظیمات logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تنظیمات ربات
TOKEN = "8010785406:AAFPInJ3QQmyNti9KwDxj075iOmVUhZJ364"
WEBHOOK_URL = "https://bot-ltl5.onrender.com"
ADMIN_ID = 7549512366

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# داده‌های کاربران
user_data = {}

# وضعیت‌ها
USER_STATES = {
    'START': 0,
    'PHONE': 1,
    'NAME': 2,
    'AREA': 3,
    'DETAILS': 4
}

# کیبورد اصلی
def main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📞 تماس با پشتیبانی", "ℹ️ درباره ما", "⚖️ درخواست مشاوره جدید")
    return markup

# شروع ربات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {'state': USER_STATES['START']}
    welcome_text = """
⚖️ *خوش آمدید به elawfirm!* 📜

ما با تکیه بر دانش حقوقی عمیق، راه‌حل‌های دقیق ارائه می‌دهیم.

👈 برای شروع، لطفاً گزینه مورد نظر را انتخاب کنید:
"""
    bot.send_message(cid, welcome_text, parse_mode="Markdown", reply_markup=main_keyboard())

# مدیریت پیام‌های متنی
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    cid = message.chat.id
    text = message.text
    
    if text == "📞 تماس با پشتیبانی":
        bot.send_message(cid, "📞 تماس با پشتیبانی:\n☎️ 021-12345678\n🕒 9 صبح تا 5 عصر", reply_markup=main_keyboard())
    elif text == "ℹ️ درباره ما":
        bot.send_message(cid,
            "🏛️ *درباره elawfirm:*\nما گروهی از وکلای متخصص هستیم.\n✅ خدمات: مشاوره حقوقی، کیفری، لوایح و وکالت",
            parse_mode="Markdown", reply_markup=main_keyboard()
        )
    elif text == "⚖️ درخواست مشاوره جدید":
        start_consultation_process(cid)
    else:
        if cid in user_data:
            state = user_data[cid].get('state')
            if state == USER_STATES['PHONE']:
                handle_phone_text(message)
            elif state == USER_STATES['NAME']:
                handle_name(message)
            elif state == USER_STATES['DETAILS']:
                handle_details(message)
        else:
            bot.send_message(cid, "لطفاً از منوی زیر گزینه‌ای انتخاب کنید:", reply_markup=main_keyboard())

# شروع فرآیند مشاوره
def start_consultation_process(cid):
    user_data[cid] = {'state': USER_STATES['AREA']}
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("⚖️ حقوقی", callback_data="area_legal"),
        telebot.types.InlineKeyboardButton("🔒 کیفری", callback_data="area_criminal")
    )
    bot.send_message(cid, "لطفاً حوزه مشاوره را انتخاب کنید:", reply_markup=markup)

# سوالات جزئی
LEGAL_QUESTIONS = {
    "property": ["🏠 آیا ملک شما سند رسمی دارد؟", "📑 مشکل در اجاره‌نامه", "❌ سایر موارد"],
    "contracts": "📝 لطفاً جزئیات قرارداد خود را بنویسید:",
    "family": ["💍 طلاق توافقی", "👶 حضانت فرزند", "❌ سایر موارد"],
    "inheritance": "🕰️ جزئیات ارث و وصیت را وارد کنید:"
}

CRIMINAL_QUESTIONS = {
    "finance": ["💸 کلاهبرداری", "🏦 اختلاس", "❌ سایر موارد"],
    "violence": ["👊 درگیری فیزیکی", "🔪 تهدید", "❌ سایر موارد"]
}

# مدیریت callback‌ها
@bot.callback_query_handler(func=lambda c: True)
def handle_callbacks(call):
    cid = call.message.chat.id
    data = call.data
    bot.answer_callback_query(call.id)

    if data == "area_legal":
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("🏠 املاک", callback_data="legal_property"),
            telebot.types.InlineKeyboardButton("📝 قراردادها", callback_data="legal_contracts"),
            telebot.types.InlineKeyboardButton("👨‍👩‍👧 خانواده", callback_data="legal_family"),
            telebot.types.InlineKeyboardButton("🕰️ ارث و وصیت", callback_data="legal_inheritance"),
        )
        bot.send_message(cid, "لطفاً موضوع دقیق‌تر را انتخاب کنید:", reply_markup=markup)

    elif data == "area_criminal":
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("💰 جرائم مالی", callback_data="criminal_finance"),
            telebot.types.InlineKeyboardButton("🚨 خشونت", callback_data="criminal_violence"),
        )
        bot.send_message(cid, "لطفاً موضوع دقیق‌تر را انتخاب کنید:", reply_markup=markup)

    elif data.startswith("legal_"):
        sub = data.replace("legal_", "")
        user_data[cid]["subarea"] = sub
        user_data[cid]["state"] = USER_STATES['DETAILS']
        msg = LEGAL_QUESTIONS.get(sub, "لطفاً جزئیات را وارد کنید:")
        if isinstance(msg, list):
            send_option_question(cid, msg)
        else:
            bot.send_message(cid, msg)

    elif data.startswith("criminal_"):
        sub = data.replace("criminal_", "")
        user_data[cid]["subarea"] = sub
        user_data[cid]["state"] = USER_STATES['DETAILS']
        msg = CRIMINAL_QUESTIONS.get(sub, "لطفاً جزئیات را وارد کنید:")
        if isinstance(msg, list):
            send_option_question(cid, msg)
        else:
            bot.send_message(cid, msg)

    elif data.startswith("details_"):
        answer = data.replace("details_", "")
        user_data[cid]["details"] = answer
        bot.send_message(cid, f"✅ پاسخ شما ثبت شد: {answer}", reply_markup=main_keyboard())
        bot.send_message(ADMIN_ID, f"کاربر {user_data[cid].get('name','ناشناس')} شماره {user_data[cid].get('phone','---')}:\n{answer}")

# ارسال سوال گزینه‌ای
def send_option_question(cid, options):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for opt in options:
        markup.add(telebot.types.InlineKeyboardButton(opt, callback_data=f"details_{opt}"))
    bot.send_message(cid, "لطفاً گزینه مورد نظر را انتخاب کنید یا متن خود را وارد کنید:", reply_markup=markup)

# دریافت شماره تماس از دکمه
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    cid = message.chat.id
    if cid in user_data and user_data[cid].get('state') == USER_STATES['PHONE']:
        user_data[cid]["phone"] = message.contact.phone_number
        user_data[cid]["state"] = USER_STATES['NAME']
        bot.send_message(cid, "✅ شماره ثبت شد. لطفاً نام و نام خانوادگی را وارد کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())

# دریافت شماره تماس متنی
def handle_phone_text(message):
    cid = message.chat.id
    phone = message.text.strip()
    user_data[cid]["phone"] = phone
    user_data[cid]["state"] = USER_STATES['NAME']
    bot.send_message(cid, "✅ شماره ثبت شد. لطفاً نام و نام خانوادگی را وارد کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())

# دریافت نام
def handle_name(message):
    cid = message.chat.id
    name = message.text.strip()
    user_data[cid]["name"] = name
    user_data[cid]["state"] = USER_STATES['DETAILS']
    bot.send_message(cid, "✅ نام ثبت شد. لطفاً جزئیات مشکل خود را وارد کنید یا از گزینه‌ها انتخاب کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())

# دریافت جزئیات
def handle_details(message):
    cid = message.chat.id
    details = message.text.strip()
    user_data[cid]["details"] = details
    bot.send_message(cid, "✅ اطلاعات شما ثبت شد. به زودی با شما تماس خواهیم گرفت.", reply_markup=main_keyboard())
    bot.send_message(ADMIN_ID, f"کاربر {user_data[cid].get('name','ناشناس')} شماره {user_data[cid].get('phone','---')}:\n{details}")

# Flask webhook
@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '!', 200

# تنظیم Webhook
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
