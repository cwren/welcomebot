# Welcome Bot

A bot that monitors signal chat groups and posts a message when people join

## Getting Started 

**Note**: this is a work in progress. These setup instructions are very rough and will be evolving rapidly.

Create a local volume to hold the state of the signal-api and the welcomebot. This volume will be replaced by an encrypted volume in the cloud: 
```
docker volume create welcomebot_state
```

Also create a bridge nwork that you will need later:
```
docker network create --driver bridge signal
```


Register your account with signal-api, but link the volume in a little higher in the filesystem so we can use the volume for other state sotrage as well:
```
docker run --detach --name signal-api --restart=always -p 8080:8080 \
      --volume welcomebot_state:/home/.local \
      --network signal \
      -e 'MODE=json-rpc' bbernhard/signal-cli-rest-api
```

run signal-api using that volume:
```
docker run -d  --name signal-api --restart=always -p 9922:8080 \
     -v welcomebot_state:/home/.local \
     --network signal \
     -e 'MODE=json-rpc' bbernhard/signal-cli-rest-api
```

Open the registration QR code at http://localhost:8080/v1/qrcodelink?device_name=welcome-bot
And scan it with the "link account" flow from the phone with the bot account.

Note that the bot will have access to all the contacts and chats of the account
you link it to. **You should not use your personal Signal account for this.** You 
should get a separate phone number, create a Signal account with that number, 
and then use that account only for the bot.

Replace 12125551212 with the bot's phone number and execute these commands.
```
curl http://localhost:8080/v1/groups/+12125551212
curl http://localhost:8080/v1/contacts/+112125551212
```
If you are using a fresh Signal account (you are, right?), then they should both
return an empty result: `[]`.

Send the bot account a message from the account you want it to trust as the
management account. Accept that message as the bot using the phone. Then
invite it to a group chat with a title you will remember, like "Welcomebot
Control Room".

Rerun those `curl` commands above and look for the new (only!) responses. 

The value WELCOME_MANAGER will be the `uuid` of your entry in the response 
to the contacts query. The value of WELCOME_CNC will be the `internal_id`
in the response to the groups query.

Now create .env with:
```
SIGNAL_SERVICE=localhost:8080
PHONE_NUMBER=...
WELCOME_MANAGER=...
WELCOME_CNC=...
```

Then test locally with:
```
uv sync
uv run pytest
uv run python -m welcomebot
```

If you send the message "help" to the bot in the CNC channel, it
should reply with a help message.

## containerized!

Now you should be able to copy your local state to a volume and run the bot in it's own container:
```
# copy state into the volume
docker build -f copypaste.dockerfile -t copypaste .
docker run -it -v ~/.local/share:/home/a -v wecomebot_state:/home/b copypaste

# run the bot
docker build -f docker/welcomebot.dockerfile -t welcomebot .
docker run -d --name welcomebot --restart=always  \
     -v welcomebot_state:/home/.local \
     --env-file .env \
     --network container:signal-api \
     welcomebot
```

## compose 

Stop the other containers and use `compose.yaml` config to bring the services up together:
```
docker compose up
```

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
## Release Process

```
uv run pytest
uv version --bump patch
uv build 
git push
uv publish
```


