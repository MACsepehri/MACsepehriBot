
import telebot
import dotenv
import os
import json

dotenv.load_dotenv()

telebot.apihelper.API_URL = "https://tapi.bale.ai/bot{0}/{1}"

TOKEN = os.environ['API_KEY']
bot = telebot.TeleBot(TOKEN)

# Initialize
os.makedirs('session', exist_ok=True)

if not os.path.exists('session/messages.json'):
    with open('session/messages.json', 'w', encoding='utf-8') as file:
        json.dump({'chats': {}}, file, ensure_ascii=False, indent=4)


# Functions
def __add_message(msg, msg_id, chatid, sender_name):
    with open('session/messages.json', 'r', encoding='utf-8') as file:
        content = json.load(file)

    chatid = str(chatid)

    if chatid not in content['chats']:
        content['chats'][chatid] = {'messages': []}

    content['chats'][chatid]['messages'].append({
        'text': msg,
        'message_id': msg_id,
        'from':sender_name
    })

    with open('session/messages.json', 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def __remove_bad_messages(msg, msgid, chatid, sender_name):
    with open('badWords.txt', 'r', encoding='utf-8') as file:
        words = [line.strip() for line in file if line.strip()]

    for word in words:
        if word in msg:
            bot.delete_message(chatid, msgid)
            bot.send_message(chatid, f'کاربر {sender_name} لطفا از استفاده از الفاظ زشت پرهیز کنید.')
            return True

    return False


# App
@bot.message_handler(commands=['start'])
def __start(msg):
    bot.send_message(msg.chat.id, 'سلام! به ربات مدیریت گروه TeleManager خوش آمدید.\nبرای استفاده از ربات و مشاهده راهنما از دستور /help استفاده کنید.')


@bot.message_handler(content_types=['text'])
def app(msg):
    text = msg.text
    chatid = msg.chat.id
    messageid = msg.message_id
    sender_name = msg.from_user.username

    if __remove_bad_messages(text, messageid, chatid, sender_name):
        return

    __add_message(text, messageid, chatid, sender_name)


bot.infinity_polling()
