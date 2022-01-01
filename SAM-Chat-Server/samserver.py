import socket
import threading
import logging
import sys
import random

# logging setup
root = logging.getLogger("SAM-Server")
root.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


class User:
    def __init__(self, client):
        self.client = client
        self.username = None
        self.userid = None
        self.ip_address = None

    def receive_messages(self):
        while server_running:
            msg = receive_data(self)
            if not msg:
                break
            else:
                send_to_all(msg, self, True)
        self.remove()

    def remove(self):
        self.client.close()
        users.remove(self)
        send_to_all(f"{self.username} has left the chat", self, False)


ip = ""
port = 25469

if "dev" in sys.argv:
    ip = "127.0.0.1"

server_running = True
users = []

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_root = None
root.debug("Initialized socket")


def assign_id():
    userid = random.randint(100, 999)
    for user in users:
        if user.userid == userid:
            assign_id()
    return userid


def receive_data(user: User):
    try:
        bufflen = int.from_bytes(user.client.recv(4), "little")
        data = user.client.recv(bufflen).decode("utf-8")
        return data
    except socket.error as e:
        root.error(e)


def send_to_all(msg, user: User, send_username: bool):
    if send_username:
        msg = f"{user.username}: " + msg
    root.info(f"({user.userid} | {user.ip_address}) {msg}")
    encoded_message = len(msg).to_bytes(4, "little") + msg.encode("utf-8")
    for user in users:
        user.client.send(encoded_message)


def add_client(client: socket.socket, address):
    user = User(client)
    user.userid = assign_id()
    user.ip_address = address[0]
    root.debug(f"Assigned new userid for new connection: {user.userid}")
    root.debug(f"({user.userid} | {user.ip_address}) Waiting for username to be sent")
    username = receive_data(user)
    root.debug(f"({user.userid} | {user.ip_address}) Received username {username}")
    if username:
        user.username = username
        users.append(user)
        root.debug(f"({user.userid} | {user.ip_address}) Added user to current connections")
        send_to_all(f"{username} has connected to the chat", user, False)
        user.receive_messages()


def connection_listener():
    sock.listen()
    root.debug("Listening for connections")

    while server_running:
        conn, addr = sock.accept()
        root.info(f"New connection from {addr[0]}")
        threading.Thread(target=lambda: add_client(conn, addr), daemon=True).start()


try:
    sock.bind((ip, port))
    if ip == "":
        ip = "every network interface"
    root.debug(f"Binded socket to {ip} on port {port}")
    root.debug("Creating server root user")
    server_root = User(None)
    server_root.username = "Server"
    server_root.userid = 0
    server_root.ip_address = "sus.sus.sus.sus"

    connection_listener()
except socket.error as e:
    root.error(e)
