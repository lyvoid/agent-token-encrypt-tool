#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符串加密/解密工具
使用 AES-256-CBC 进行对称加密，通过 PBKDF2 从密码派生密钥。
依赖: pip install cryptography

使用方式:
  解密 token（默认读取 encrypt_token.txt 中第一个 token）:
    python3 encrypt_tool.py

  列出 encrypt_token.txt 中所有 token 标题:
    python3 encrypt_tool.py list

  按标题关键词解密（模糊匹配）:
    python3 encrypt_tool.py find <关键词>

  解密指定密文:
    python3 encrypt_tool.py <密文>

  加密字符串:
    python3 encrypt_tool.py encrypt <明文>

encrypt_token.txt 格式:
  每组 token 由两行组成：第一行以 # 开头为标题，第二行为密文。
  组之间用空行分隔。
"""

import base64
import os
import sys

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# 内置密码（主人指定的统一密码）
DEFAULT_PASSWORD = "******"

# 同目录下的 token 文件
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "encrypt_token.txt")


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend(),
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt(plaintext: str, password: str = DEFAULT_PASSWORD) -> str:
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


def decrypt(encrypted_text: str, password: str = DEFAULT_PASSWORD) -> str:
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


def parse_token_file():
    """
    解析 encrypt_token.txt，返回 [(title, ciphertext), ...] 列表。
    格式：# 标题行 + 密文行，组间空行分隔。
    """
    if not os.path.exists(TOKEN_FILE):
        print(f"错误: 找不到 token 文件 {TOKEN_FILE}", file=sys.stderr)
        sys.exit(1)
    with open(TOKEN_FILE, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    tokens = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            # 寻找下一个非空行作为密文
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip() and not lines[j].strip().startswith("#"):
                tokens.append((title, lines[j].strip()))
                i = j + 1
            else:
                i = j
        else:
            i += 1
    return tokens


def read_token_file():
    """读取 encrypt_token.txt 中第一个 token 的密文"""
    tokens = parse_token_file()
    if not tokens:
        print(f"错误: {TOKEN_FILE} 中没有找到有效的 token", file=sys.stderr)
        sys.exit(1)
    return tokens[0][1]


def list_tokens():
    """列出所有 token 标题"""
    tokens = parse_token_file()
    if not tokens:
        print("（暂无 token）")
        return
    for idx, (title, _) in enumerate(tokens, 1):
        print(f"  {idx}. {title}")


def find_token(keyword: str):
    """按标题关键词模糊匹配，返回密文"""
    tokens = parse_token_file()
    matched = [(t, c) for t, c in tokens if keyword.lower() in t.lower()]
    if not matched:
        print(f"错误: 没有找到标题包含 '{keyword}' 的 token", file=sys.stderr)
        sys.exit(1)
    if len(matched) > 1:
        print(f"找到多个匹配的 token，请用更精确的关键词：")
        for t, _ in matched:
            print(f"  - {t}")
        sys.exit(1)
    return matched[0][1]


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        # 无参数：解密第一个 token
        print(decrypt(read_token_file()))
    elif args[0] == "list":
        list_tokens()
    elif args[0] == "find" and len(args) >= 2:
        print(decrypt(find_token(args[1])))
    elif len(args) == 1 and not args[0].startswith("#"):
        # 单参数：尝试解密给定密文
        print(decrypt(args[0]))
    elif args[0] == "encrypt" and len(args) >= 2:
        print(encrypt(args[1]))
    else:
        print("用法:")
        print("  python3 encrypt_tool.py              # 解密第一个 token")
        print("  python3 encrypt_tool.py list          # 列出所有 token 标题")
        print("  python3 encrypt_tool.py find <关键词>  # 按标题关键词解密")
        print("  python3 encrypt_tool.py <密文>        # 解密指定密文")
        print("  python3 encrypt_tool.py encrypt <明文> # 加密字符串")
        sys.exit(1)
