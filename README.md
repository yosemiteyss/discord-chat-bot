# discord-chat-bot

This project is forked and modified from [gpt-discord-bot](https://github.com/openai/gpt-discord-bot) to support multiple
chat services.


## Supported Services
- OpenAI GPT
- Azure OpenAI
- PaLM Chat

## Features
- Support multiple chat services
- Forward request through VPN using Gluetun

## Configuration
1. Copy `.env.example` to `.env`
2. Fill in env variables for the required chat service in `.env`
3. Set `CHAT_SERVICE` to the chat service to connect to

## Add Models
- To add more chat models, edit `src/models.py`

## Run
- `python -m src.main`

## Docker
- `docker build -t discord-chat-bot . && docker stop discord-chat-bot && docker rm discord-chat-bot && docker run -d --restart always --name discord-chat-bot discord-chat-bot`

## Docker Compose
- `docker-compose up -d`

## Unit test
- Run: `python -m unittest discover test`