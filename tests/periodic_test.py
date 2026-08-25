from datetime import datetime, UTC
import logging
from pathlib import Path
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

from welcomebot import Attachment, Calendar, Reminder, Reminders, Message   

from .utils import FakeCall, assert_sent_once, assert_sent_multiple

from .conftest import NEW_CHAT_ID
from .conftest import SOCIAL_CHAT_ID
from .conftest import DATE
from .conftest import TODAY

MESSAGE_1 = Message("message one")
MESSAGE_2 = Message("message two")
WEEKLY = 7
MONTHLY = 30
NO_REPEAT = 0

AT = '12345678-1234-1234-1234-1234567890ab'
MESSAGE_AT = Message(f'message one @{AT}')
MESSAGE_AT_SENT = f'message one \uFFFC'
MESSAGE_AT_START = 12

ONE_REMINDER = [ Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_1, 1) ]
TWO_REMINDERS = [ 
    Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_1, 1),
    Reminder(NEW_CHAT_ID, TODAY, MONTHLY, MESSAGE_2, 2),
]
ONE_SHOT = [ Reminder(SOCIAL_CHAT_ID, TODAY, 0, MESSAGE_1, 1) ]
# store should return these ordered by due date ascending
OVERLAPPING_REMINDERS = [ 
    Reminder(SOCIAL_CHAT_ID, TODAY - 1, WEEKLY, MESSAGE_1, 1),
    Reminder(SOCIAL_CHAT_ID, TODAY, MONTHLY, MESSAGE_2, 2), 
]
REPEATING_AND_NONREPEATING_REMINDERS = [ 
    Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_1, 1),
    Reminder(SOCIAL_CHAT_ID, TODAY, NO_REPEAT, MESSAGE_2, 2), 
]
OLD_REMINDER = [ 
    Reminder(SOCIAL_CHAT_ID, TODAY - 30, 7, MESSAGE_1, 1),
]

logger = logging.getLogger("periodic_test")


@pytest.fixture
def config():
    config = SimpleNamespace()
    config.logger = logger
    return config


@pytest.fixture
def reminders(config, bot, store, cal):
    return Reminders(config, bot, store, cal)


async def test_empty_process(reminders):
    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    reminders.store.repost_reminder.assert_not_called()
    reminders.bot.messages.send.assert_not_called()


async def test_one_process(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=ONE_REMINDER)

    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    assert_sent_once(reminders.bot.messages, receiver=SOCIAL_CHAT_ID, text=MESSAGE_1.text)
    reminders.store.repost_reminder.assert_called_once_with(1, TODAY + WEEKLY)
    reminders.store.delete_reminder.assert_not_called()


async def test_stale(reminders):
    reminder = ONE_REMINDER[0]
    reminder.next -= 30 # 30 days late
    reminders.store.get_due_reminders = MagicMock(return_value=[reminder])

    await reminders.process_queue()
    
    # message is weekly, it's 30 days, or 4 weeks and 2 days late
    # the next message should go out in 5 days to get back on schedule
    reminders.store.repost_reminder.assert_called_once_with(1, TODAY + 5)
    

async def test_one_shot(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=ONE_SHOT)

    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    assert_sent_once(reminders.bot.messages, receiver=SOCIAL_CHAT_ID, text=MESSAGE_1.text)
    reminders.store.repost_reminder.assert_not_called()
    reminders.store.delete_reminder.assert_called_once_with(1)
    

async def test_rich_reminder(reminders):
    rich = ONE_SHOT[0]
    rich.message = Message(MESSAGE_1.text, [Attachment('bar', dir='foo', data='0000')])
    reminders.store.get_due_reminders = MagicMock(return_value=[rich])
    reminders.store.get_reminder = MagicMock(return_value=rich)

    await reminders.process_queue()
    
    assert_sent_once(reminders.bot.messages, SOCIAL_CHAT_ID, MESSAGE_1.text, attachments=['foo/bar'])
    

async def test_mention_reminder(reminders):
    at = ONE_SHOT[0]
    at.message = Message(MESSAGE_AT.text)
    reminders.store.get_due_reminders = MagicMock(return_value=[at])

    await reminders.process_queue()

    assert_sent_once(reminders.bot.messages, SOCIAL_CHAT_ID, MESSAGE_AT_SENT, mentions=[{ 'start': MESSAGE_AT_START, 'length': 1, 'author': AT }])

