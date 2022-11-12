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

from imapclient import IMAPClient
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
    for uid, message_data in imap.fetch(messages, "RFC822").items():
        email_message = email.message_from_bytes(message_data[b"RFC822"])
        print(uid, email_message.get("From"), email_message.get("Subject"))
        submit_spam(email_message)
        imap.move(uid, config['folders']['submitted'])


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

    with smtplib.SMTP_SSL(config["smtp"]["host"], int(config["smtp"]["port"])) as server:
        server.login(config["smtp"]["username"], passencrypt.decrypt(config['smtp']['password']))
        server.sendmail(message["From"], message["To"], message.as_string())

    imap.append('Junk.Sent', message.as_string())


def run():
    global imap
    imap = IMAPClient(config['imap']['host'], use_uid=True)
    imap.login(config['imap']['username'], passencrypt.decrypt(config['imap']['password']))
    imap.select_folder(config['folders']['to_submit'])
    process_new_messages()
    while True:
        try:
            imap.idle()
            responses = imap.idle_check(timeout=600)
            for (size, message) in responses:
                if message.decode('UTF-8') == 'EXISTS' and size>0:
                    process_new_messages()
        except KeyboardInterrupt:
            break
        finally:
            imap.idle_done()
    logging.info('Terminating')
    imap.logout()


if __name__ == '__main__':
    run()