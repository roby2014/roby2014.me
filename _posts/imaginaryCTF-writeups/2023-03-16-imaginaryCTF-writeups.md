---
layout: post
title: ImaginaryCTF writeups
date: 2023-03-16 01:00 +0700
modified: 2023-03-16 01:00 +0700
description: ImaginaryCTF writeups.
tag:
  - ctf
  - misc
  - web
  - rev
  - pwn
  - forensics
image: /
---

## Table of contents
- [Table of contents](#table-of-contents)
- [Introduction](#introduction)
- [web](#web)
  - [Just Web Things (50pts)](#just-web-things-50pts)
    - [Description](#description)
    - [Attachments](#attachments)
    - [Solution](#solution)
- [rev](#rev)
- [pwn](#pwn)
- [crypto](#crypto)
- [misc](#misc)
  - [Xeger1 (75pts)](#xeger1-75pts)
    - [Description](#description-1)
    - [Attachments](#attachments-1)
    - [Solution](#solution-1)
- [forensics](#forensics)
  - [Wireshark! (50pts)](#wireshark-50pts)
    - [Description](#description-2)
    - [Attachments](#attachments-2)
    - [Solution](#solution-2)

## Introduction
Some writeups of my (dumb) solutions for [ImaginaryCTF](https://imaginaryctf.org).

## web

### Just Web Things (50pts)

#### Description
- Just a little web app I made to play with some web things. Have fun!

#### Attachments
- http://puzzler7.imaginaryctf.org:11002

#### Solution
Looking at the source code, we can see that is some sort of API written in python + flask.

```py
@app.route('/flag')
@limiter.limit("5/second")
def flag_endpoint():
    if "token" not in request.cookies:
        ret = redirect("/flag")
        ret.set_cookie("token", get_new_cookie())
        return ret
    if check_cookie(request.cookies.get("token")):
        return open("flag.txt").read()
    else:
        return "Only admins can view the flag!"
```

There is the `/flag` route, where we can see that it returns the flag if `check_cookie` returns true.

```py
def check_cookie(cookie):
    return jwt.decode(cookie, options={"verify_signature": False}, algorithms="HS256").get("user", "") == "admin"
```

And `check_cookie` returns true if the `"user"` cookie decoded is `"admin"`.
By default it sets the cookie token as `"normal"`:
```py
def get_new_cookie():
    return jwt.encode({"user": "normal"}, secret, algorithm="HS256")
```

My solution was to simple generate a JWT token [here](https://jwt.io/) as the following:
```json
{
  "user": "admin"
}
```
And manually overwrite the browser cookie so I could access `/flag` route.

<img src="./just_web_things.png" width="600">



## rev

## pwn

## crypto

## misc

### Xeger1 (75pts)

#### Description
- I've had you generating regrets to match strings before, but never the other way around - let's see how this goes.

#### Attachments
- `nc puzzler7.imaginaryctf.org 11003`
- https://imaginaryctf.org/f/oqui5#xeger1.py

#### Solution


```py
#!/usr/bin/env python3

from re import fullmatch
from time import time
from random import choice, randint

clear = '\x1b\x5b\x48\x1b\x5b\x32\x4a\x1b\x5b\x33\x4a'

def die(*args):
    print(*args)
    exit()

def gen_entity():
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    return '[' + ''.join(choice(alphabet) for i in range(randint(2, 8))) + ']'

def gen_length():
    length = randint(1, 10)
    if length == 1:
        return ""
    else:
        return f"{{{length}}}"

def gen_regex():
    length = randint(2, 5)
    return ''.join(gen_entity()+gen_length() for _ in range(length))

def puzzle(n):
    rx = gen_regex()
    print(clear, end='')
    print('='*80)
    print(f'** Regex #{n} **\n')
    print('Please generate a string to match the regex:')
    print(f'\t{rx}\n')
    inp = input("Enter string:\n>>> ")
    if fullmatch(rx, inp) is None:
        die("Input did not match!")

def main():
    solved = 0
    start = time()
    while solved < 100:
        solved += 1
        puzzle(solved)
        if time() - start > 180:
            die("Out of time!")
    die(f"Congrats! {open('flag.txt').read()}")


if __name__ == '__main__':
    main()
```

Looking at the source code, you can see that the `puzzle` function is the main point of this CTF: it generates a random regex pattern and asks user for a string, the string needs to match the pattern. In order to get the flag, you have to solve this 100 times.

My approach was to create a simple python script that connects to the server, reads the pattern, generates a string, and loop this until we can get the flag.

```py
from pwn import *

# generates string that matches [pattern] regex
def get_str_from_regex(pattern, pattern_length):
    charset = ''.join(set(re.findall(r'\[([^\]]+)\]', pattern)))
    string = ''.join(charset[1] for _ in range(pattern_length))
    return string

# returns pattern length, e.g: "[xuz]{3}"" returns 3, "[aka]" returns None
def get_length_from_pattern(pattern):
    match = re.match(r"\[([^\[\]]+)\]\{(\d+)\}", pattern)
    if not match:
        return None
    length = int(match.group(2))
    return length

# main
def main():
    server = 'puzzler7.imaginaryctf.org'
    port = 11003
    conn = remote(server, port)
    conn.recv()
    sent = 0 # sent solution strings

    # print the output message
    while True:
        str = conn.recv().decode().split("\n")
        pattern = str[4].strip() # str[4] is the regex pattern
        # split patterns so its faster
        patterns = re.findall(r"\[[^\[\]]+\](?:\{\d+\})?", pattern)
        solution = "" # for each pattern, we generate the solution string and append to this variable
        for p in patterns:
            pattern_length = get_length_from_pattern(p)
            if pattern_length == None:
                solution += p[1] # [asdf] has no {x}, so we can just input 1 char
            else:
                solution += get_str_from_regex(p, pattern_length)[0:pattern_length]

        conn.sendline(solution)
        sent += 1
        print("sent solutions = {}".format(sent))
        if sent == 100:
            conn.interactive()
        else:
            conn.recv()

if __name__ == "__main__":
    main()
```

The script should be easy to understand and follow.

<img src="./xeger1_solve.png" width="500">

## forensics

### Wireshark! (50pts)

#### Description
- Wireshark is fun!

#### Attachments
- https://imaginaryctf.org/f/iTzDw

#### Solution

Opening the `pcapng` file using Wireshark, we can follow the TCP stream and we get the following:

<img src="./tcp_stream_png.png" width="500">

It looks like a `png` image (because it starts with `.PNG` (?) idk xD), so I exported the data (using `Export Packet Bytes`) and saved as a `.png` file.

<img src="./wireshark_is_fun.png" width="500">


