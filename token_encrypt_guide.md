# Token 加密机制说明

- 用户提供的 token 均经过 AES-256-CBC 加密。
- 使用当前文件的同文件夹下的encrypt_tool.py进行加解密操作。
- 加解密密码记录在当前文件的同文件夹下的agent_encrypt_key.txt中。
- 加密后的密码记录在当前文件的同文件夹下的encrypt_token.txt中。

## encrypt_token.txt 文件格式

每组 token 两行：第一行 `# 标题说明`，第二行密文。组间空行分隔。示例：

```
# GitHub PAT - lyvoid/mystatictools
ZP1Xj5PewJt+VJ9RAtYxcsed5QHY1hmUnaj+...
```

## 解密方式

```bash
# 列出所有 token 标题
python3 encrypt_tool.py list

# 按标题关键词解密（模糊匹配）
python3 encrypt_tool.py find GitHub

# 解密 encrypt_token.txt 中第一个 token
python3 encrypt_tool.py

# 解密指定密文
python3 encrypt_tool.py "<密文>"

# 加密一个新字符串
python3 encrypt_tool.py encrypt "<明文>"
```

## 使用规则
- 使用 token 时，**先解密后使用**，不要将明文 token 记录到任何记忆文件中。
- 用户发来的新加密 token，在 `encrypt_token.txt` 中追加新组（标题行 + 密文行），不要覆盖已有 token，除非是更新同一个。
