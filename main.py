
from telebot.types import ChatPermissions
import telebot
import dotenv
import threading
import os
import json
import time

dotenv.load_dotenv()

telebot.apihelper.API_URL = "https://tapi.bale.ai/bot{0}/{1}"

ADMIN_ID = int(os.environ['ADMIN_ID'])
TOKEN = os.environ['API_KEY']

bot = telebot.TeleBot(TOKEN)

# Initialize
os.makedirs('session', exist_ok=True)

if not os.path.exists('session/messages.json'):
    with open('session/messages.json', 'w', encoding='utf-8') as file:
        json.dump({'chats': {}}, file, ensure_ascii=False, indent=4)


# Temporary Messages
def delete_temp_message(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception as e:
        print(f'Temporary message deletion error: {e}')


def send_temp_message(chat_id, text, reply_to=None):
    message = bot.send_message(
        chat_id,
        text,
        reply_to_message_id=reply_to
    )

    timer = threading.Timer(
        15,
        delete_temp_message,
        args=(chat_id, message.message_id)
    )

    timer.daemon = True
    timer.start()

    return message


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

                send_temp_message(
                    chatid,
                    f'کاربر {sender_name} لطفا از استفاده از الفاظ زشت پرهیز کنید.'
                )

            except Exception as e:
                print(f'Message deletion error: {e}')

            return True

    return False


def is_admin(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']

    except Exception as e:
        print(f'Admin check error: {e}')
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
    send_temp_message(
        msg.chat.id,
        'سلام! به ربات مدیریت گروه TeleManager خوش آمدید. برای استفاده از ربات و مشاهده راهنما از دستور /help استفاده کنید.'
    )


# Mute
@bot.message_handler(func=lambda m: m.text and (
    m.text.startswith('میوت') or m.text.startswith('سکوت')
))
def __mute_user(msg):
    if not is_admin(msg.chat.id, msg.from_user.id):
        send_temp_message(msg.chat.id, 'شما دسترسی ادمین ندارید!', msg.message_id)
        return

    if not msg.reply_to_message:
        send_temp_message(msg.chat.id, 'روی پیام شخص موردنظر Reply کنید.', msg.message_id)
        return

    try:
        minutes = int(msg.text.split()[1])

        if minutes < 1:
            raise ValueError()

        set_talk_user(False, msg, minutes)

        send_temp_message(
            msg.chat.id,
            'کاربر با موفقیت میوت شد.',
            msg.message_id
        )

    except (ValueError, IndexError):
        send_temp_message(msg.chat.id, 'زمان داده شده معتبر نیست.', msg.message_id)

    except Exception as e:
        print(f'Mute error: {e}')
        send_temp_message(msg.chat.id, 'خطا در میوت کردن کاربر!', msg.message_id)


# Unmute
@bot.message_handler(func=lambda m: m.text in ['ان میوت', 'آن میوت'])
def __unmute_user(msg):
    if not is_admin(msg.chat.id, msg.from_user.id):
        send_temp_message(msg.chat.id, 'شما دسترسی ادمین ندارید!', msg.message_id)
        return

    if not msg.reply_to_message:
        send_temp_message(msg.chat.id, 'روی پیام شخص موردنظر Reply کنید.', msg.message_id)
        return

    try:
        set_talk_user(True, msg)

        send_temp_message(
            msg.chat.id,
            'کاربر با موفقیت آن میوت شد.',
            msg.message_id
        )

    except Exception as e:
        print(f'Unmute error: {e}')
        send_temp_message(msg.chat.id, 'خطا در آن‌میوت کردن کاربر!', msg.message_id)


# Ban
@bot.message_handler(func=lambda m: m.text == 'بن')
def __ban_user(msg):
    if not is_admin(msg.chat.id, msg.from_user.id):
        send_temp_message(msg.chat.id, 'شما دسترسی ادمین ندارید!', msg.message_id)
        return

    if not msg.reply_to_message:
        send_temp_message(msg.chat.id, 'روی پیام شخص موردنظر Reply کنید.', msg.message_id)
        return

    user_id = msg.reply_to_message.from_user.id

    if user_id == bot.get_me().id:
        send_temp_message(msg.chat.id, 'نمی‌توانم خودم را بن کنم!', msg.message_id)
        return

    if is_admin(msg.chat.id, user_id):
        send_temp_message(msg.chat.id, 'امکان بن کردن ادمین وجود ندارد.', msg.message_id)
        return

    try:
        bot.ban_chat_member(msg.chat.id, user_id)

        send_temp_message(
            msg.chat.id,
            'کاربر بن شد.',
            msg.message_id
        )

    except Exception as e:
        print(f'Ban error: {e}')
        send_temp_message(msg.chat.id, 'خطا در بن کردن کاربر!', msg.message_id)


# Delete Messages
@bot.message_handler(func=lambda m: m.text and m.text.split(maxsplit=1)[0] == 'حذف')
def __remove_messages(msg):
    chat_id = msg.chat.id
    chatid = str(chat_id)

    if not is_admin(chat_id, msg.from_user.id):
        send_temp_message(chat_id, 'شما دسترسی ادمین را ندارید!', msg.message_id)
        return

    try:
        args = msg.text.split()

        if len(args) != 2:
            send_temp_message(
                chat_id,
                'فرمت صحیح:\nحذف 10\nحذف همه',
                msg.message_id
            )
            return

        if args[1].isdigit():
            total = int(args[1])

            if total <= 0:
                raise ValueError('Invalid number')

        elif args[1] == 'همه':
            total = 500

        else:
            raise ValueError('Invalid argument')

        sender_name = (
            f"@{msg.from_user.username}"
            if msg.from_user.username
            else msg.from_user.first_name
        )

        # Save delete command
        __add_message(
            msg.text,
            msg.message_id,
            chat_id,
            sender_name
        )

        with open('session/messages.json', 'r', encoding='utf-8') as file:
            content = json.load(file)

        if chatid not in content['chats']:
            send_temp_message(chat_id, 'پیامی برای حذف وجود ندارد.')
            return

        messages = content['chats'][chatid]['messages']
        selected = messages[-total:]

        deleted_ids = set()

        for message in reversed(selected):
            try:
                bot.delete_message(
                    chat_id,
                    message['message_id']
                )

                deleted_ids.add(message['message_id'])

            except Exception as e:
                print(
                    f"Failed to delete message "
                    f"{message['message_id']}: {repr(e)}"
                )

        content['chats'][chatid]['messages'] = [
            message for message in messages
            if message['message_id'] not in deleted_ids
        ]

        with open('session/messages.json', 'w', encoding='utf-8') as file:
            json.dump(content, file, ensure_ascii=False, indent=4)

        send_temp_message(
            chat_id,
            f'حذف موفق: {len(deleted_ids)}\n'
            f'حذف ناموفق: {len(selected) - len(deleted_ids)}'
        )

    except Exception as e:
        print(type(e).__name__, repr(e))
        send_temp_message(chat_id, 'خطا در اجرای دستور!')


# Get ID
@bot.message_handler(commands=['get_id'])
def __get_id(msg):
    send_temp_message(
        msg.chat.id,
        str(msg.from_user.id),
        msg.message_id
    )


# Admin Panel
@bot.message_handler(commands=['admin'])
def __admin_panel(msg):
    if msg.from_user.id == ADMIN_ID:
        with open('session/messages.json', 'r', encoding='utf-8') as file:
            data = json.load(file)

        total_chats = len(data['chats'])

        total_messages = sum(
            len(data['chats'][chat]['messages'])
            for chat in data['chats']
        )

        send_temp_message(
            msg.chat.id,
            f'خوش آمدید ادمین!\n'
            f'تعداد چت ها: {total_chats}\n'
            f'تعداد پیام های ذخیره شده توسط بات: {total_messages}.',
            msg.message_id
        )

    else:
        send_temp_message(
            msg.chat.id,
            'شما دسترسی ندارید!',
            msg.message_id
        )

@bot.message_handler(commands=['help'])
def __get_help(msg):
    send_temp_message(
        msg.chat.id,
        'راهنمای MACsepehriBot :\n/get_id => آیدی شما\n/help => باش شدن همین منو\nحذف [عدد / همه] => حذف پیام ها\nمیوت / سکوت => میوت کردن کاربران\nآن میوت / ان میوت => آن میوت کردن کاربران',
        msg.message_id
    )


# Message Handler
@bot.message_handler(content_types=['text'])
def app(msg):
    text = msg.text
    chat_id = msg.chat.id
    message_id = msg.message_id

    sender_name = (
        f"@{msg.from_user.username}"
        if msg.from_user.username
        else msg.from_user.first_name
    )

    if __remove_bad_messages(text, message_id, chat_id, sender_name):
        return

    __add_message(
        text,
        message_id,
        chat_id,
        sender_name
    )


bot.infinity_polling()
