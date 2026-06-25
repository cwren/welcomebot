from collections import Counter

class Attachment:
    def __init__(self, filename, data=None):
        self.data = data
        self.filename = filename

class Message:
    def __init__(self, text, attachments=[]):
        self.text = text
        self.attachments = attachments


    def __str__(self):
        return f'{self.text}\n[with {len(self.attachments)} attachments]'


    def __eq__(self, other):
        if isinstance(other, Message):
            return (self.text == other.text and
                    Counter(self.attachments) == Counter(other.attachments))
        return NotImplemented
        
        
    def send(self, vector, receiver=None):
        attachment_data = [a.data for a in self.attachments] if self.attachments else None
        if receiver:
            # send via bot interface to a specific recipient
            if attachment_data:
                return vector.send(receiver, self.text, base64_attachments=attachment_data)
            else:
                return vector.send(receiver, self.text)
        else:
            # reply to a message context
            if attachment_data:
                return vector.send(self.text, base64_attachments=attachment_data)
            else:
                return vector.send(self.text)