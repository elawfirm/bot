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
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://bot-ltl5.onrender.com"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# داده‌های کاربران
user_data = {}

# وضعیت‌ها
USER_STATES = {
    'START': 0,
    'PHONE': 1,
    'NAME': 2,
    'SUBAREA': 3,
    'DETAILS': 4,
    'CONFIRM': 5
}

# کیبورد اصلی
def main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📞 تماس با پشتیبانی", "ℹ️ درباره ما", "⚖️ درخواست مشاوره جدید")
    return markup

# اعتبارسنجی شماره تلفن ایرانی
def validate_iranian_phone_number(phone):
    import re
    pattern = r'^(\+98|0)?9\d{9}$'
    return re.match(pattern, phone) is not None

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
                handle_details_text(message)
            elif state == USER_STATES['CONFIRM']:
                handle_confirmation(message)
        else:
            bot.send_message(cid, "لطفاً از منوی زیر گزینه‌ای انتخاب کنید:", reply_markup=main_keyboard())

# شروع فرآیند مشاوره
def start_consultation_process(cid):
    user_data[cid] = {'state': USER_STATES['START']}
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("⚖️ حقوقی", callback_data="legal"),
        telebot.types.InlineKeyboardButton("🔒 کیفری", callback_data="criminal")
    )
    bot.send_message(cid, "لطفاً حوزه مشاوره را انتخاب کنید:", reply_markup=markup)

# مدیریت callback‌ها
@bot.callback_query_handler(func=lambda c: True)
def handle_callbacks(call):
    cid = call.message.chat.id
    data = call.data
    
    if data in ["legal", "criminal"]:
        user_data[cid] = {"type": data, "state": USER_STATES['PHONE']}
        bot.answer_callback_query(call.id)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True))
        bot.send_message(cid, "📞 شماره تماس خود را وارد کنید یا دکمه زیر را بزنید:", reply_markup=markup)
    
    elif data.startswith("legal_"):
        process_legal_subarea(call)
    elif data.startswith("criminal_"):
        process_criminal_subarea(call)

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
    if validate_iranian_phone_number(phone):
        user_data[cid]["phone"] = phone
        user_data[cid]["state"] = USER_STATES['NAME']
        bot.send_message(cid, "✅ شماره ثبت شد. لطفاً نام و نام خانوادگی را وارد کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())
    else:
        bot.send_message(cid, "❌ شماره معتبر نیست. لطفاً دوباره وارد کنید:")

# دریافت نام
def handle_name(message):
    cid = message.chat.id
    name = message.text.strip()
    if len(name) < 3:
        bot.send_message(cid, "❌ نام کوتاه است. لطفاً نام کامل را وارد کنید:")
        return
    user_data[cid]["name"] = name
    if user_data[cid]["type"] == "legal":
        user_data[cid]["state"] = USER_STATES['SUBAREA']
        send_legal_subareas(cid)
    else:
        user_data[cid]["state"] = USER_STATES['SUBAREA']
        send_criminal_types(cid)

# زیرشاخه‌های حقوقی
def send_legal_subareas(cid):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🏠 اموال", callback_data="legal_property"),
        telebot.types.InlineKeyboardButton("📝 قراردادها", callback_data="legal_contracts")
    )
    markup.add(
        telebot.types.InlineKeyboardButton("👨‍👩‍👧 خانواده", callback_data="legal_family"),
        telebot.types.InlineKeyboardButton("🕰️ ارث", callback_data="legal_inheritance")
    )
    bot.send_message(cid, "🏛️ *زیرشاخه حقوقی:* لطفاً انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

def process_legal_subarea(call):
    cid = call.message.chat.id
    subarea = call.data.replace("legal_", "")
    user_data[cid]["subarea"] = subarea
    user_data[cid]["state"] = USER_STATES['DETAILS']
    bot.answer_callback_query(call.id)
    messages = {
        "property": "🏠 جزئیات اموال و مالکیت را وارد کنید:",
        "contracts": "📝 جزئیات قراردادها را وارد کنید:",
        "family": "👨‍👩‍👧 جزئیات دعاوی خانواده را وارد کنید:",
        "inheritance": "🕰️ جزئیات ارث و وصیت را وارد کنید:"
    }
    bot.send_message(cid, messages.get(subarea, "لطفاً جزئیات را وارد کنید:"), parse_mode="Markdown")

# نوع جرایم کیفری
def send_criminal_types(cid):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        telebot.types.InlineKeyboardButton("🔍 جرایم مالی", callback_data="criminal_finance"),
        telebot.types.InlineKeyboardButton("🚨 جرایم خشونت‌آمیز", callback_data="criminal_violence")
    )
    bot.send_message(cid, "🔒 *نوع جرم را انتخاب کنید:*", parse_mode="Markdown", reply_markup=markup)

def process_criminal_subarea(call):
    cid = call.message.chat.id
    crime_type = call.data.replace("criminal_", "")
    user_data[cid]["subarea"] = crime_type
    user_data[cid]["state"] = USER_STATES['DETAILS']
    bot.answer_callback_query(call.id)
    messages = {
        "finance": "🔍 جزئیات جرایم مالی را وارد کنید:",
        "violence": "🚨 جزئیات جرایم خشونت‌آمیز را وارد کنید:"
    }
    bot.send_message(cid, messages.get(crime_type, "لطفاً جزئیات را وارد کنید:"), parse_mode="Markdown")

# دریافت جزئیات نهایی
def handle_details_text(message):
    cid = message.chat.id
    details = message.text.strip()
    user_data[cid]["details"] = details
    user_data[cid]["state"] = USER_STATES['CONFIRM']
    summary = f"""
✅ اطلاعات شما ثبت شد:

📞 شماره: {user_data[cid]['phone']}
👤 نام: {user_data[cid]['name']}
📌 حوزه: {user_data[cid]['type']}
📂 زیرشاخه: {user_data[cid]['subarea']}
📝 جزئیات: {details}

آیا تایید می‌کنید؟
"""
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("تایید ✅", "ویرایش 🔄")
    bot.send_message(cid, summary, reply_markup=markup)

# تایید یا ویرایش
def handle_confirmation(message):
    cid = message.chat.id
    text = message.text.strip()
    if text == "تایید ✅":
        send_to_admin(cid)
        bot.send_message(cid, "✅ مشاوره شما ثبت شد. به زودی با شما تماس می‌گیریم.", reply_markup=main_keyboard())
        user_data.pop(cid, None)
    elif text == "ویرایش 🔄":
        start_consultation_process(cid)
    else:
        bot.send_message(cid, "لطفاً یکی از گزینه‌ها را انتخاب کنید.")

def send_to_admin(cid):
    data = user_data[cid]
    msg = f"""
⚖️ درخواست مشاوره جدید:

📞 شماره: {data['phone']}
👤 نام: {data['name']}
📌 حوزه: {data['type']}
📂 زیرشاخه: {data['subarea']}
📝 جزئیات: {data['details']}
"""
    bot.send_message(ADMIN_ID, msg)

# Flask Webhook
@app.route('/', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'ok', 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=5000)
