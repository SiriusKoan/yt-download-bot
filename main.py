import telebot
from telebot import types
import pytube
import config
import json
from os import remove, rename
from functions import *
from moviepy.editor import AudioFileClip
import requests

TOKEN = config.TOKEN
BOT_NAME = config.BOT_NAME
welcome_msg = """
Welcome to use this bot!
It can download YouTube audio for you.
"""

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start", "help"])
def start(message):
    add_user_record(message.chat.id)
    bot.reply_to(message, welcome_msg, parse_mode="Markdown")


@bot.message_handler(commands=["setting"])
def setting(message):
    inline_keyboard = types.InlineKeyboardMarkup()
    options = ["forward"]
    for option in options:
        inline_keyboard.add(types.InlineKeyboardButton(option, callback_data=option))
        bot.send_message(
            message.chat.id,
            text="Please select what you want to choose:",
            reply_markup=inline_keyboard,
        )


# receive setting
@bot.callback_query_handler(lambda query: query.data in ["forward"])
def receive_setting(query):
    # set which option
    chat_id = query.from_user.id
    message_id = query.message.message_id
    inline_keyboard = types.InlineKeyboardMarkup()
    if query.data == "forward":
        # set whether forward the audio to channel
        options = ["YES", "NO"]
        for option in options:
            inline_keyboard.add(
                types.InlineKeyboardButton(option, callback_data=option)
            )
        bot.edit_message_text(
            chat_id=chat_id,
            text="Whether you want to forward the audio to channel:",
            reply_markup=inline_keyboard,
            message_id=message_id,
        )


@bot.callback_query_handler(lambda query: query.data in ["YES", "NO"])
def receive_whether_forward(query):
    # set whether forward to channel
    chat_id = query.from_user.id
    set_forward(chat_id, query.data)
    message_id = query.message.message_id
    bot.edit_message_text(
        chat_id=chat_id,
        text="Send to channel: *%s*" % query.data,
        message_id=message_id,
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda message: True)
def check_link(message):
    # TODO modify forward setting
    chat_id = message.chat.id
    if message.text[0] == "@":
        set_forward(chat_id, message.text)
        bot.send_message(chat_id, "Send audio to %s" % message.text)
        return

    link = message.text
    try:
        if "watch" in link or "youtu.be" in link:
            audio_origin = pytube.YouTube(link)
            audio = audio_origin.streams.filter(only_audio=True, file_extension="mp4")[0]
            thumbnails = requests.get(audio_origin.thumbnail_url.replace('maxresdefault.jpg', 'default.jpg')).content
            bot.reply_to(message, "You will soon receive the audio file.")
            filename = audio.download()
            
            if audio.filesize > 50000000:
                bot.send_message(chat_id, "The file is too large so that it will be divided into many files.")
                divide = (audio.filesize // 50000000) + 1
                audio_file = AudioFileClip(filename)
                per_duration = audio_file.duration / divide
                media_group = []
                media_group_files = []
                for i in range(divide):
                    clip = audio_file.subclip(per_duration*i, per_duration*(i+1))
                    sub_filename = filename[:-4] + '_%d'%i + '.mp3'
                    clip.write_audiofile(sub_filename)
                    audio_clip = open(sub_filename, "rb")
                    msg = bot.send_audio(config.storage, audio_clip, thumb=thumbnails)
                    media_group_files.append(audio_clip)
                    media_group.append(types.InputMediaAudio(msg.audio.file_id))
                    
                message_id = bot.send_media_group(chat_id, media_group)
                forward = get_forward(chat_id)
                if forward:
                    bot.forward_message(forward, chat_id, message_id)
                for f in media_group:
                    f.close()
                    remove(f.name)
            else:
                with open(filename, "rb") as audio:
                    msg = bot.send_audio(config.storage, audio, thumb=thumbnails)
                    message_id = bot.send_audio(chat_id, msg.audio.file_id).message_id
                    forward = get_forward(chat_id)
                    if forward:
                        bot.forward_message(forward, chat_id, message_id)
                remove(filename)
    except IndexError as e:
        bot.send_message(chat_id, "No audio provided.")
    except Exception as e:
        print(e)
        bot.send_message(chat_id, "Unexpected error.")



bot.polling()