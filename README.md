# Welcome Bot

A bot that performs some routine tasks useful for organizations operating on Signal. Primary intended use case is posting messages either periodically or when peple join a group to keep informational posts available that might otherwise slip past the disappearing message horizon, or be invisible to new members.

Primary Functions:
- monitors chat groups and post a message when people join
  - either immediately
  - or periodically
- post periodic reminders to the group
  - code of conduct
  - directories of other groups
  - anything you can compose in a message to the bot

Features:
- supports attachments and mentions (sort of)
- configure mostly by chatting with the bot
- no LLMs were harmed, this is old-school
- data stays in the hosting environment of your choice
  - host privately
  - docker compose formula for cloud hosting

More information in [Getting Started](./docs/getting_started.md) and [Configuration](./docs/configuration.md)

## Primary Dependancies

- https://github.com/bbernhard/signal-cli-rest-api
- https://github.com/signalbot-org/signalbot
