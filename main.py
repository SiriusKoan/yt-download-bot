import telebot
from telebot import types
import pytube
import requests
import config
import json
from os import remove
from functions import *

TOKEN = config.TOKEN
BOT_NAME = config.BOT_NAME
YT_KEY = config.YT_KEY
max_result = config.max_result
cache_time = config.cache_time
welcome_msg = """
Welcome to use this bot!
It can download YouTube audio for you.
                    
You can type `%s ` in the message field to search video. Then tap on one of the result to send to the bot.
"""%BOT_NAME

bot = telebot.TeleBot(TOKEN)

def download(audio, message):
    filename = audio.download()
    with open(filename, 'rb') as audio:
        bot.send_message(message.chat.id, 'Sending...')
        bot.send_audio(message.chat.id, audio)
    remove(filename)

@bot.message_handler(commands = ['start', 'help'])
def start(message):
    add_user_record(message.chat.id)
    bot.reply_to(message, welcome_msg, parse_mode = 'Markdown')

@bot.message_handler(commands = ['setting'])
def setting(message):
    inline_keyboard = types.InlineKeyboardMarkup()
    options = ['set duration', 'search for']
    for option in options:
        inline_keyboard.add(types.InlineKeyboardButton(option, callback_data = option))
    bot.send_message(message.chat.id, text = 'Please select what you want to choose:', reply_markup = inline_keyboard)


# receive setting
@bot.callback_query_handler(lambda query: query.data in ['set duration', 'search for'])
def receive_setting(query):
    # set which option
    chat_id = query.from_user.id
    message_id = query.message.message_id
    inline_keyboard = types.InlineKeyboardMarkup()
    print(query.data)
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
            channel_name = data['items'][i]['channelTitle']
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
        if 'video' in link:
            audio = pytube.YouTube(link).streams.filter(only_audio = True, file_extension = 'mp4')[0]
            bot.reply_to(message, 'You will soon receive the audio file.')
            download(audio, message)
        elif 'playlist' in link:
            audio = []
            playlist = pytube.Playlist(link).video_urls
            for video_link in playlist:
                audio.append(pytube.YouTube(video_link))
            inline_keyboard = types.InlineKeyboardMarkup()
            for a in audio:
                inline_keyboard.add(types.InlineKeyboardButton(a.title, callback_data = a.watch_url))
            bot.send_message(message.chat.id, 'Please select the video you want to download: ', reply_markup = inline_keyboard)
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, 'Invaild link...')
    

bot.polling()
