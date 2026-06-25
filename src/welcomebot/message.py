from collections import Counter

class Attachment:
    def __init__(self, filename, data=None):
        self.data = data
        self.filename = filename


    def __eq__(self, other):
        if isinstance(other, Attachment):
            return (self.filename == other.filename and
                    self.data == other.data)
        return NotImplemented
    
    
    def __hash__(self):
        return hash((self.filename, self.data))


class Message:
    def __init__(self, text, attachments=[], has_attachments=False):
        self.text = text
        self.attachments = attachments
        self.has_attachments = len(attachments) > 0 if attachments else has_attachments


    def __str__(self):
        return f'{self.text}\n[with {len(self.attachments)} attachments]'


    def __eq__(self, other):
        if isinstance(other, Message):
            return (self.text == other.text and
                    Counter(self.attachments) == Counter(other.attachments))
        return NotImplemented
        
        
    def send(self, vector, receiver=None, preamble=""):
        attachment_data = [a.data for a in self.attachments] if self.attachments else None
        if receiver:
            # send via bot interface to a specific recipient
            if attachment_data:
                return vector.send(receiver, preamble + self.text, base64_attachments=attachment_data)
            else:
                return vector.send(receiver, preamble + self.text)
        else:
            # reply to a message context
            if attachment_data:
                return vector.send(preamble + self.text, base64_attachments=attachment_data)
            else:
                return vector.send(preamble + self.text)