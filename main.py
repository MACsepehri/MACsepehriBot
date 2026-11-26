from telebot.types import ChatPermissions
import telebot
import dotenv
import os
import json
import time

dotenv.load_dotenv()

telebot.apihelper.API_URL = "https://tapi.bale.ai/bot{0}/{1}"
ADMIN_ID = os.environ['ADMIN_ID']
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
        print('Member:', member)
        print('Status:', member.status)

        return member.status in ['administrator', 'creator']

    except Exception as e:
        print('Admin check error:', repr(e))
        return False


def set_talk_user(yes, message, minutes=0):
    user_id = message.reply_to_message.from_user.id

    permissions = ChatPermissions(
        can_send_messages=yes,
        can_send_audios=yes,
        can_send_documents=yes,
        can_send_photos=yes,
        can_send_videos=yes,
        can_send_video_notes=yes,
        can_send_voice_notes=yes,
        can_send_polls=yes,
        can_send_other_messages=yes,
        can_add_web_page_previews=yes
    )

    if not yes:
        bot.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions,
            until_date=int(time.time()) + (minutes * 60)
        )
    else:
        bot.restrict_chat_member(
            message.chat.id,
            user_id,
            permissions
        )



# App
@bot.message_handler(commands=['start'])
def __start(msg):
    bot.send_message(msg.chat.id, 'سلام! به ربات مدیریت گروه TeleManager خوش آمدید. برای استفاده از ربات و مشاهده راهنما از دستور /help استفاده کنید.')


@bot.message_handler(func=lambda m: m.text and (m.text.startswith('میوت') or m.text.startswith('سکوت')))
def __mute_user(msg):
    if not is_admin(msg.chat.id, msg.from_user.id):
        bot.reply_to(msg, 'شما دسترسی ادمین ندارید!')
        return

    if not msg.reply_to_message:
        bot.reply_to(msg, 'روی پیام شخص موردنظر Reply کنید.')
        return

    try:
        minutes = int(msg.text.split()[1])
    except (ValueError, IndexError):
        bot.reply_to(msg, 'زمان داده شده معتبر نیست.')
        return

    if minutes < 1:
        bot.reply_to(msg, 'زمان میوت باید حداقل 1 دقیقه باشد.')
        return

    set_talk_user(False, msg, minutes)
    bot.reply_to(msg, 'کاربر با موفقیت میوت شد.')


@bot.message_handler(func=lambda m: m.text in ['ان میوت', 'آن میوت'])
def __unmute_user(msg):
    if not is_admin(msg.chat.id, msg.from_user.id):
        bot.reply_to(msg, 'شما دسترسی ادمین ندارید!')
        return

    if not msg.reply_to_message:
        bot.reply_to(msg, 'روی پیام شخص موردنظر Reply کنید.')
        return

    set_talk_user(True, msg)
    bot.reply_to(msg, 'کاربر با موفقیت آن میوت شد.')


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


@bot.message_handler(func=lambda m: m.text and m.text.startswith('حذف'))
def __remove_messages(msg):
    chat_id = msg.chat.id
    chatid = str(chat_id)

    text = msg.text
    chatid = msg.chat.id
    messageid = msg.message_id
    sender_name = (
        f"@{msg.from_user.username}"
        if msg.from_user.username
        else msg.from_user.first_name
    )
    __add_message(text, messageid, chatid, sender_name)

    if not is_admin(chat_id, msg.from_user.id):
        bot.reply_to(msg, 'شما دسترسی ادمین را ندارید!')
        return

    try:
        args = msg.text.split()

        if len(args) != 2:
            bot.reply_to(msg, 'فرمت صحیح: مرض 10 یا مرض همه')
            return

        with open('session/messages.json', 'r', encoding='utf-8') as file:
            content = json.load(file)

        if chatid not in content['chats']:
            bot.reply_to(msg, 'پیامی برای حذف وجود ندارد.')
            return

        messages = content['chats'][chatid]['messages']

        if args[1].isdigit():
            total = int(args[1])
            if total <= 0:
                raise ValueError('Invalid number')

        elif args[1] == 'همه':
            total = 500

        else:
            raise ValueError('Invalid argument')

        selected = messages[-total:]
        remaining = messages[:-len(selected)] if selected else messages

        deleted_messages = []

        for message in reversed(selected):
            try:
                bot.delete_message(
                    chat_id,
                    message['message_id']
                )

                deleted_messages.append(message)

            except Exception as e:
                print(
                    f"Failed to delete message "
                    f"{message['message_id']}: {repr(e)}"
                )

        deleted_ids = {
            message['message_id']
            for message in deleted_messages
        }

        content['chats'][chatid]['messages'] = [
            message for message in messages
            if message['message_id'] not in deleted_ids
        ]

        with open('session/messages.json', 'w', encoding='utf-8') as file:
            json.dump(content, file, ensure_ascii=False, indent=4)

        bot.reply_to(
            msg,
            f'حذف موفق: {len(deleted_messages)}\n'
            f'حذف ناموفق: {len(selected) - len(deleted_messages)}'
        )

    except Exception as e:
        print(type(e).__name__, repr(e))
        bot.reply_to(msg, 'خطا در اجرای دستور!')


@bot.message_handler(commands=['get_id'])
def __get_id(msg):
    bot.reply_to(msg, msg.from_user.id)




@bot.message_handler(commands=['admin'])
def __admin_panel(msg):
    user_id = msg.from_user.id
    if user_id == int(ADMIN_ID):
        with open('session/messages.json','r') as file:
            data = json.load(file)
        total_chats = len(data['chats'])
        total_messages = 0
        for chat in data['chats']:
            total_messages += len(data['chats'][chat]['messages'])

        bot.reply_to(msg, f'خوش آمدید ادمین!\nتعداد چت ها : {total_chats}\nتعداد پیام های ذخیره شده توسط بات : {total_messages}.')
    else:
        bot.reply_to(msg, 'شما دسترسی ندارید!')





@bot.message_handler(content_types=['text'])
def app(msg):
    text = msg.text
    chatid = msg.chat.id
    messageid = msg.message_id
    user_id = msg.from_user.id

    print()

    sender_name = (
        f"@{msg.from_user.username}"
        if msg.from_user.username
        else msg.from_user.first_name
    )

    if __remove_bad_messages(text, messageid, chatid, sender_name):
        return

    __add_message(text, messageid, chatid, sender_name)


bot.infinity_polling()
