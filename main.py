import telebot
from telebot import types
import pytube
import requests
import config
import json
from os import system

TOKEN = config.TOKEN
yt_key = config.yt_key
max_result = config.max_result
cache_time = config.cache_time

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands = ['start'])
def start(message):
    bot.reply_to(message, "Welcome to use this bot!\nIt can download YouTube audio for you.")

@bot.inline_handler(lambda query: query.query != '')
def search_youtube(query):
    r = requests.get('https://www.googleapis.com/youtube/v3/search?'
                    + '&key=%s'%yt_key
                    + '&part=snippet'
                    + '&type=video'
                    + '&maxResults=%s'%str(max_result)
                    + '&order=relevance'
                    + '&q=%s'%query.query
                    )
    print(r.url)
    data = json.loads(r.text)
    response = []
    for i in range(max_result):
        title = data['items'][i]['snippet']['title']
        link = types.InputTextMessageContent('https://www.youtube.com/watch?v=' + data['items'][i]['id']['videoId'])
        avatar = data['items'][i]['snippet']['thumbnails']['medium']['url']
        ans = types.InlineQueryResultArticle(i, title, link, thumb_url = avatar)
        response.append(ans)
    bot.answer_inline_query(query.id, response, cache_time = cache_time)

@bot.message_handler(func = lambda message: True)
def download(message):
    link = message.text
    try:
        audio = pytube.YouTube(link).streams.filter(only_audio = True, file_extension = 'mp4')[0]
    except:
        bot.reply_to(message, 'Invaild link...')
    else:
        bot.reply_to(message, 'You will soon receive the audio file.')
        filename = audio.download()
        with open(filename, 'rb') as audio:
            bot.send_message(message.chat.id, 'Sending...')
            bot.send_audio(message.chat.id, audio)
        system('rm %s'%filename)
    

bot.polling()
