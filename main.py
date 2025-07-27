
import telebot
from flask import Flask, request, render_template_string

API_TOKEN = 'توکن_ربات_اینجا'
ADMIN_ID = 7549512366

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

user_data = {}

@app.route('/panel')
def panel():
    html = "<h2>پنل مدیریتی</h2>"
    for user_id, data in user_data.items():
        html += f"<p><b>{user_id}</b>: {data}</p>"
    return render_template_string(html)

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    return 'ok'

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "سلام! لطفاً نام خود را وارد کنید:")
    user_data[message.chat.id] = {}

@bot.message_handler(func=lambda message: True)
def collect_data(message):
    uid = message.chat.id
    if 'name' not in user_data[uid]:
        user_data[uid]['name'] = message.text
        bot.send_message(uid, "شماره تماس را وارد کنید:")
    elif 'phone' not in user_data[uid]:
        user_data[uid]['phone'] = message.text
        bot.send_message(uid, "✅ اطلاعات با موفقیت ثبت شد.")
        bot.send_message(ADMIN_ID, f"کاربر جدید:
👤 نام: {user_data[uid]['name']}
📞 شماره: {user_data[uid]['phone']}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
