# main.py with login and export
import os
import sqlite3
import csv
from flask import Flask, request, render_template_string, send_from_directory, redirect, url_for

import telebot

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
ADMIN_PASS = "admin123"  # رمز عبور ساده برای ورود به پنل

bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")
app = Flask(__name__)

os.makedirs("voices", exist_ok=True)

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            problem TEXT,
            voice_file TEXT
        )'''
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
user_state = {}

# Telegram handlers
@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id
    user_state[chat_id] = {"step": "phone"}
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(telebot.types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True))
    bot.send_message(
        chat_id,
        "⚖️ *به هلدینگ حقوقی الای خوش آمدید.*\n"
        "برای رزرو وقت مشاوره مراحل زیر را کامل کنید.\n\n"
        "📱 لطفاً شماره تماس خود را ارسال کنید:",
        reply_markup=kb,
    )

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    chat_id = message.chat.id
    phone = message.contact.phone_number
    user_state[chat_id] = {"phone": phone, "step": "name"}
    bot.send_message(
        chat_id,
        f"📞 شماره شما ثبت شد: {phone}\n"
        "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:",
        reply_markup=telebot.types.ReplyKeyboardRemove(),
    )

@bot.message_handler(func=lambda m: True, content_types=["text", "voice"])
def handle_all(message):
    chat_id = message.chat.id
    if chat_id not in user_state:
        bot.reply_to(message, "برای شروع از دستور /start استفاده کنید.")
        return

    step = user_state[chat_id]["step"]

    if step == "phone":
        phone = message.text
        user_state[chat_id]["phone"] = phone
        user_state[chat_id]["step"] = "name"
        bot.send_message(
            chat_id,
            f"📞 شماره شما ثبت شد: {phone}\n"
            "👤 لطفاً نام و نام خانوادگی خود را وارد کنید:",
        )

    elif step == "name":
        user_state[chat_id]["name"] = message.text
        user_state[chat_id]["step"] = "problem"
        bot.send_message(chat_id, "📝 لطفاً مشکل یا موضوع حقوقی خود را به صورت متن یا ویس ارسال کنید:")

    elif step == "problem":
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

        save_user(
            chat_id,
            user_state[chat_id]["name"],
            user_state[chat_id]["phone"],
            problem_text,
            voice_path,
        )

        bot.send_message(
            ADMIN_ID,
            "🔔 *درخواست جدید مشاوره*\n"
            f"👤 نام: {user_state[chat_id]['name']}\n"
            f"📞 شماره: {user_state[chat_id]['phone']}\n"
            f"📝 مشکل: {'ویس ارسال شد' if voice_path else problem_text}",
        )

        bot.send_message(
            chat_id,
            "✅ اطلاعات شما با موفقیت ثبت شد.\n"
            "کارشناسان ما در اسرع وقت با شما تماس می‌گیرند.\n\n"
            "☎️ برای مشاوره فوری: 09001003914",
            reply_markup=telebot.types.ReplyKeyboardRemove(),
        )
        del user_state[chat_id]

@app.route('/' + TOKEN, methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.data.decode('utf-8'))
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "Legal bot is running.", 200

# پنل با لاگین ساده
@app.route('/panel', methods=['GET'])
def panel():
    password = request.args.get("pass")
    if password != ADMIN_PASS:
        return "<h3>رمز اشتباه است. ?pass=ADMIN_PASS</h3>"

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    html = '<html><head><meta charset="UTF-8"><title>پنل مدیریت</title></head><body>'
    html += f"<h2>درخواست‌ها (رمز: {ADMIN_PASS})</h2><table border='1'><tr><th>ID</th><th>نام</th><th>شماره</th><th>مشکل</th><th>ویس</th></tr>"
    for r in rows:
        voice_link = f"<a href='/voice/{r[0]}?pass={ADMIN_PASS}'>دانلود</a>" if r[5] else "-"
        html += f"<tr><td>{r[0]}</td><td>{r[2]}</td><td>{r[3]}</td><td>{r[4]}</td><td>{voice_link}</td></tr>"
    html += "</table><br><a href='/export?pass={ADMIN_PASS}'>دانلود Excel</a></body></html>"
    return html

@app.route('/voice/<int:uid>')
def voice(uid):
    password = request.args.get("pass")
    if password != ADMIN_PASS:
        return "Access Denied", 403
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT voice_file FROM users WHERE id=?",(uid,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return send_from_directory('.', row[0], as_attachment=True)
    return "File not found", 404

@app.route('/export')
def export():
    password = request.args.get("pass")
    if password != ADMIN_PASS:
        return "Access Denied", 403
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT id, name, phone, problem FROM users")
    rows = c.fetchall()
    conn.close()
    filename = "export.csv"
    with open(filename, "w", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Phone", "Problem"])
        writer.writerows(rows)
    return send_from_directory('.', filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
