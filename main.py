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
CHANNEL_ID = config.CHANNEL_ID
YT_KEY = config.YT_KEY
max_result = config.max_result
cache_time = config.cache_time
welcome_msg = """
Welcome to use this bot!
It can download YouTube audio for you.
                    
You can type `%s ` in the message field to search video. Then tap on one of the result to send to the bot.
"""%BOT_NAME

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands = ['start', 'help'])
def start(message):
    add_user_record(message.chat.id)
    bot.reply_to(message, welcome_msg, parse_mode = 'Markdown')

@bot.message_handler(commands = ['setting'])
def setting(message):
    inline_keyboard = types.InlineKeyboardMarkup()
    options = ['set duration', 'search for', 'forward']
    for option in options:
        inline_keyboard.add(types.InlineKeyboardButton(option, callback_data = option))
    bot.send_message(message.chat.id, text = 'Please select what you want to choose:', reply_markup = inline_keyboard)


# receive setting
@bot.callback_query_handler(lambda query: query.data in ['set duration', 'search for', 'forward'])
def receive_setting(query):
    # set which option
    chat_id = query.from_user.id
    message_id = query.message.message_id
    inline_keyboard = types.InlineKeyboardMarkup()
    if query.data == 'set duration':
        # set duration
        options = ['any', 'short', 'medium', 'long']
        for option in options:
            inline_keyboard.add(types.InlineKeyboardButton(option, callback_data = option))
        bot.edit_message_text(chat_id = chat_id, text = 'Please select the duration you want to set:', reply_markup = inline_keyboard, message_id = message_id)
    elif query.data == 'search for':
        # set search video or playlist
        options = ['video', 'playlist']
        for option in options:
            inline_keyboard.add(types.InlineKeyboardButton(option, callback_data = option))
        bot.edit_message_text(chat_id = chat_id, text = 'Please select what you want to search: ', reply_markup = inline_keyboard, message_id = message_id)
    elif query.data == 'forward':
        # set whether forward the audio to channel
        options = ['YES', 'NO']
        for option in options:
            inline_keyboard.add(types.InlineKeyboardButton(option, callback_data = option))
        bot.edit_message_text(chat_id = chat_id, text = 'Whether you want to forward the audio to channel:', reply_markup = inline_keyboard, message_id = message_id)

@bot.callback_query_handler(lambda query: query.data in ['any', 'short', 'medium', 'long'])
def receive_set_duration(query):
    # set video duration
    chat_id = query.from_user.id
    message_id = query.message.message_id
    set_duration(chat_id, query.data)
    bot.edit_message_text(chat_id = chat_id, text = 'Set duration to *%s*.\nYou have to wait for about %s seconds since your last search.'%(query.data, str(cache_time)), message_id = message_id, parse_mode = 'Markdown')

@bot.callback_query_handler(lambda query: query.data in ['video', 'playlist'])
def receive_set_search(query):
    # set what to search
    chat_id = query.from_user.id
    set_search_for(chat_id, query.data)
    message_id = query.message.message_id
    bot.edit_message_text(chat_id = chat_id, text = 'Set search to *%s*.\nYou have to wait for about %s seconds since your last search.'%(query.data, str(cache_time)), message_id = message_id, parse_mode = 'Markdown')

@bot.callback_query_handler(lambda query: query.data in ['YES', 'NO'])
def receive_whether_forward(query):
    # set whether forward to channel
    chat_id = query.from_user.id
    set_forward(chat_id, query.data)
    message_id = query.message.message_id
    bot.edit_message_text(chat_id = chat_id, text = 'Set whether forward audio to channel: *%s*'%query.data, message_id = message_id, parse_mode = 'Markdown')

