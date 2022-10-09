# YouTube Audio Download Bot

[@YTAudioDownloaderBot](https://t.me/YTAudioDownloaderBot)  

## Setup
1. Install necessary modules
    ```
    $ pip install -r requirements.txt
    ```
2. Place your Telegram bot token, Telegram bot name and YouTube search API key into `config.py`.
## Deploy
1. Build the image with your bot token
    ```
    $ docker build . -t {image name} --build-arg TOKEN='{your bot token}'
    ```
2. Run the container
    ```
    $ docker run --name ytbot -it -d --rm {image name}
    ```
