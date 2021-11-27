#!/usr/bin/python3
import socket
import time
import re
import random


# https://stackoverflow.com/a/17697651/13197635
def recvall(sock):
    BUFF_SIZE = 4096  # 4 KiB
    data = b''
    while True:
        part = sock.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            # either 0 or end of data
            break
    return data


killerPorts = []
daniel = ""
pid = -1


def findKillers(secs=10):
    global killerPorts
    global daniel
    global pid
    print("Finding killer ports ({}s)...".format(secs))
    try:
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.settimeout(1.0)
        s2.connect(("mpg-r2.hitcon.org", 29272))
        time.sleep(secs)
        msg = recvall(s2).decode().split("\n")
    except Exception:
        return
    for i in range(len(msg)):
        line = msg[i]
        if "SYSTEM: Process " in line:
            continue

        if "daniellin" in line:
            if i + 1 != len(msg) and ("You need to cool down." in msg[i + 1] or "Too bad! Door is closed!" in msg[i + 1]):
                continue
            killerPorts = [x for x in killerPorts if x != daniel]
            daniel = line.split("grep -v ")[-1].split(" | ")[0]
            killerPorts.append(daniel)
            print(line)
            print("daniellin fingerprint: " + daniel)
            print()
        elif "Process Created: PID=" in line and "HUP TERM INT" in line:
            if i + 1 != len(msg) and ("You need to cool down." in msg[i + 1] or "Too bad! Door is closed!" in msg[i + 1]):
                continue
            killerPorts = [x for x in killerPorts if x != pid]
            pid = line.split("Process Created: PID=")[-1].split(" ")[0]
            killerPorts.append(pid)
            print(line)
            print("Dans PID: " + daniel)
            print()
        elif "kill" in line:
            if "#" in line:
                line = "".join(line.split("#")[:-1])
            for killerPort in [s for s in re.findall(r'\b\d+\b', line) if int(s) >= 30000 and int(s) < 40000]:
                if killerPort not in killerPorts:
                    killerPorts.append(killerPort)
                    print(line)
                    print("Found " + killerPort)
                    print()
    random.shuffle(killerPorts)
    print(killerPorts)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(1.0)
s.connect(("mpg-r2.hitcon.org", 29271))
s.send(b"Nick NyanCat2021 [REDACTED]\n")
print(recvall(s).decode())

curTime = 0
prevScore = 0

while True:
    findKillers(2)

    while True:
        try:
            s.send(b"CurrentGame\n")
            stats = recvall(s).decode().split("\n")
            status = stats[1].split(": ")[-1]
        except Exception:
            status = "WTF"

        if status == "GAME_RUNNING":
            try:
                if killerPorts == []:
                    findKillers()

                findKillers(0.5)
                s.send(b"PlayerInfo\n")
                recvall(s)
            except Exception:
                pass
            break
        else:
            if "GAME_STARTING" in status:
                killerPorts = []
            print("Game is not running...")

        time.sleep(0.1)

    while True:
        try:
            s.send(b"PlayerInfo\n")
            port = recvall(s).decode().split("=")[-1][:-1].strip()
            break
        except Exception:
            findKillers(0.5)
            continue

    findKillers(0.5)

    cmd1 = """Cmd socat -lf/tmp/{1} TCP-LISTEN:{0} -\n""".format(port, "".join(killerPorts))
    print(cmd1)
    s.send(cmd1.encode())

    try:
        recvall(s)
    except socket.timeout:
        break
