import telebot
from flask import Flask, request, render_template_string

TOKEN = "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8"
ADMIN_ID = 7549512366
WEBHOOK_URL = "https://bot-ll15.onrender.com/" + TOKEN

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Storage for messages
messages = []

# Panel route
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return '', 200

@app.route("/panel", methods=["GET"])
def panel():
    html = "<h2>📥 پیام‌های دریافتی:</h2><ul>"
    for m in messages:
        html += f"<li><b>{m['user']}</b>: {m['text']}</li>"
    html += "</ul>"
    return render_template_string(html)

# Start command handler
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "سلام عزیزم، به ربات حقوقی خوش اومدی. لطفاً مشکلت رو برام بنویس 📝")
   bot.send_message(ADMIN_ID, f"کاربر جدید شروع کرد: {message.from_user.first_name}")
👤 {message.chat.first_name} ({message.chat.id})")

# All text messages
@bot.message_handler(func=lambda m: True, content_types=['text', 'voice'])
def receive_message(message):
    user = message.chat.first_name or "ناشناس"
    text = "[voice]" if message.content_type == 'voice' else message.text
    messages.append({'user': user, 'text': text})
    bot.send_message(message.chat.id, "✅ پیام شما دریافت شد. در اولین فرصت پاسخ داده خواهد شد.")
    bot.send_message(ADMIN_ID, f"📩 پیام جدید از {user}:
{text}")

if __name__ == "__main__":
    import telebot
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
