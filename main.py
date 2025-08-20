import telebot
from flask import Flask, request, jsonify
import os
import re
import logging
from datetime import datetime

# تنظیمات logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تنظیمات ربات
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    logger.error("TOKEN environment variable is not set!")
    exit(1)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
if not WEBHOOK_URL:
    logger.error("WEBHOOK_URL environment variable is not set!")
    exit(1)

ADMIN_ID = os.getenv("ADMIN_ID")
if not ADMIN_ID:
    logger.error("ADMIN_ID environment variable is not set!")
    exit(1)

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    logger.error("ADMIN_ID must be an integer!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# دیکشنری برای ذخیره داده کاربران (در محیط production از دیتابیس استفاده کنید)
user_data = {}

# وضعیت‌های مختلف کاربر
USER_STATES = {
    'START': 0,
    'PHONE': 1,
    'NAME': 2,
    'DETAILS': 3,
    'SUBAREA': 4
}

# کیبورد اصلی
def main_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📞 تماس با پشتیبانی", "ℹ️ درباره ما", "⚖️ درخواست مشاوره جدید")
    return markup

# اعتبارسنجی شماره تلفن ایرانی
def validate_iranian_phone_number(phone):
    pattern = r'^(\+98|0)?9\d{9}$'
    return re.match(pattern, phone) is not None

# شروع ربات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        cid = message.chat.id
        user_data[cid] = {'state': USER_STATES['START']}
        
        welcome_text = """
        ⚖️ *خوش آمدید به elawfirm!* 📜
        
        ما با تکیه بر دانش حقوقی عمیق، راه‌حل‌های دقیق ارائه می‌دهیم.
        
        👈 برای شروع، لطفاً گزینه مورد نظر را انتخاب کنید:
        """
        
        bot.send_message(
            cid, 
            welcome_text, 
            parse_mode="Markdown", 
            reply_markup=main_keyboard()
        )
    except Exception as e:
        logger.error(f"Error in send_welcome: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# مدیریت تمام پیام‌های متنی
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    try:
        cid = message.chat.id
        text = message.text
        
        if text == "📞 تماس با پشتیبانی":
            bot.send_message(
                cid, 
                "📞 برای تماس با پشتیبانی می‌توانید با شماره زیر ارتباط برقرار کنید:\n\n"
                "☎️ 021-12345678\n"
                "🕒 ساعت پاسخگویی: 9 صبح تا 5 عصر",
                reply_markup=main_keyboard()
            )
        
        elif text == "ℹ️ درباره ما":
            bot.send_message(
                cid,
                "🏛️ *درباره elawfirm:*\n\n"
                "ما گروهی از وکلای متخصص و با تجربه هستیم که با هدف ارائه خدمات حقوقی و کیفری به صورت تخصصی فعالیت می‌کنیم.\n\n"
                "✅ *خدمات ما:*\n"
                "• مشاوره حقوقی تخصصی\n"
                "• مشاوره کیفری\n"
                "• تنظیم لوایح و دادخواست\n"
                "• وکالت در دادگاه‌ها\n\n"
                "اعضای تیم ما دارای سال‌ها تجربه در پرونده‌های مختلف هستند.",
                parse_mode="Markdown",
                reply_markup=main_keyboard()
            )
        
        elif text == "⚖️ درخواست مشاوره جدید":
            start_consultation_process(cid)
        
        else:
            # بررسی وضعیت کاربر و هدایت به مرحله مناسب
            if cid in user_data:
                state = user_data[cid].get('state')
                
                if state == USER_STATES['PHONE']:
                    handle_phone_text(message)
                
                elif state == USER_STATES['NAME']:
                    handle_name(message)
                
                elif state == USER_STATES['DETAILS']:
                    handle_details(message)
            
            else:
                bot.send_message(
                    cid, 
                    "لطفاً از منوی زیر یک گزینه را انتخاب کنید:",
                    reply_markup=main_keyboard()
                )
    
    except Exception as e:
        logger.error(f"Error in handle_all_messages: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# شروع فرآیند مشاوره
def start_consultation_process(cid):
    try:
        user_data[cid] = {'state': USER_STATES['START']}
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("⚖️ مشاوره حقوقی تخصصی", callback_data="legal"),
            telebot.types.InlineKeyboardButton("🔒 مشاوره کیفری", callback_data="criminal")
        )
        
        bot.send_message(
            cid, 
            "لطفاً حوزه موردنظر را انتخاب کنید:", 
            parse_mode="Markdown", 
            reply_markup=markup
        )
    except Exception as e:
        logger.error(f"Error in start_consultation_process: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# مدیریت callback‌ها
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    try:
        cid = call.message.chat.id
        data = call.data
        
        if data in ["legal", "criminal"]:
            user_data[cid] = {
                "type": data,
                "state": USER_STATES['PHONE']
            }
            
            bot.answer_callback_query(call.id)
            
            markup = telebot.types.ReplyKeyboardMarkup(
                resize_keyboard=True, 
                one_time_keyboard=True
            )
            markup.add(telebot.types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True))
            
            bot.send_message(
                cid, 
                "📞 لطفاً شماره تماس خود را وارد کنید یا دکمه زیر را بزنید:",
                reply_markup=markup
            )
        
        elif data.startswith("legal_"):
            process_legal_details(call)
        
        elif data.startswith("criminal_"):
            process_criminal_details(call)
    
    except Exception as e:
        logger.error(f"Error in handle_callbacks: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# مدیریت دریافت شماره تماس از دکمه
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    try:
        cid = message.chat.id
        
        if cid in user_data and user_data[cid].get('state') == USER_STATES['PHONE']:
            phone = message.contact.phone_number
            user_data[cid]["phone"] = phone
            user_data[cid]["state"] = USER_STATES['NAME']
            
            bot.send_message(
                cid, 
                "✅ شماره شما ثبت شد.\n📝 لطفاً نام و نام خانوادگی خود را وارد کنید:",
                reply_markup=telebot.types.ReplyKeyboardRemove()
            )
    
    except Exception as e:
        logger.error(f"Error in handle_contact: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# مدیریت دریافت شماره تماس به صورت متنی
def handle_phone_text(message):
    try:
        cid = message.chat.id
        phone = message.text.strip()
        
        if validate_iranian_phone_number(phone):
            user_data[cid]["phone"] = phone
            user_data[cid]["state"] = USER_STATES['NAME']
            
            bot.send_message(
                cid, 
                "✅ شماره شما ثبت شد.\n📝 لطفاً نام و نام خانوادگی خود را وارد کنید:",
                reply_markup=telebot.types.ReplyKeyboardRemove()
            )
        else:
            bot.send_message(
                cid, 
                "❌ شماره تماس معتبر نیست.\nلطفاً شماره تماس خود را به درستی وارد کنید (مانند 09123456789):"
            )
    
    except Exception as e:
        logger.error(f"Error in handle_phone_text: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# مدیریت دریافت نام کاربر
def handle_name(message):
    try:
        cid = message.chat.id
        name = message.text.strip()
        
        if len(name) < 3:
            bot.send_message(cid, "❌ نام وارد شده بسیار کوتاه است. لطفاً نام کامل خود را وارد کنید:")
            return
        
        user_data[cid]["name"] = name
        
        if user_data[cid]["type"] == "legal":
            user_data[cid]["state"] = USER_STATES['SUBAREA']
            send_legal_subareas(cid)
        else:
            user_data[cid]["state"] = USER_STATES['DETAILS']
            send_criminal_questions(cid)
    
    except Exception as e:
        logger.error(f"Error in handle_name: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# ارسال زیرشاخه‌های حقوقی
def send_legal_subareas(cid):
    try:
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("🏠 اموال و مالکیت", callback_data="legal_property"),
            telebot.types.InlineKeyboardButton("📝 تعهدات و قراردادها", callback_data="legal_contracts")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("👨‍👩‍👧 دعاوی خانواده", callback_data="legal_family"),
            telebot.types.InlineKeyboardButton("🕰️ ارث و وصیت", callback_data="legal_inheritance")
        )
        markup.add(
            telebot.types.InlineKeyboardButton("🏢 شرکت‌ها و اشخاص حقوقی", callback_data="legal_company"),
            telebot.types.InlineKeyboardButton("🛡️ مسئولیت مدنی", callback_data="legal_civil_liability")
        )
        
        bot.send_message(
            cid, 
            "🏛️ *حوزه‌های تخصصی حقوقی:* ⚖️\nلطفاً حوزه موردنظر را انتخاب کنید:",
            parse_mode="Markdown", 
            reply_markup=markup
        )
    
    except Exception as e:
        logger.error(f"Error in send_legal_subareas: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# پردازش جزئیات حقوقی
def process_legal_details(call):
    try:
        cid = call.message.chat.id
        subarea = call.data.replace("legal_", "")
        user_data[cid]["subarea"] = subarea
        user_data[cid]["state"] = USER_STATES['DETAILS']
        
        bot.answer_callback_query(call.id)
        
        # تعیین پیام بر اساس زیرشاخه انتخاب شده
        messages = {
            "property": "🏠 *اموال و مالکیت:* ⚖️\nلطفاً جزئیات (نام اموال، مالکیت مورد مناقشه، اسناد موجود، طرفین درگیر) را وارد کنید:",
            "contracts": "📝 *تعهدات و قراردادها:* ⚖️\nلطفاً جزئیات (نوع قرارداد، تعهدات طرفین، مبلغ، تاریخ انعقاد، مشکلات حقوقی پیش‌آمده) را وارد کنید:",
            "family": "👨‍👩‍👧 *دعاوی خانواده:* ⚖️\nلطفاً جزئیات (نوع دعوا مانند طلاق، حضانت، نفقه، طرفین، مدارک خانوادگی) را وارد کنید:",
            "inheritance": "🕰️ *ارث و وصیت:* ⚖️\nلطفاً جزئیات (نام متوفی، وارثان، محتوای وصیت‌نامه، اموال مورد ارث، مشکلات تقسیم) را وارد کنید:",
            "company": "🏢 *شرکت‌ها و اشخاص حقوقی:* ⚖️\nلطفاً جزئیات (نوع شرکت، سهامداران، قراردادهای شرکتی، دعاوی مرتبط، وضعیت ثبت) را وارد کنید:",
            "civil_liability": "🛡️ *مسئولیت مدنی:* ⚖️\nلطفاً جزئیات (نوع مسئولیت، خسارت واردشده، طرفین، مدارک اثبات تقصیر) را وارد کنید:"
        }
        
        bot.send_message(cid, messages.get(subarea, "لطفاً جزئیات درخواست خود را وارد کنید:"), parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"Error in process_legal_details: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# ارسال سوالات کیفری
def send_criminal_questions(cid):
    try:
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            telebot.types.InlineKeyboardButton("🔍 جرایم مالی", callback_data="criminal_finance"),
            telebot.types.InlineKeyboardButton("🚨 جرایم خشونت‌آمیز", callback_data="criminal_violence")
        )
        
        bot.send_message(
            cid, 
            "🔒 *مشاوره کیفری:* ⚖️\nلطفاً نوع جرم را انتخاب کنید:",
            parse_mode="Markdown", 
            reply_markup=markup
        )
    
    except Exception as e:
        logger.error(f"Error in send_criminal_questions: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# پردازش جزئیات کیفری
def process_criminal_details(call):
    try:
        cid = call.message.chat.id
        crime_type = call.data.replace("criminal_", "")
        user_data[cid]["crime_type"] = crime_type
        user_data[cid]["state"] = USER_STATES['DETAILS']
        
        bot.answer_callback_query(call.id)
        
        messages = {
            "finance": "🔍 *جرایم مالی:* ⚖️\nلطفاً جزئیات (مبلغ، تاریخ، نحوه ارتکاب، افراد درگیر، مدارک) را وارد کنید:",
            "violence": "🚨 *جرایم خشونت‌آمیز:* ⚖️\nلطفاً جزئیات (تاریخ، محل وقوع، نوع خشونت، افراد درگیر، مدارک) را وارد کنید:"
        }
        
        bot.send_message(
            cid, 
            messages.get(crime_type, "لطفاً جزئیات را وارد کنید:"), 
            parse_mode="Markdown"
        )
    
    except Exception as e:
        logger.error(f"Error in process_criminal_details: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# مدیریت دریافت جزئیات درخواست
def handle_details(message):
    try:
        cid = message.chat.id
        
        if cid not in user_data:
            bot.send_message(cid, "❌ اطلاعات شما یافت نشد. لطفاً دوباره شروع کنید.", reply_markup=main_keyboard())
            return
        
        user_data[cid]["details"] = message.text
        name = user_data[cid].get("name", "نام ناشناخته")
        phone = user_data[cid].get("phone", "شماره ناشناخته")
        consultation_type = "مشاوره حقوقی تخصصی" if user_data[cid]["type"] == "legal" else "مشاوره کیفری"
        
        # ایجاد پیام برای ادمین
        admin_message = f"🔔 *درخواست جدید elawfirm:* ⚖️\n\n"
        admin_message += f"👤 *نام:* {name}\n"
        admin_message += f"📱 *شماره تماس:* {phone}\n"
        admin_message += f"🌐 *نوع مشاوره:* {consultation_type}\n"
        
        if user_data[cid]["type"] == "legal":
            subarea = user_data[cid].get("subarea", "نامشخص")
            subarea_names = {
                "property": "اموال و مالکیت",
                "contracts": "تعهدات و قراردادها",
                "family": "دعاوی خانواده",
                "inheritance": "ارث و وصیت",
                "company": "شرکت‌ها و اشخاص حقوقی",
                "civil_liability": "مسئولیت مدنی"
            }
            admin_message += f"📂 *زیرحوزه:* {subarea_names.get(subarea, subarea)}\n"
        else:
            crime_type = user_data[cid].get("crime_type", "نامشخص")
            crime_names = {
                "finance": "جرایم مالی",
                "violence": "جرایم خشونت‌آمیز"
            }
            admin_message += f"📂 *نوع جرم:* {crime_names.get(crime_type, crime_type)}\n"
        
        admin_message += f"📝 *جزئیات:* {user_data[cid]['details']}\n\n"
        admin_message += f"🕒 *زمان ثبت:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # ارسال به ادمین
        bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")
        
        # ارسال تأیید به کاربر
        bot.send_message(
            cid, 
            "🎉 *درخواست شما با موفقیت ثبت شد!* ✅\n\n"
            "📞 تیم elawfirm در اسرع وقت با شما تماس خواهد گرفت.\n\n"
            "برای ارسال درخواست جدید می‌توانید از منوی زیر استفاده کنید:",
            parse_mode="Markdown", 
            reply_markup=main_keyboard()
        )
        
        # حذف اطلاعات کاربر از حافظه موقت
        if cid in user_data:
            del user_data[cid]
    
    except Exception as e:
        logger.error(f"Error in handle_details: {e}")
        bot.send_message(cid, "⚠️ خطایی رخ داده است. لطفاً دوباره تلاش کنید.")

# وب‌هوک برای Flask
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        if request.headers.get("content-type") == "application/json":
            json_string = request.get_data().decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return jsonify({"status": "success"}), 200
        return jsonify({"error": "Invalid content type"}), 403
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"error": str(e)}), 500

# صفحه اصلی برای بررسی سلامت سرور
@app.route("/")
def index():
    return "Elawfirm Bot is running!"

# تنظیم وب‌هوک
@app.before_first_request
def setup_webhook():
    try:
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        logger.info("Webhook set successfully")
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("DEBUG", "False").lower() == "true")
