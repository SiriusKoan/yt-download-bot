import io
import telebot
from telebot import types
import pytube
import requests
import config

TOKEN = config.TOKEN

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start", "help"])
def start(message):
    bot.reply_to(
        message,
        "Welcome to use this bot!\nIn can download YouTube audio for you.",
        parse_mode="Markdown",
    )


@bot.message_handler(func=lambda message: True)
def check_link(message):
    chat_id = message.chat.id
    link = message.text
    if not ("watch" in link or "youtu.be" in link):
        return
    try:
        audio_origin = pytube.YouTube(link)
        audio = audio_origin.streams.filter(only_audio=True, file_extension="mp4")[0]
        thumbnails = requests.get(
            audio_origin.thumbnail_url.replace("maxresdefault.jpg", "default.jpg")
        ).content
        bot.reply_to(message, "You will soon receive the audio file.")

        if audio.filesize > 50000000:
            bot.send_message(
                chat_id,
                "The file is too large, so it cannot be downloaded.",
            )
            """
                divide = (audio.filesize // 50000000) + 1
                audio_file = AudioFileClip(filename)
                per_duration = audio_file.duration / divide
                media_group = []
                media_group_files = []
                for i in range(divide):
                    clip = audio_file.subclip(per_duration * i, per_duration * (i + 1))
                    sub_filename = f"{fi)ename[:-4]}_{i}.mp3"
                    clip.write_audiofile(sub_filename)
                    audio_clip = open(sub_filename, "rb")
                    media_group_files.append(audio_clip)
                    media_group.append(types.InputMediaAudio(audio_clip))

                message_id = bot.send_media_group(chat_id, media_group)
                for f in media_group:
                    f.close()
                    remove(f.name)
                """
        else:
            with io.BytesIO() as buffer:
                audio.stream_to_buffer(buffer)
                bot.send_audio(
                    chat_id, buffer.getvalue(), thumb=thumbnails, title=audio.title
                )
    except IndexError as e:
        bot.send_message(chat_id, "No audio provided.")
    except Exception as e:
        print(e)
        bot.send_message(chat_id, "Unexpected error. Please try again.")


bot.polling()
