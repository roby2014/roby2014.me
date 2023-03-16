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
        patterns = re.findall(r"\[[^\[\]]+\](?:\{\d+\})?", pattern)
        solution = ""
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
