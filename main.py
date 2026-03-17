import logging
import os
from dotenv import load_dotenv
from pysignalclirestapi import SignalCliRestApi

done = False


def main():
    signal = SignalCliRestApi(
        'http://' + os.getenv("SIGNAL_SERVICE"),
        os.getenv("PHONE_NUMBER"))
    while(not done):
        myMessages = signal.receive(send_read_receipts=True)
        for message in myMessages:
            if 'dataMessage' in message['envelope']:
                address = message['envelope']['sourceUuid']
                name = message['envelope']['sourceName']
                body = message['envelope']['dataMessage']['message']
                print('from %s received %s' % (name, body))
                signal.send_message(
                    message=f'I heard {body}',
                    recipients=address)


            
if __name__ == "__main__":
    load_dotenv()
    main()
