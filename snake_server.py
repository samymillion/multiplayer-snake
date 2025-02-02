import numpy as np
import socket
from _thread import *
import pickle
from snake import SnakeGame
import uuid
import time
import rsa
import threading

# server = "10.11.250.207"
server = "localhost"
port = 5555
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

counter = 0
rows = 20

clients = []

try:
    s.bind((server, port))
except socket.error as e:
    str(e)

s.listen(5)
# s.settimeout(0.5)
print("Waiting for a connection, Server Started")

game = SnakeGame(rows)
game_state = ""
last_move_timestamp = time.time()
interval = 0.2
moves_queue = set()

timestamp_lock = threading.Lock()
def game_thread():
    global game, moves_queue, game_state, last_move_timestamp
    while True:
        with timestamp_lock:
            last_move_timestamp = time.time()
        game.move(moves_queue)
        moves_queue = set()
        game_state = game.get_state()
        while time.time() - last_move_timestamp < interval:
            time.sleep(0.1)


rgb_colors = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "orange": (255, 165, 0),
}
rgb_colors_list = list(rgb_colors.values())


def main():
    global counter, game, server_n, server_e
    start_new_thread(game_thread, ())

    while True:
        conn, addr = s.accept()
        print("Connected to:", addr)

        server_public_key, server_private_key = rsa.newkeys(512)
        print(server_public_key.e, server_private_key.n)
        client_n_data = conn.recv(1024)
        client_e_data = conn.recv(1024)

        try:
            client_n = int(client_n_data.decode())
        except Exception as e:
            print(f"Error decoding server_e: {e}")
        try:
            client_e = int(client_e_data.decode())
        except Exception as e:
            print(f"Error decoding server_e: {e}")

        client_public_key = rsa.PublicKey(client_n, client_e)
        conn.send(str(server_public_key.n).encode())
        conn.send(str(server_public_key.e).encode())

        clients.append((conn, client_public_key))

        threading.Thread(target=run_game, args=(conn, client_public_key, server_private_key), daemon=True).start()


def run_game(conn, client_public_key, server_private_key):
    unique_id = str(uuid.uuid4())
    color = rgb_colors_list[np.random.randint(0, len(rgb_colors_list))]
    game.add_player(unique_id, color=color)

    while True:
        data = rsa.decrypt(conn.recv(500), server_private_key).decode()
        conn.send(game_state.encode())
        move = None
        if not data:
            print("no data received from client")
            break
        elif data == "get":
            print("received get")
            pass
        elif data == "quit":
            print("received quit")
            game.remove_player(unique_id)
            clients.remove((conn, client_public_key))
            break
        elif data == "reset":
            game.reset_player(unique_id)
        elif data in ["up", "down", "left", "right"]:
            move = data
            moves_queue.add((unique_id, move))
        elif data in ["Hello!", "Good Game!", "Bye!"]:
            msg = ("User" + unique_id + ": " + data)
            for i in clients:
                i[0].send(rsa.encrypt(msg.encode(), i[1]))
        else:
            print("Invalid data received from client:", data)

    conn.close()


if __name__ == "__main__":
    main()
