# json-rpc mode for the signalbot library

sudo docker run -d  --name signal-api --restart=always -p 9922:8080 \
     -v signal-state:/home/.local \
     -e 'MODE=json-rpc' bbernhard/signal-cli-rest-api

- create .env with
  - SIGNAL_SERVICE=localhost:9922
  - PHONE_NUMBER The number of the signal account
  - WELCOME_MANAGER The signal ID of the manager
  - WELCOME_CNC The command and control group chat ID

uv sync
uv run pytest
uv run python -m welcomebot

docker container stop signal-api
docker container rm signal-api   

if migrating an existing bot, copy:
 - signalbot_internal_state.db
 - bot_memory.db
 
# native mode for the pysignalclirestapi library

sudo docker run -d  --name signal-api --restart=always -p 9922:8080  \
     -v signal-state:/home/.local/share/signal-cli \
     -e 'MODE=native' bbernhard/signal-cli-rest-api

