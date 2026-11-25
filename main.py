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
        'from': sender_name
    })

    with open('session/messages.json', 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)


def __remove_bad_messages(msg, msgid, chatid, sender_name):
    if not os.path.exists('badWords.txt'):
        return False

    with open('badWords.txt', 'r', encoding='utf-8') as file:
        words = [line.strip() for line in file if line.strip()]

    for word in words:
        if word in msg:
            try:
                bot.delete_message(chatid, msgid)
                bot.send_message(chatid, f'کاربر {sender_name} لطفا از استفاده از الفاظ زشت پرهیز کنید.')
            except Exception as e:
                print(f"Message deletion error: {e}")

            return True

    return False


def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except Exception as e:
        print(f"Admin check error: {e}")
        return False


# App
@bot.message_handler(commands=['start'])
def __start(msg):
    bot.send_message(msg.chat.id, 'سلام! به ربات مدیریت گروه TeleManager خوش آمدید. برای استفاده از ربات و مشاهده راهنما از دستور /help استفاده کنید.')


@bot.message_handler(func=lambda m: m.text=='بن')
def __ban_user(msg):
    if not is_admin(msg.chat.id, msg.from_user.id):
        bot.reply_to(msg, 'شما دسترسی ادمین ندارید!')
        return

    if not msg.reply_to_message:
        bot.reply_to(msg, 'روی پیام شخص موردنظر Reply کنید.')
        return

    user_id = msg.reply_to_message.from_user.id

    if is_admin(msg.chat.id, user_id):
        bot.reply_to(msg, 'امکان بن کردن ادمین وجود ندارد.')
        return

    if user_id == bot.get_me().id:
        bot.reply_to(msg, 'نمی‌توانم خودم را بن کنم!')
        return

    try:
        bot.ban_chat_member(msg.chat.id, user_id)
        bot.reply_to(msg, 'کاربر بن شد.')
    except Exception as e:
        print(f"Ban error: {e}")
        bot.reply_to(msg, 'خطا در بن کردن کاربر!')


@bot.message_handler(content_types=['text'])
def app(msg):
    text = msg.text
    chatid = msg.chat.id
    messageid = msg.message_id

    sender_name = (
        f"@{msg.from_user.username}"
        if msg.from_user.username
        else msg.from_user.first_name
    )

    if __remove_bad_messages(text, messageid, chatid, sender_name):
        return

    __add_message(text, messageid, chatid, sender_name)


bot.infinity_polling()
