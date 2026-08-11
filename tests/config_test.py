import logging
import os

from welcomebot import Configuration

logger = logging.getLogger("config_test")

def setup_module(module):
    os.environ["SIGNAL_SERVICE"] = "remotehost:1234"
    os.environ["PHONE_NUMBER"] = "+12345678901"
    os.environ["LOGLEVEL"] = "MYLOGLEVEL"
    os.environ["LOGTAG"] = "MYLOGTAG"
    os.environ["WELCOME_CNC"] = "MYCNCROOM"
    os.environ["WELCOME_MANAGER"] = "MANAGER1, MANAGER2"
    os.environ["INSTANT_WELCOME"] = "false"
    os.environ["REMINDER_TIMES"] = "10,20"
    os.environ["WELCOME_TIMES"] = "5,15"


def test_config():
    config = Configuration(logger)

    assert config.logger == logger
    assert config.signal_service == "remotehost:1234"
    assert config.phone_number == "+12345678901"
    assert config.log_level == "MYLOGLEVEL"
    assert config.log_tag == "MYLOGTAG"
    assert config.welcome_cnc == "MYCNCROOM"
    assert config.welcome_managers == ["MANAGER1", "MANAGER2"]
    assert config.instant_welcome == False
    assert config.reminder_times == "10,20"
    assert config.welcome_times == "5,15"


def test_strings():
    config = Configuration(logger)
    strings = config.to_strings()
    string = " ".join(strings)
    assert "remotehost:1234" in string
    assert "+12345678901" in string
    assert "MYLOGLEVEL" in string
    assert "MYLOGTAG" in string
    assert "MYCNCROOM" in string
    assert "MANAGER1" in string
    assert "MANAGER2" in string
    assert "False" in string
    assert "10,20" in string
    assert "5,15" in string