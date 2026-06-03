from datetime import datetime, UTC
import logging
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

from welcomebot import Calendar, Reminder, Reminders

DATE = [ 2026, 5, 26, 16, 47, 10, 1, UTC ]
TODAY = 2461187
CHAT_ID_1 = "chatIDOne"
MESSAGE_1 = "message one"
INTERVAL_1 = 7
CHAT_ID_2 = "chatIDTwo"
MESSAGE_2 = "message two"
INTERVAL_2 = 2

ONE_REMINDER = [ Reminder(CHAT_ID_1, TODAY, 7, MESSAGE_1, 1) ]
TWO_REMINDERS = [ 
    Reminder(CHAT_ID_1, TODAY, INTERVAL_1, MESSAGE_1, 1),
    Reminder(CHAT_ID_2, TODAY, INTERVAL_2, MESSAGE_2, 2),
]
ONE_SHOT = [ Reminder(CHAT_ID_1, TODAY, 0, MESSAGE_1, 1) ]
# store should return these ordered by due date ascending
OVERLAPPING_REMINDERS = [ 
    Reminder(CHAT_ID_1, TODAY - 1, INTERVAL_1, MESSAGE_1, 1),
    Reminder(CHAT_ID_1, TODAY, INTERVAL_2, MESSAGE_2, 2), 
]

logger = logging.getLogger("welcomebot")

@pytest.fixture
def store():
    fake_store = SimpleNamespace()
    fake_store.get_due_reminders = MagicMock(return_value=[])
    fake_store.repost_reminder = MagicMock()
    fake_store.delete_reminder = MagicMock()
    return fake_store


@pytest.fixture
def bot():
    fake_bot = SimpleNamespace()
    fake_bot.send = AsyncMock()
    return fake_bot


@pytest.fixture
def reminders(bot, store):
    return Reminders(logger, bot, store)


async def test_empty_process(reminders):
    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    reminders.store.repost_reminder.assert_not_called()
    reminders.bot.send.assert_not_called()


async def test_one_process(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=ONE_REMINDER)

    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    reminders.bot.send.assert_called_once_with(CHAT_ID_1, MESSAGE_1)
    reminders.store.repost_reminder.assert_called_once_with(1)
    reminders.store.delete_reminder.assert_not_called()


async def test_one_shot(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=ONE_SHOT)

    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    reminders.bot.send.assert_called_once_with(CHAT_ID_1, MESSAGE_1)
    reminders.store.repost_reminder.assert_not_called()
    reminders.store.delete_reminder.assert_called_once_with(1)


async def test_two_process(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=TWO_REMINDERS)

    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    reminders.bot.send.assert_has_calls([
        call(CHAT_ID_1, MESSAGE_1),
        call(CHAT_ID_2, MESSAGE_2)
    ])
    reminders.store.repost_reminder.assert_has_calls([
        call(1),
        call(2)
    ])


async def test_overlapping(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=OVERLAPPING_REMINDERS)
    
    await reminders.process_queue()

    # the second message to the same group should be delayed to tomorrow
    reminders.bot.send.assert_called_once_with(CHAT_ID_1, MESSAGE_1)
    reminders.store.repost_reminder.assert_called_once_with(1)


def test_real_today():
    cal = Calendar()
    assert cal.today() > 2461000 # safely in the past


def test_fake_today():
    now = datetime(*DATE)
    dt = SimpleNamespace()
    dt.now = MagicMock(return_value=now)
    cal = Calendar(dt)
    assert cal.today() == TODAY


def test_decode():
    cal = Calendar()
    assert cal.to_ymd(TODAY) == '2026-05-26'
    assert cal.to_ymd(TODAY - 1) == '2026-05-25'