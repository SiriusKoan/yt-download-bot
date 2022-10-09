import telebot
from telebot import types
import pytube
import config
import json
from os import remove, rename
from moviepy.editor import AudioFileClip
import requests

TOKEN = config.TOKEN

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.reply_to(message, "Welcome to use this bot!\nIn can download YouTube audio for you.", parse_mode="Markdown")



@bot.message_handler(func=lambda message: True)
def check_link(message):
    # TODO modify forward setting
    chat_id = message.chat.id
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
                    media_group_files.append(audio_clip)
                    media_group.append(types.InputMediaAudio(audio_clip))

                message_id = bot.send_media_group(chat_id, media_group)
                for f in media_group:
                    f.close()
                    remove(f.name)
            else:
                with open(filename, "rb") as audio:
                    message_id = bot.send_audio(chat_id, audio).message_id
                remove(filename)
    except IndexError as e:
        bot.send_message(chat_id, "No audio provided.")
    except Exception as e:
        print(e)
        bot.send_message(chat_id, "Unexpected error.")


bot.polling()
