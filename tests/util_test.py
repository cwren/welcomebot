from copy import deepcopy
import logging
import pytest
import random
from types import SimpleNamespace
from unittest.mock import MagicMock

from welcomebot import update_group

from .conftest import CNC_GROUP, GROUPS, FakeGroupDir
from .conftest import SOCIAL_GROUP
from .conftest import USER_1
from .conftest import USER_2

logger = logging.getLogger("store_test")


async def test_null_members(bot, store):
    assert not await update_group(logger, bot, "not a group", store)
    store.put_members.assert_not_called()
    assert "foo" not in store.retain_only.call_args.args
    for g in GROUPS:
        assert g.internal_id in store.retain_only.call_args.args[0]


async def test_same_members(bot, store):
    assert not await update_group(logger, bot, SOCIAL_GROUP.internal_id, store)
    store.put_members.assert_not_called()
    store.put_members.retain_only()


async def test_new_members(bot, store):
    SOCIAL_GROUP_BIGGER = deepcopy(SOCIAL_GROUP)
    SOCIAL_GROUP_BIGGER.members.append(USER_2)
    bot.groups = FakeGroupDir([ CNC_GROUP, SOCIAL_GROUP_BIGGER ])

    assert await update_group(logger, bot, SOCIAL_GROUP.internal_id, store)

    store.put_members.assert_called_once()
    store.put_members.retain_only()


async def test_removed_members(bot, store):
    store.get_members = MagicMock(return_value=[USER_1, USER_2])

    assert not await update_group(logger, bot, SOCIAL_GROUP.internal_id, store)

    store.put_members.assert_called_once()
    store.retain_only.assert_called_once()
