#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os.path
from cryptography.fernet import Fernet
from getpass import getpass


def get_key() -> bytes:
    key_file = 'config.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            key = f.read()
            return key
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key


def encrypt(password: str) -> str:
    key = get_key()
    encrypted = Fernet(key).encrypt(password.encode('UTF-8'))
    return encrypted.decode('UTF-8')


def decrypt(encrypted: str):
    key = get_key()
    return Fernet(key).decrypt(encrypted).decode('UTF-8')


if __name__ == '__main__':
    password = getpass()
    print(encrypt(password))