async def test_two_process(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=TWO_REMINDERS)

    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    assert_sent_multiple(reminders.bot.messages, [
        FakeCall(SOCIAL_CHAT_ID, MESSAGE_1.text),
        FakeCall(NEW_CHAT_ID, MESSAGE_2.text),
    ])
    reminders.store.repost_reminder.assert_has_calls([
        call(1, TODAY + WEEKLY),
        call(2, TODAY + MONTHLY),
    ], any_order=True)


async def test_overlapping(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=OVERLAPPING_REMINDERS)
    
    await reminders.process_queue()

    # the second message to the same group should be delayed to tomorrow
    assert_sent_once(reminders.bot.messages, receiver=SOCIAL_CHAT_ID, text=MESSAGE_1.text)
    reminders.store.repost_reminder.assert_called_once_with(1, TODAY - 1 + WEEKLY)


async def test_prioritize_non_repeating(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=REPEATING_AND_NONREPEATING_REMINDERS)
    
    await reminders.process_queue()

    # the second message to the same group should be delayed to tomorrow
    assert_sent_once(reminders.bot.messages, receiver=SOCIAL_CHAT_ID, text=MESSAGE_2.text)
    reminders.store.repost_reminder.assert_not_called()


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


def test_order_non_repeating_reminders_first():
    # non-repeating go before repeating, even if those are overdue 
    assert Reminder(SOCIAL_CHAT_ID, TODAY, NO_REPEAT, MESSAGE_1, 2) < Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_2, 1)
    assert Reminder(SOCIAL_CHAT_ID, TODAY, NO_REPEAT, MESSAGE_1, 2) < Reminder(SOCIAL_CHAT_ID, TODAY - 1, WEEKLY, MESSAGE_2, 1)
    assert Reminder(SOCIAL_CHAT_ID, TODAY, NO_REPEAT, MESSAGE_1, 2) < Reminder(SOCIAL_CHAT_ID, TODAY - 5, MONTHLY, MESSAGE_2, 1)
    

def test_order_overdue_reminders_first():
    assert Reminder(SOCIAL_CHAT_ID, TODAY - 1, WEEKLY, MESSAGE_1, 2) < Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_1, 1)
    # regardless of how often they are supposed to post
    assert Reminder(SOCIAL_CHAT_ID, TODAY - 1, MONTHLY, MESSAGE_1, 2) < Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_1, 1)
    # non-repeating reminders also sort by most over-due first between them
    assert Reminder(SOCIAL_CHAT_ID, TODAY - 1 , NO_REPEAT, MESSAGE_1, 2) < Reminder(SOCIAL_CHAT_ID, TODAY, NO_REPEAT,  MESSAGE_2, 1)


def test_order_draft_reminders_first():
    assert Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_1) < Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_1, 2)
    assert Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_1, 1) > Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, MESSAGE_1)


def test_order_accept_null_messages():
    try:
        Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, None, 2) < Reminder(SOCIAL_CHAT_ID, TODAY, WEEKLY, 'ZZZ', 2)
    except:
        pytest.fail()

def test_today():
    dt = SimpleNamespace()
    dt.now = MagicMock(return_value=datetime(2026, 5, 26, 0, 47, 10, 1, UTC))
    assert Calendar(dt=dt).today() == TODAY
    dt.now = MagicMock(return_value=datetime(2026, 5, 26, 1, 47, 10, 1, UTC))
    assert Calendar(dt=dt).today() == TODAY
    dt.now = MagicMock(return_value=datetime(2026, 5, 26, 5, 47, 10, 1, UTC))
    assert Calendar(dt=dt).today() == TODAY
    dt.now = MagicMock(return_value=datetime(2026, 5, 26, 12, 47, 10, 1, UTC))
    assert Calendar(dt=dt).today() == TODAY
    dt.now = MagicMock(return_value=datetime(2026, 5, 26, 23, 47, 10, 1, UTC))
    assert Calendar(dt=dt).today() == TODAY
    dt.now = MagicMock(return_value=datetime(2026, 5, 27, 0, 47, 10, 1, UTC))
    assert Calendar(dt=dt).today() == TODAY + 1

def test_to_ymd():
    dt = SimpleNamespace()
    dt.now = MagicMock()
    assert Calendar(dt=dt).to_ymd(TODAY) == "2026-05-26"
    assert Calendar(dt=dt).to_ymd(TODAY + 1) == "2026-05-27"
    assert Calendar(dt=dt).to_ymd(TODAY - 1) == "2026-05-25"
    dt.now.assert_not_called()