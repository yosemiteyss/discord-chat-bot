# discord-chat-bot

This project is forked and modified from [gpt-discord-bot](https://github.com/openai/gpt-discord-bot) to support multiple
chat services.


## Supported Services
- OpenAI GPT
- Azure OpenAI
- PaLM Chat

## Features
- Support multiple chat services
- Support switching chat models dynamically
- Forward request through VPN using Gluetun

## Commands
- `/chat`: Send a message to the chat service
- `/model`: Change the chat model
- `/count_token`: Count the number of tokens in a message

## Configuration
1. Copy `.env.example` to `.env`
2. Fill in env variables for the required chat service in `.env`
3. Set `CHAT_SERVICE` to the chat service to connect to

## Add Models
- To add more chat models, edit `src/models.py`

## Run
- `python -m src.main`

## Docker Compose
- Azure
  - `docker-compose -f ./docker-compose/docker-compose-azure.yml up -d`
  - `docker-compose -f ./docker-compose/docker-compose-azure.yml down`
- OpenAI
  - `docker-compose -f ./docker-compose/docker-compose-openai.yml up -d`
  - `docker-compose -f ./docker-compose/docker-compose-openai.yml down`
- Palm
  - `docker-compose -f ./docker-compose/docker-compose-palm.yml up -d`
  - `docker-compose -f ./docker-compose/docker-compose-palm.yml down`

## Unit test
- `python -m unittest discover test`