# configuring the bot

## Startup Configuration

Some of the low-level or sensitive configuration is accomplished via environment variables, often supplied via a `.env` file.

your `.env` file should probably contain these things (there are defaults, but it's nice to be intentional):
 - `SIGNAL_SERVICE=localhost:8080` this works in the docker compose environment, salt to taste wherever your environment puts the `signal-cli-rest-api` endpoint 
 - `PHONE_NUMBER=+12345678901` the phone number of the bot account. You should probably have a separate account for the bot, but you don't have to
 - `WELCOME_MANAGER=12345678-1234-1234-1234-1234567890ab` comma-separated list of [UUID](https://github.com/bbernhard/signal-cli-rest-api/blob/1a2da6c79b6dce68317a714d3f4015d18e30dcad/src/docs/swagger.json#L866)s of the manager accounts that the bot should trust to execute commands
 - `WELCOME_CNC=AbCdEfGhIjKlMnOpQrStUvWxYz01234567898765432=` the [`internal_id`](https://github.com/bbernhard/signal-cli-rest-api/blob/1a2da6c79b6dce68317a714d3f4015d18e30dcad/src/docs/swagger.json#L798) of the one group chat where the bot will accept commands
- `LOGTAG=MyWelcomeBot` a tag prefix to help you find your logs
- `LOGLEVEL=Warning` a [python logging-level](https://docs.python.org/3/library/logging.html#logging-levels), note that `DEBUG` may inject personally identifying information into your logs
- `REMINDER_TIMES=17,18` times of day the bot will post reminders, one reminder per group per time slot. Times interpreted in the local time zone of the process. 
- `INSTANT_WELCOME=false` a value of `true` will attempt to sent the welcome message as soon as the bot receives a group update message that adds someone to the group roster. A `false` value will delay the post to the next `WELCOMER_TIMES` event.
- `WELCOMER_TIMES=*` The `*` will instruct the bot to scan for new members every hour, on the half hour, in any group with an active welcome (`motd`) message set and post the welcome message if any are found. This will catch any members where the `GROUP_UPDATE_MESSAGE` message 

The `REMINDER_TIMES` and `WELCOMER_TIMES` configuration strings will be passed to an [apscheduler cron trigger](https://github.com/agronholm/apscheduler/blob/26bff5d1001d8d259f4d7ddaad6cf055072bb257/src/apscheduler/triggers/cron/__init__.py#L25) as the `hours` field.

## Run-Time Configuration

Most of the configuration is done by sending messages to the bot via Signal. Send `help` to the bot in the CNC chat for the full list of run-time commands.

Note that the bot will only respond to the managers listed in the `WELCOME_MANAGER` environment variable and only in the command and control room specified in the `WELCOME_CNC` environment variable. See [Getting Started](./getting_started.md) for more details. 

### Creating a Welcome Message

This feature is useful for posting instructions that new members need right away. If you have a waiting room where new members wait to be vetted into the organization, this is a good way to post the instructions they need, since they won't be able to see any previous messages.

- invite the bot to a group you want to manage
- send `list_groups` to the bot in the CNC chat
- note the short code for the group
- set the welcome message for the group:
```
set_motd ABCD
hello and welcome to the waiting room.
Someone will contact you soon to begin the onboarding process.
While you wait, you might want to....
```

The short codes help disambiguate groups that might have the same names.

### Creating Periodic Reminders

These are useful for posting information that should remain visible to members despite the disappearing message setting, such as a code of conduct post, for example.

- find the group short code as above
- set the reminder by posting the CNC channel
```
set_reminder ABCD 1 7
thank you for being here, please remember to be kind to each other
https://codeforamerica.org/code-of-conduct/
```

This would post the~ code of conduct to the ABCD group once a week (every *`7`* days) starting today (in *`1`* day). The delay (*`1`* in the above example, is useful when scheduling a bunch of reminders that you want spread out over time). Note that the bot will only post one message at a time per group. It prefers non-repeating messages over repeating messages (second argument of `0`) and prefers the most overdue message over others. If you want multiple messages to post per day, supply multiple posting hours in the `REMINDER_TIMES` environment variable. 

### Mentions Support (sort of)

The Signal app does not allow you to mention people who are not in the group, so adding mentions to `set_motd` or `set_reminder` messages is not possible unless that person is in the CNC chat room (which would be awkward and probably not generally advisable).

However, the bot has no such limitation. A properly formatted mentions payload will render in the app correctly even if the mentioned account is not in the target group (or the CNC channel). Tapping on the mention takes the user to a DM with that account, which is exactly the desired result for messages like "contact @foo for help with bar".

Author messages to the bot using @uuid format instead, and the bot will send them as real mentions:
```
set_reminder ABCD 0 14
please contact @12345678-1234-1234-1234-1234567890ab for help with ordering t-shirts
```

## Where to find UUIDs and Group IDs

Mentions and `WELCOME_MANAGER` configuration require knowing the UUID of accounts, and the `WELCOME_CNC` variable requires recovering he internal ID of that group,  but the Signal UI does not surface these. You can find these IDs in the debug output of the `signal-cli-rest-api` process, or you can use tools like [signal-id](https://github.com/cwren/signal-id) to help.