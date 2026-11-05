#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符串加密/解密工具
使用 AES-256-CBC 进行对称加密，通过 PBKDF2 从密码派生密钥。
依赖: pip install cryptography

使用方式:
  解密 keys/ 下第一个 token:
    python3 encrypt_tool.py

  列出 keys/ 下所有 token 标题:
    python3 encrypt_tool.py list

  按标题/文件名关键词解密（模糊匹配）:
    python3 encrypt_tool.py find <关键词>

  解密 keys/ 下指定文件:
    python3 encrypt_tool.py decrypt <文件名或标题关键词>

  解密指定密文:
    python3 encrypt_tool.py <密文>

  加密字符串:
    python3 encrypt_tool.py encrypt <明文>

文件说明:
  secret.key        加密密码（一行明文，用于派生 AES 密钥）
  keys/<name>.txt   每个 token 一个文件：第一行 "// 标题说明"，第二行为密文。
"""

import base64
import os
import sys

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(BASE_DIR, "secret.key")
KEYS_DIR = os.path.join(BASE_DIR, "keys")


def load_password() -> str:
    """从 secret.key 读取加密密码"""
    if not os.path.exists(KEY_FILE):
        print(f"错误: 找不到密钥文件 {KEY_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        password = f.read().strip()
    if not password:
        print(f"错误: {KEY_FILE} 为空", file=sys.stderr)
        sys.exit(1)
    return password


PASSWORD = load_password()


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt(plaintext: str, password: str = PASSWORD) -> str:
    salt = os.urandom(16)
    iv = os.urandom(16)
    key = derive_key(password, salt)

    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    combined = salt + iv + ciphertext
    return base64.b64encode(combined).decode("utf-8")


def decrypt(encrypted_text: str, password: str = PASSWORD) -> str:
    combined = base64.b64decode(encrypted_text)

    salt = combined[:16]
    iv = combined[16:32]
    ciphertext = combined[32:]

    key = derive_key(password, salt)

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(padded_data) + unpadder.finalize()

    return plaintext.decode("utf-8")


def parse_key_file(path: str):
    """解析单个 key 文件，返回 (title, ciphertext)。首行 // 注释为标题，下一行为密文。"""
    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    title = os.path.splitext(os.path.basename(path))[0]
    ciphertext = ""
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("//"):
            title = s.lstrip("/").strip()
        elif s and not s.startswith("#"):
            ciphertext = s
            break
    return title, ciphertext


def parse_keys_dir():
    """扫描 keys/ 目录，返回 [(filename, title, ciphertext), ...] 按文件名排序。"""
    if not os.path.isdir(KEYS_DIR):
        print(f"错误: 找不到 token 目录 {KEYS_DIR}", file=sys.stderr)
        sys.exit(1)
    keys = []
    for name in sorted(os.listdir(KEYS_DIR)):
        if not name.endswith(".txt"):
            continue
        path = os.path.join(KEYS_DIR, name)
        if os.path.isfile(path):
            title, ciphertext = parse_key_file(path)
            if ciphertext:
                keys.append((name, title, ciphertext))
    return keys


def read_first_token():
    """读取 keys/ 下第一个 token 的密文"""
    keys = parse_keys_dir()
    if not keys:
        print(f"错误: {KEYS_DIR} 中没有找到有效的 token 文件", file=sys.stderr)
        sys.exit(1)
    return keys[0][2]


def list_tokens():
    """列出所有 token 标题"""
    keys = parse_keys_dir()
    if not keys:
        print("（暂无 token）")
        return
    for idx, (name, title, _) in enumerate(keys, 1):
        print(f"  {idx}. {title}  ({name})")


def find_token(keyword: str):
    """按标题/文件名关键词模糊匹配，返回密文"""
    keys = parse_keys_dir()
    matched = [
        (name, title, c)
        for name, title, c in keys
        if keyword.lower() in title.lower() or keyword.lower() in name.lower()
    ]
    if not matched:
        print(f"错误: 没有找到包含 '{keyword}' 的 token", file=sys.stderr)
        sys.exit(1)
    if len(matched) > 1:
        print("找到多个匹配的 token，请用更精确的关键词：")
        for name, title, _ in matched:
            print(f"  - {title}  ({name})")
        sys.exit(1)
    return matched[0][2]


def decrypt_file(keyword: str):
    """按文件名或标题关键词找到 keys/ 下的文件并解密"""
    return decrypt(find_token(keyword))


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        # 无参数：解密第一个 token
        print(decrypt(read_first_token()))
    elif args[0] == "list":
        list_tokens()
    elif args[0] == "find" and len(args) >= 2:
        print(decrypt(find_token(args[1])))
    elif args[0] == "decrypt" and len(args) >= 2:
        print(decrypt_file(args[1]))
    elif args[0] == "encrypt" and len(args) >= 2:
        print(encrypt(args[1]))
    elif len(args) == 1 and not args[0].startswith("#"):
        # 单参数：尝试解密给定密文
        print(decrypt(args[0]))
    else:
        print("用法:")
        print("  python3 encrypt_tool.py                # 解密 keys/ 下第一个 token")
        print("  python3 encrypt_tool.py list            # 列出所有 token 标题")
        print("  python3 encrypt_tool.py find <关键词>    # 按标题/文件名关键词解密")
        print("  python3 encrypt_tool.py decrypt <关键词> # 解密指定 token 文件")
        print("  python3 encrypt_tool.py <密文>           # 解密指定密文")
        print("  python3 encrypt_tool.py encrypt <明文>   # 加密字符串")
        sys.exit(1)
