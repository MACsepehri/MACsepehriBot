import telebot
import dotenv
import os
import json

# init
dotenv.load_dotenv()

telebot.apihelper.API_URL = "https://tapi.bale.ai/bot{0}/{1}"

TOKEN = os.environ['API_KEY']
bot = telebot.TeleBot(TOKEN)
messages = []

# app
@bot.message_handler(commands=['start'])
def __start(msg):
    chatid = msg.chat.id

    bot.send_message(chatid, 'سلام! به ربات مدیریت گروه TeleManager خوش آمدید.\nبرای استفاده از ربات و مشاهده راهنما از دستور /help استفاده کنید.')

@bot.message_handler(func=lambda m: True)
def app(msg):
    text = msg.text



bot.infinity_polling()
