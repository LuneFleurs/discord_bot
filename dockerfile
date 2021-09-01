FROM python:3

WORKDIR /discord_bot
COPY . .
RUN pip3 install youtube-dl discord pynacl
RUN apt update
RUN apt install ffmpeg -y

CMD [ "python3", "./main.py" ]