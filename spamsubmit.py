#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
import email
import logging
import smtplib
import sys
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from imapclient import IMAPClient, SEEN
import passencrypt

config = configparser.ConfigParser()
config.read(sys.argv[1])

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


def print_folders():
    for (flags, delimiter, name) in imap.list_folders():
        print(name)


def process_new_messages():
    logging.info('Processing new messages')
    imap.select_folder(config['folders']['to_submit'])
    messages = imap.search()
    logging.info('Got %d messages', len(messages))
    for uid, message_data in imap.fetch(messages, "RFC822").items():
        message_bytes = message_data[b"RFC822"]
        email_message = email.message_from_bytes(message_bytes)
        logging.info('Message %d, %d bytes, From (%s), Subject "%s"', uid, len(message_bytes),
                     email_message.get("From"),
                     email_message.get("Subject"))
        submit_spam(email_message)
        imap.move(uid, config['folders']['submitted'])
    logging.info('Finished processing new messages')


def submit_spam(spam: Message):
    message = email.mime.multipart.MIMEMultipart()
    message["From"] = config['smtp']['sender']
    message["To"] = config['spamcop']['to']
    message["Subject"] = config['spamcop']['subject']
    message.attach(MIMEText(config['spamcop']['message'], "plain"))

    part = MIMEBase("message", "rfc822")
    part.set_payload(spam.as_string())
    part.add_header("Content-Disposition", "attachment; filename=\"message.eml\"")
    message.attach(part)

    with smtplib.SMTP_SSL(config["smtp"]["host"], int(config["smtp"]["port"])) as smtp:
        smtp.login(config["smtp"]["username"], passencrypt.decrypt(config['smtp']['password']))
        response = smtp.sendmail(message["From"], message["To"], message.as_string())
        smtp.quit()
        if len(response) > 0:
            logging.error('Error sending message: %s', response)
        else:
            imap.append(config['folders']['sent'], message.as_string(), (SEEN,))


def run():
    global imap
    imap = IMAPClient(config['imap']['host'], use_uid=True)
    imap.login(config['imap']['username'], passencrypt.decrypt(config['imap']['password']))
    imap.select_folder(config['folders']['to_submit'])
    process_new_messages()
    is_idle = False
    while True:
        try:
            imap.idle()
            is_idle = True
            responses = imap.idle_check(timeout=600)
            imap.idle_done()
            is_idle = False
            for (size, message) in responses:
                if message.decode('UTF-8') == 'EXISTS' and size > 0:
                    process_new_messages()
        except KeyboardInterrupt:
            break
        finally:
            if is_idle:
                imap.idle_done()
    logging.info('Terminating')
    imap.logout()


if __name__ == '__main__':
    run()
