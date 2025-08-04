import telebot
from telebot import types
from flask import Flask, request
import os
from datetime import datetime
import pandas as pd
from io import BytesIO
import pyodbc

TOKEN = "8010785406:AAFPInJ3QQmyNti9KwDxj075iOmVUhZJ364"  # توکن ربات elawfirm
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://93.127.180.8:443/webhook"  # استفاده از IP VPS با پورت 443

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_data = {}

# پیام خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⚖️ مشاوره حقوقی", callback_data="legal"),
               types.InlineKeyboardButton("🌐 مهاجرت", callback_data="migration"))
    bot.send_message(cid, "⚖️ *خوش آمدید به elawfirm!* 📜\nما در کنار شما برای حل مسائل حقوقی و مهاجرتی هستیم.\nلطفاً نوع مشاوره را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

# پردازش انتخاب نوع مشاوره
@bot.callback_query_handler(func=lambda call: call.data in ["legal", "migration"])
def process_consultation_type(call):
    cid = call.message.chat.id
    user_data[cid] = {"type": call.data, "step": "phone"}
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 ارسال شماره"))
    bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text="🌟 انتخاب شما ثبت شد! ⚖️")
    bot.send_message(cid, "📞 شماره تماس خود را وارد کنید یا دکمه زیر را بزنید:", reply_markup=markup)

# دریافت شماره تماس
@bot.message_handler(content_types=['contact'], func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone")
def handle_contact(message):
    cid = message.chat.id
    phone = message.contact.phone_number
    user_data[cid]["phone"] = phone
    user_data[cid]["step"] = "name"
    markup = types.ReplyKeyboardRemove()
    bot.send_message(cid, "✅ شماره شما ثبت شد! 📜\n📝 نام و نام خانوادگی خود را وارد کنید:", reply_markup=markup)

# دریافت نام
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "name")
def handle_name(message):
    cid = message.chat.id
    user_data[cid]["name"] = message.text.strip()
    user_data[cid]["step"] = "details"
    if user_data[cid]["type"] == "legal":
        send_legal_questions(cid)
    else:
        send_migration_questions(cid)

# سوالات تخصصی برای مشاوره حقوقی
def send_legal_questions(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🏛️ قرارداد", callback_data="legal_contract"),
               types.InlineKeyboardButton("⚖️ دعاوی", callback_data="legal_dispute"))
    bot.send_message(cid, "🏛️ *نوع مشاوره حقوقی:* ⚖️\nلطفاً انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["legal_contract", "legal_dispute"])
def process_legal_details(call):
    cid = call.message.chat.id
    user_data[cid]["details"] = call.data.replace("legal_", "")
    bot.answer_callback_query(call.id)
    if call.data == "legal_contract":
        bot.send_message(cid, "📝 جزئیات قرارداد (نوع، مبلغ، طرفین) را وارد کنید:")
    elif call.data == "legal_dispute":
        bot.send_message(cid, "⚖️ توضیحات دعوا (موضوع، تاریخ) را بنویسید:")
    user_data[cid]["step"] = "final_details"

# سوالات تخصصی برای مهاجرت
def send_migration_questions(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌍 ویزای توریستی", callback_data="migration_tour"),
               types.InlineKeyboardButton("💼 ویزای کار", callback_data="migration_work"))
    bot.send_message(cid, "🌐 *نوع مشاوره مهاجرت:* ⚖️\nلطفاً انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["migration_tour", "migration_work"])
def process_migration_details(call):
    cid = call.message.chat.id
    user_data[cid]["details"] = call.data.replace("migration_", "")
    bot.answer_callback_query(call.id)
    if call.data == "migration_tour":
        bot.send_message(cid, "🌍 هدف سفر و مدت اقامت (روز) را وارد کنید:")
    elif call.data == "migration_work":
        bot.send_message(cid, "💼 شغل، تجربه کاری، و کشور مقصد را مشخص کنید:")
    user_data[cid]["step"] = "final_details"

# دریافت جزئیات نهایی
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "final_details")
def handle_final_details(message):
    cid = message.chat.id
    details = message.text
    user_data[cid]["details"] = details
    name = user_data[cid].get("name", "نام ناشناخته")
    phone = user_data[cid].get("phone", "شماره ناشناخته")
    consultation_type = "مشاوره حقوقی" if user_data[cid]["type"] == "legal" else "مشاوره مهاجرت"
    bot.send_message(ADMIN_ID, f"🔔 *درخواست جدید elawfirm:* ⚖️\n👤 {name}\n📱 {phone}\n🌐 {consultation_type}\n📝 {details}")
    send_completion(cid)

# پیام تکمیل
def send_completion(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 شروع مجدد", callback_data="restart"),
               types.InlineKeyboardButton("📋 تاریخچه", callback_data="history"))
    markup.add(types.InlineKeyboardButton("📊 اکسپورت اکسل", callback_data="export_excel"),
               types.InlineKeyboardButton("🗃️ اکسپورت Access", callback_data="export_access"))
    bot.send_message(cid, "🎉 *درخواست شما ثبت شد!* ✅\n📞 تیم elawfirm تماس می‌گیرد.\n⚖️ با ما پیش بروید!", parse_mode="Markdown", reply_markup=markup)
    del user_data[cid]

# پردازش دکمه‌ها
@bot.callback_query_handler(func=lambda call: call.data in ["restart", "history", "export_excel", "export_access"])
def process_callback(call):
    cid = call.message.chat.id
    if call.data == "restart":
        del user_data[cid]
        user_data[cid] = {}
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚖️ مشاوره حقوقی", callback_data="legal"),
                   types.InlineKeyboardButton("🌐 مهاجرت", callback_data="migration"))
        bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text="🔄 *روند ریست شد!* ⚖️ لطفاً انتخاب کنید.")
        bot.send_message(cid, "⚖️ *خوش آمدید به elawfirm!* 📜\nما در کنار شما هستیم.\nلطفاً نوع مشاوره را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)
    elif call.data == "history":
        requests = [(user_data[cid].get("name", "نام ناشناخته"), user_data[cid].get("phone", "شماره ناشناخته"), 
                     "مشاوره حقوقی" if user_data[cid].get("type") == "legal" else "مشاوره مهاجرت", 
                     user_data[cid].get("details", "بدون جزئیات"), datetime.now())]
        if requests[0][0] != "نام ناشناخته":
            history_text = "📋 *تاریخچه درخواست‌ها:* ⚖️\n"
            for req in requests:
                name, phone, consultation_type, details, timestamp = req
                history_text += f"🕒 {timestamp.strftime('%Y-%m-%d %H:%M')}\n👤 {name}\n📱 {phone}\n🌐 {consultation_type}\n📝 {details}\n---\n"
            bot.send_message(cid, history_text, parse_mode="Markdown")
        else:
            bot.send_message(cid, "📭 *هنوز درخواستی ثبت نشده!* 🌱\n⚖️ شروع کنید!")
    elif call.data == "export_excel":
        export_to_excel(cid)
    elif call.data == "export_access":
        export_to_access(cid)

# اکسپورت به اکسل
def export_to_excel(cid):
    requests = [(user_data[cid].get("name", "نام ناشناخته"), user_data[cid].get("phone", "شماره ناشناخته"), 
                 "مشاوره حقوقی" if user_data[cid].get("type") == "legal" else "مشاوره مهاجرت", 
                 user_data[cid].get("details", "بدون جزئیات"), datetime.now())]
    if requests[0][0] != "نام ناشناخته":
        df = pd.DataFrame([requests[0]], columns=["نام", "شماره تماس", "نوع مشاوره", "جزئیات", "زمان ثبت"])
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name="Consultations", index=False)
        output.seek(0)
        bot.send_document(cid, document=output, filename=f"elawfirm_history_{cid}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", caption="📊 *فایل اکسل!* ⚖️\nبررسی کنید.", parse_mode="Markdown")
    else:
        bot.send_message(cid, "📭 *داده‌ای وجود ندارد!* 🌱")

