from unittest.mock import call

from signalbot import SendMessage

class FakeCall():
    def __init__(self, receiver=None, text=None, mentions=None, attachments=None):
        self.receiver = receiver
        self.text = text
        self.mentions = mentions
        self.attachments = attachments

def assert_sent_once(vector, fakecall):
    if fakecall.receiver:
        vector.send.assert_called_once_with(SendMessage(text=fakecall.text, text_mode='styled', mentions=fakecall.mentions, attachments=fakecall.attachments), recipient=fakecall.receiver)
    else:
        vector.send.assert_called_once_with(SendMessage(text=fakecall.text, text_mode='styled', mentions=fakecall.mentions, attachments=fakecall.attachments))

def assert_sent_multiple(vector, fakecalls):
    calls = []
    for fakecall in fakecalls:
        if fakecall.receiver:
            calls.append(call(SendMessage(text=fakecall.text, text_mode='styled', mentions=fakecall.mentions, attachments=fakecall.attachments), recipient=fakecall.receiver))
        else:
            calls.append(call(SendMessage(text=fakecall.text, text_mode='styled', mentions=fakecall.mentions, attachments=fakecall.attachments)))
    vector.send.assert_has_calls(calls, any_order=True)