# inline query to search
@bot.inline_handler(lambda query: query.query != '')
def search_youtube(query):
    chat_id = query.from_user.id
    search = get_search_for(chat_id)
    response = []
    if search == 'video':
        r = requests.get('https://www.googleapis.com/youtube/v3/search?'
                        + '&key=%s'%YT_KEY
                        + '&part=snippet'
                        + '&type=video'
                        + '&maxResults=%s'%str(max_result)
                        + '&order=relevance'
                        + '&topicId=/m/04rlf'
                        + '&videoDuration=%s'%get_duration(chat_id)
                        + '&q=%s'%query.query
                        )
        data = json.loads(r.text)
        for i in range(max_result):
            title = data['items'][i]['snippet']['title']
            link = types.InputTextMessageContent('https://www.youtube.com/watch?v=' + data['items'][i]['id']['videoId'])
            avatar = data['items'][i]['snippet']['thumbnails']['medium']['url']
            channel_name = data['items'][i]['snippet']['channelTitle']
            ans = types.InlineQueryResultArticle(i, title, link, thumb_url = avatar, description = channel_name)
            response.append(ans)
    else:
        r = requests.get('https://www.googleapis.com/youtube/v3/search?'
                        + '&key=%s'%YT_KEY
                        + '&part=snippet'
                        + '&type=playlist'
                        + '&maxResults=%s'%str(max_result)
                        + '&order=relevance'
                        + '&topicId=/m/04rlf'
                        + '&q=%s'%query.query
                        )
        data = json.loads(r.text)
        for i in range(max_result):
            title = data['items'][i]['snippet']['title']
            link = types.InputTextMessageContent('https://www.youtube.com/playlist?list=' + data['items'][i]['id']['playlistId'])
            avatar = data['items'][i]['snippet']['thumbnails']['medium']['url']
            ans = types.InlineQueryResultArticle(i, title, link, thumb_url = avatar)
            response.append(ans)

    # send link
    bot.answer_inline_query(query.id, response, cache_time = cache_time)


@bot.message_handler(func = lambda message: True)
def check_link(message):
    link = message.text
    try:
        if 'watch' in link or 'youtu.be' in link:
            audio = pytube.YouTube(link).streams.filter(only_audio = True, file_extension = 'mp4')[0]
            if audio.filesize > 50000000:
                raise FileTooLarge
            bot.reply_to(message, 'You will soon receive the audio file.')
            filename = audio.download()
            with open(filename, 'rb') as audio:
                message_id = bot.send_audio(message.chat.id, audio).message_id
                if get_forward(message.chat.id):
                    bot.forward_message(CHANNEL_ID, message.chat.id, message_id)
            remove(filename)
        elif 'playlist' in link:
            playlist = pytube.Playlist(link)
            inline_keyboard = types.InlineKeyboardMarkup()
            button = []
            for i, audio in enumerate(playlist):
                button.append(types.InlineKeyboardButton(i + 1, callback_data = audio))
            for i in range(0, len(button), 5):
                inline_keyboard.row(*button[i:i + 5])
            inline_keyboard.row(types.InlineKeyboardButton('complete', callback_data = 'playlist_download_complete'))
            bot.send_message(message.chat.id, 'Please select the video in %s you want to download: '%playlist.title(), reply_markup = inline_keyboard)
    except FileTooLarge:
        bot.send_message(message.chat.id, 'The audio file is too large to send.')
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Invaild link.')

@bot.callback_query_handler(lambda query: 'https://' in query.data)
def receive_video_in_playlist(query):
    chat_id = query.from_user.id
    audio = pytube.YouTube(query.data).streams.filter(only_audio = True, file_extension = 'mp4')[0]
    filename = audio.download()
    with open(filename, 'rb') as audio:
        message_id = bot.send_audio(chat_id, audio).message_id
        if get_forward(chat_id):
            bot.forward_message(CHANNEL_ID, chat_id, message_id)
    remove(filename)

@bot.callback_query_handler(lambda query: query.data == 'playlist_download_complete')
def receive_playlist_download_complete(query):
    chat_id = query.from_user.id
    message_id = query.message.message_id
    bot.delete_message(chat_id, message_id)
    

bot.polling()