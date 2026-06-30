from datetime import datetime, UTC
import logging
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

from welcomebot import Attachment, Calendar, Reminder, Reminders, Message

DATE = [ 2026, 5, 26, 16, 47, 10, 1, UTC ]
TODAY = 2461187
CHAT_ID_1 = "chatIDOne"
MESSAGE_1 = Message("message one")
WEEKLY = 7
CHAT_ID_2 = "chatIDTwo"
MESSAGE_2 = Message("message two")
MONTHLY = 30
NO_REPEAT = 0

ONE_REMINDER = [ Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_1, 1) ]
TWO_REMINDERS = [ 
    Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_1, 1),
    Reminder(CHAT_ID_2, TODAY, MONTHLY, MESSAGE_2, 2),
]
ONE_SHOT = [ Reminder(CHAT_ID_1, TODAY, 0, MESSAGE_1, 1) ]
# store should return these ordered by due date ascending
OVERLAPPING_REMINDERS = [ 
    Reminder(CHAT_ID_1, TODAY - 1, WEEKLY, MESSAGE_1, 1),
    Reminder(CHAT_ID_1, TODAY, MONTHLY, MESSAGE_2, 2), 
]
REPEATING_AND_NONREPEATING_REMINDERS = [ 
    Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_1, 1),
    Reminder(CHAT_ID_1, TODAY, NO_REPEAT, MESSAGE_2, 2), 
]
OLD_REMINDER = [ 
    Reminder(CHAT_ID_1, TODAY - 30, 7, MESSAGE_1, 1),
]

logger = logging.getLogger("welcomebot")

@pytest.fixture
def cal():
    dt = SimpleNamespace()
    dt.now = MagicMock(return_value=datetime(*DATE))
    return Calendar(dt=dt)


@pytest.fixture
def store():
    fake_store = SimpleNamespace()
    fake_store.get_due_reminders = MagicMock(return_value=[])
    fake_store.repost_reminder = MagicMock()
    fake_store.delete_reminder = MagicMock()
    fake_store.get_reminder = MagicMock()
    return fake_store


@pytest.fixture
def bot():
    fake_bot = SimpleNamespace()
    fake_bot.send = AsyncMock()
    return fake_bot


@pytest.fixture
def reminders(bot, store, cal):
    return Reminders(logger, bot, store, cal)


async def test_empty_process(reminders):
    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    reminders.store.repost_reminder.assert_not_called()
    reminders.bot.send.assert_not_called()


async def test_one_process(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=ONE_REMINDER)

    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    reminders.bot.send.assert_called_once_with(CHAT_ID_1, MESSAGE_1.text)
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
    reminders.bot.send.assert_called_once_with(CHAT_ID_1, MESSAGE_1.text)
    reminders.store.repost_reminder.assert_not_called()
    reminders.store.delete_reminder.assert_called_once_with(1)
    

async def test_rich_reminder(reminders):
    rich = ONE_SHOT[0]
    rich.message = Message(MESSAGE_1.text, [Attachment('foo', '0000')])
    reminders.store.get_due_reminders = MagicMock(return_value=[rich])
    reminders.store.get_reminder = MagicMock(return_value=rich)

    await reminders.process_queue()
    
    assert len(reminders.bot.send.call_args.args) == 2
    assert CHAT_ID_1 in reminders.bot.send.call_args.args[0]
    assert MESSAGE_1.text in reminders.bot.send.call_args.args[1]
    assert '0000' == reminders.bot.send.call_args.kwargs['base64_attachments'][0]


async def test_two_process(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=TWO_REMINDERS)

    await reminders.process_queue()
    
    reminders.store.get_due_reminders.assert_called_once()
    reminders.bot.send.assert_has_calls([
        call(CHAT_ID_1, MESSAGE_1.text),
        call(CHAT_ID_2, MESSAGE_2.text)
    ])
    reminders.store.repost_reminder.assert_has_calls([
        call(1, TODAY + WEEKLY),
        call(2, TODAY + MONTHLY)
    ])


async def test_overlapping(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=OVERLAPPING_REMINDERS)
    
    await reminders.process_queue()

    # the second message to the same group should be delayed to tomorrow
    reminders.bot.send.assert_called_once_with(CHAT_ID_1, MESSAGE_1.text)
    reminders.store.repost_reminder.assert_called_once_with(1, TODAY - 1 + WEEKLY)


async def test_prioritize_non_repeating(reminders):
    reminders.store.get_due_reminders = MagicMock(return_value=REPEATING_AND_NONREPEATING_REMINDERS)
    
    await reminders.process_queue()

    # the second message to the same group should be delayed to tomorrow
    reminders.bot.send.assert_called_once_with(CHAT_ID_1, MESSAGE_2.text)
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
    assert Reminder(CHAT_ID_1, TODAY, NO_REPEAT, MESSAGE_1, 2) < Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_2, 1)
    assert Reminder(CHAT_ID_1, TODAY, NO_REPEAT, MESSAGE_1, 2) < Reminder(CHAT_ID_1, TODAY - 1, WEEKLY, MESSAGE_2, 1)
    assert Reminder(CHAT_ID_1, TODAY, NO_REPEAT, MESSAGE_1, 2) < Reminder(CHAT_ID_1, TODAY - 5, MONTHLY, MESSAGE_2, 1)
    

def test_order_overdue_reminders_first():
    assert Reminder(CHAT_ID_1, TODAY - 1, WEEKLY, MESSAGE_1, 2) < Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_1, 1)
    # regardless of how often they are supposed to post
    assert Reminder(CHAT_ID_1, TODAY - 1, MONTHLY, MESSAGE_1, 2) < Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_1, 1)
    # non-repeating reminders also sort by most over-due first between them
    assert Reminder(CHAT_ID_1, TODAY - 1 , NO_REPEAT, MESSAGE_1, 2) < Reminder(CHAT_ID_1, TODAY, NO_REPEAT,  MESSAGE_2, 1)


def test_order_draft_reminders_first():
    assert Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_1) < Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_1, 2)
    assert Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_1, 1) > Reminder(CHAT_ID_1, TODAY, WEEKLY, MESSAGE_1)


def test_order_accept_null_messages():
    try:
        Reminder(CHAT_ID_1, TODAY, WEEKLY, None, 2) < Reminder(CHAT_ID_1, TODAY, WEEKLY, 'ZZZ', 2)
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