# -*- coding: utf-8 -*-
import os
import sqlite3
import csv
from flask import Flask, request, send_from_directory
import telebot

# -------------------- تنظیمات --------------------
TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
ADMIN_PASS = "admin123"   # رمز ورود به پنل
PORT = int(os.environ.get("PORT", 10000))  # برای Render

# -------------------- بوت تلگرام --------------------
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

# -------------------- دیتابیس --------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            problem TEXT,
            voice_file TEXT
        )
        """
    )
    conn.commit()
    conn.close()

def save_user(chat_id, name, phone, problem, voice_file):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO users (user_id, name, phone, problem, voice_file) VALUES (?, ?, ?, ?, ?)",
        (chat_id, name, phone, problem, voice_file),
    )
    conn.commit()
    conn.close()

init_db()
os.makedirs("voices", exist_ok=True)

# -------------------- state کاربران --------------------
user_state = {}  # chat_id -> step
user_buf   = {}  # chat_id -> temp data

# -------------------- توابع کمکی --------------------
def start_keyboard():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(telebot.types.KeyboardButton("بزن بریم 😍✅"))
    return kb

def phone_keyboard():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(telebot.types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True))
    return kb

# -------------------- هندلرهای تلگرام --------------------
@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(
        message.chat.id,
        "سلام عزیزم، ممنون از اعتمادتون 🌟\n"
        "هلدینگ حقوقی اِلای در خدمت شماست.\n\n"
        "برای رزرو وقت مشاوره حقوقی، روی دکمه زیر بزنید.",
        reply_markup=start_keyboard()
    )

@bot.message_handler(func=lambda m: m.text == "بزن بریم 😍✅")
def ask_phone(message):
    chat_id = message.chat.id
    user_state[chat_id] = "phone"
    user_buf[chat_id] = {}
    bot.send_message(chat_id, "📞 لطفاً شماره تماس خود را ارسال کنید (می‌توانید از دکمه میانبر استفاده کنید):", reply_markup=phone_keyboard())

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    chat_id = message.chat.id
    if user_state.get(chat_id) == "phone":
        phone = message.contact.phone_number
        user_buf[chat_id]["phone"] = phone
        user_state[chat_id] = "name"
        bot.send_message(chat_id, f"📞 شماره شما ثبت شد: {phone}\n\n👤 لطفاً نام و نام خانوادگی خود را وارد کنید:",
                         reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "phone", content_types=["text"])
def phone_text_handler(message):
    chat_id = message.chat.id
    phone = message.text.strip()
    user_buf.setdefault(chat_id, {})["phone"] = phone
    user_state[chat_id] = "name"
    bot.send_message(chat_id, f"📞 شماره شما ثبت شد: {phone}\n\n👤 لطفاً نام و نام خانوادگی خود را وارد کنید:",
                     reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "name", content_types=["text"])
def name_handler(message):
    chat_id = message.chat.id
    user_buf[chat_id]["name"] = message.text.strip()
    user_state[chat_id] = "problem"
    bot.send_message(chat_id, "📝 لطفاً مشکل یا موضوع حقوقی خود را به صورت *متن یا ویس* ارسال کنید:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "problem", content_types=["text", "voice"])
def problem_handler(message):
    chat_id = message.chat.id

    voice_path = None
    if message.content_type == "voice":
        file_info = bot.get_file(message.voice.file_id)
        voice_path = f"voices/{chat_id}_{message.voice.file_id}.ogg"
        data = bot.download_file(file_info.file_path)
        with open(voice_path, "wb") as f:
            f.write(data)
        problem_text = "Voice Message"
    else:
        problem_text = message.text

    info = user_buf.get(chat_id, {})
    name  = info.get("name", "-")
    phone = info.get("phone", "-")

    # ذخیره در DB
    save_user(chat_id, name, phone, problem_text, voice_path)

    # اطلاع به ادمین
    notify = (
        "🔔 *درخواست جدید مشاوره*\n"
        f"👤 نام: {name}\n"
        f"📞 شماره: {phone}\n"
        f"📝 مشکل: {'ویس ارسال شد' if voice_path else problem_text}"
    )
    bot.send_message(ADMIN_ID, notify)
    if voice_path:
        with open(voice_path, "rb") as vf:
            bot.send_voice(ADMIN_ID, vf)

    bot.send_message(
        chat_id,
        "✅ اطلاعات شما با موفقیت ثبت شد.\n"
        "کارشناسان ما در اسرع وقت با شما تماس می‌گیرند.\n\n"
        "☎️ در صورت نیاز فوری: 09001003914",
    )

    # پاک کردن state
    user_state.pop(chat_id, None)
    user_buf.pop(chat_id, None)

# -------------------- مسیرهای Flask --------------------
from flask import Flask, request, jsonify, send_file
import telebot
import os

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/panel", methods=['GET'])
def panel():
    password = request.args.get("pass")
    if password != "admin123":
        return "Access Denied", 403
    return "<h1>Legal Bot Panel</h1><p>اطلاعات کاربران در اینجا نمایش داده می‌شود.</p>"

@app.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://bot-ll15.onrender.com/" + TOKEN)
    return "Webhook set", 200


@app.route("/panel")
def panel():
    password = request.args.get("pass", "")
    if password != ADMIN_PASS:
        return "<h3 style='direction:rtl;font-family:tahoma'>رمز نادرست است. ?pass=admin123 را اضافه کنید.</h3>"

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, name, phone, problem, voice_file FROM users ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    html = [
        "<html><head><meta charset='utf-8'><title>پنل مدیریت</title>",
        "<style>body{direction:rtl;font-family:tahoma} table{width:100%;border-collapse:collapse} td,th{border:1px solid #ccc;padding:6px;text-align:center} th{background:#333;color:#fff}</style>",
        "</head><body>",
        "<h2>پنل مدیریت درخواست‌ها</h2>",
        "<table><tr><th>ID</th><th>نام</th><th>شماره</th><th>مشکل</th><th>ویس</th></tr>"
    ]
    for r in rows:
        voice_link = f"<a href='/voice/{r[0]}?pass={ADMIN_PASS}'>دانلود</a>" if r[4] else "-"
        html.append(f"<tr><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{voice_link}</td></tr>")
    html.append("</table>")
    html.append(f"<br><a href='/export?pass={ADMIN_PASS}'>دانلود Excel (CSV)</a>")
    html.append("</body></html>")
    return "".join(html)

@app.route("/voice/<int:uid>")
def voice(uid):
    password = request.args.get("pass", "")
    if password != ADMIN_PASS:
        return "Access denied", 403

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT voice_file FROM users WHERE id=?", (uid,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return send_from_directory(".", row[0], as_attachment=True)
    return "File not found", 404

@app.route("/export")
def export():
    password = request.args.get("pass", "")
    if password != ADMIN_PASS:
        return "Access denied", 403

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, name, phone, problem FROM users ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    filename = "export.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Phone", "Problem"])
        writer.writerows(rows)

    return send_from_directory(".", filename, as_attachment=True)

# -------------------- اجرای برنامه --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
