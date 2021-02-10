import telebot
from telebot import types
import pytube
import requests
import config
import json
from os import remove
from functions import *
import traceback
import sys

TOKEN = config.TOKEN
BOT_NAME = config.BOT_NAME
YT_KEY = config.YT_KEY
max_result = config.max_result
cache_time = config.cache_time
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
    chat_id = message.chat.id
    if message.text[0] == "@":
        set_forward(chat_id, message.text)
        bot.send_message(chat_id, "Send audio to %s" % message.text)
        return

    link = message.text
    try:
        if "watch" in link or "youtu.be" in link:
            audio_origin = pytube.YouTube(link)
            thumbnails = requests.get(audio_origin.thumbnail_url).content
            thumbnails = open("c.jpeg", "rb")
            audio = audio_origin.streams.filter(only_audio=True, file_extension="mp4")[
                0
            ]
            if audio.filesize > 50000000:
                raise FileTooLarge
            bot.reply_to(message, "You will soon receive the audio file.")
            filename = audio.download()
            with open(filename, "rb") as audio:
                message_id = bot.send_audio(
                    message.chat.id, audio, thumb=thumbnails
                ).message_id
                forward = get_forward(message.chat.id)
                if forward:
                    bot.forward_message(forward, message.chat.id, message_id)
            remove(filename)
        elif "playlist" in link:
            playlist = pytube.Playlist(link)
            inline_keyboard = types.InlineKeyboardMarkup()
            button = []
            for i, audio in enumerate(playlist):
                button.append(types.InlineKeyboardButton(i + 1, callback_data=audio))
            for i in range(0, len(button), 5):
                inline_keyboard.row(*button[i : i + 5])
            inline_keyboard.row(
                types.InlineKeyboardButton(
                    "complete", callback_data="playlist_download_complete"
                )
            )
            bot.send_message(
                message.chat.id,
                "Please select the video in %s you want to download: "
                % playlist.title(),
                reply_markup=inline_keyboard,
            )
    except FileTooLarge:
        bot.send_message(message.chat.id, "The audio file is too large to send.")
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Invaild link.")


@bot.callback_query_handler(lambda query: "https://" in query.data)
def receive_video_in_playlist(query):
    chat_id = query.from_user.id
    audio_origin = pytube.YouTube(query.data)
    audio = audio_origin.streams.filter(only_audio=True, file_extension="mp4")[0]
    filename = audio.download()
    with open(filename, "rb") as audio:
        message_id = bot.send_audio(chat_id, audio).message_id
        forward = get_forward(chat_id)
        if forward:
            bot.forward_message(forward, chat_id, message_id)
    remove(filename)


@bot.callback_query_handler(lambda query: query.data == "playlist_download_complete")
def receive_playlist_download_complete(query):
    chat_id = query.from_user.id
    message_id = query.message.message_id
    bot.delete_message(chat_id, message_id)


bot.polling()