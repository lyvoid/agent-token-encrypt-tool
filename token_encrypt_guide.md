# Token 加密机制说明

主人提供的 token 均经过 AES-256-CBC 加密。

## 文件结构

```
agent-token-encrypt-tool/
├── encrypt_tool.py          # 加解密工具
├── secret.key               # 加密密码（一行明文，用于派生 AES 密钥）
├── token_encrypt_guide.md   # 本说明
└── keys/                    # 每个 token 一个文件
```

## keys/ 下 token 文件格式

每个 token 一个 `.txt` 文件，文件名符合 token 用途。内容两行：首行 `//` 注释为标题说明，第二行为密文。示例：

```
// GitHub PAT - lyvoid/mystatictools
ZP1Xj5PewJt+VJ9RAtYxcsed5QHY1hmUnaj+...
```

## 解密方式

```bash
# 列出所有 token 标题
python3 lyhome/other/agent-token-encrypt-tool/encrypt_tool.py list

# 按标题/文件名关键词解密（模糊匹配）
python3 lyhome/other/agent-token-encrypt-tool/encrypt_tool.py find GitHub

# 解密 keys/ 下第一个 token
python3 lyhome/other/agent-token-encrypt-tool/encrypt_tool.py

# 解密指定 token 文件
python3 lyhome/other/agent-token-encrypt-tool/encrypt_tool.py decrypt github_pat_mystatictools.txt

# 解密指定密文
python3 lyhome/other/agent-token-encrypt-tool/encrypt_tool.py "<密文>"

# 加密一个新字符串
python3 lyhome/other/agent-token-encrypt-tool/encrypt_tool.py encrypt "<明文>"
```

## 使用规则

- 使用 token 时，**先解密后使用**，不要将明文 token 记录到任何记忆文件中。
- 主人发来的新加密 token，在 `keys/` 下新建文件（`//` 标题行 + 密文行），文件名按用途命名，不要覆盖已有 token，除非是更新同一个。
