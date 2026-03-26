# Welcome Bot

A bot that monitors signal chat groups and posts a message when people join

## Getting Started 

**Note**: this is a work in progress. These setup instructions are very rough and will be evolving rapidly.

register signal-api locally, then bring up a shim container to copy relevant fiels into the volume:
```
docker volume create signal-state
docker run -it -v ~/.local/share/welcomebot:/home/welcombot -v signal-state:/home/signal_state alpine 
```

run signal-api using that volume:
```
docker create network signal
docker run -d  --name signal-api --restart=always -p 9922:8080 \
     -v signal-state:/home/.local \
     --network signal \
     -e 'MODE=json-rpc' bbernhard/signal-cli-rest-api
```

- create a command and control group chat with the bot
- create .env with
  - SIGNAL_SERVICE=localhost:9922
  - PHONE_NUMBER The number of the signal account
  - WELCOME_MANAGER The signal ID of the manager
  - WELCOME_CNC The command and control group chat ID

testlocally with 
```
uv sync
uv run pytest
uv run python -m welcomebot
```

migrating these files to the volume:
 - signalbot_internal_state.db
 - bot_memory.db

then run the bot in it's own container:
```
docker run -d --name welcomebot --restart=always  \
     -v signal-state:/home/.local \
     --env-file .env -e SIGNAL_SERVICE=127.0.0.1:8080 \
     --network container:signal-api \
     welcomebot
```

*TODO*: dockercompose

## controlling the bot

- send `help` to the bot in the CNC chat
- invite the bot to a group you want to manage
- send `list_groups` to the bot in the CNC chat
- set the welcome mesage for the group:
```
set_motd 0
hello and welcome to the chat.
please adhere to group guidlines at
https://codeforamerica.org/code-of-conduct/
```