# اکسپورت به Access
def export_to_access(cid):
    requests = [(user_data[cid].get("name", "نام ناشناخته"), user_data[cid].get("phone", "شماره ناشناخته"), 
                 "مشاوره حقوقی" if user_data[cid].get("type") == "legal" else "مشاوره مهاجرت", 
                 user_data[cid].get("details", "بدون جزئیات"), datetime.now())]
    if requests[0][0] != "نام ناشناخته":
        conn_str = (
            r"DRIVER={Microsoft Access Driver (*.mdb, *.accdb)};"
            r"DBQ=elawfirm_backup_{}.accdb;".format(cid)
        )
        try:
            access_conn = pyodbc.connect(conn_str)
            cursor_access = access_conn.cursor()
            cursor_access.execute("CREATE TABLE Consultations (name TEXT, phone TEXT, consultation_type TEXT, details TEXT, timestamp DATETIME)")
            cursor_access.execute("INSERT INTO Consultations (name, phone, consultation_type, details, timestamp) VALUES (?, ?, ?, ?, ?)", 
                                  (requests[0][0], requests[0][1], requests[0][2], requests[0][3], requests[0][4]))
            access_conn.commit()
            cursor_access.close()
            access_conn.close()

            with open(f"elawfirm_backup_{cid}_{datetime.now().strftime('%Y%m%d_%H%M')}.accdb", "rb") as f:
                bot.send_document(cid, document=f, filename=f"elawfirm_backup_{cid}_{datetime.now().strftime('%Y%m%d_%H%M')}.accdb", caption="🗃️ *فایل Access!* ⚖️\nبررسی کنید.", parse_mode="Markdown")
            os.remove(f"elawfirm_backup_{cid}_{datetime.now().strftime('%Y%m%d_%H%M')}.accdb")
        except pyodbc.Error as e:
            bot.send_message(cid, f"❌ *خطا در ایجاد Access:* {str(e)}\n⚖️ درایور Access را نصب کنید!")
    else:
        bot.send_message(cid, "📭 *داده‌ای وجود ندارد!* 🌱")

# پیکربندی webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "", 403

@app.route("/")
def index():
    return "ربات elawfirm فعال است ⚖️"

# تنظیم اولیه Webhook
import telebot.apihelper
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)  # پورت محلی، Nginx ترافیک 443 رو مدیریت می‌کنه
