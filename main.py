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

# functions
def __add_message(msg, msg_id, chatid):
    with open('session/messages.json','r') as file:
        content = json.load(file)
    print(0)
    found_group = False
    group_id = 0
    for chat in content['chats']:
        if chat == str(chatid):
            found_group = True
            group_id = chat

    if (found_group):
        content['chats'][group_id]['messages'].append({'text':msg,'message.id':msg_id})

        with open('session/messages.json','w') as file:
            json.dump(content, file)
    else:
        content['chats'][chatid] = {'messages':[]}
        content['chats'][chatid]['messages'].append({'text':msg,'message.id':msg_id})

        with open('session/messages.json','w') as file:
            json.dump(content, file)

def __remove_bad_messages():
    pass

# app
@bot.message_handler(commands=['start'])
def __start(msg):
    chatid = msg.chat.id

    bot.send_message(chatid, 'سلام! به ربات مدیریت گروه TeleManager خوش آمدید.\nبرای استفاده از ربات و مشاهده راهنما از دستور /help استفاده کنید.')

@bot.message_handler(func=lambda m: True)
def app(msg):
    text = msg.text
    chatid = msg.chat.id
    messageid = msg.message_id

    __add_message(text,messageid,chatid)

bot.infinity_polling()
