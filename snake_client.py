"""
CS 3357A
ASSIGNMENT 4
SAMUEL GEBRETSION
251173970
"""
import random
import threading

import pygame
import socket
import rsa

# Initialize settings and constants
DEBUG_MODE = True
HOST = "localhost"
PORT = 5555
WINDOW_WIDTH, WINDOW_HEIGHT = 400, 400
COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "grid": (200, 200, 200)
}

# Initialize Pygame
pygame.init()
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Server-driven Snake Game")

def draw_grid():
    for x in range(0, WINDOW_WIDTH, 20):
        pygame.draw.line(window, COLORS['grid'], (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, 20):
        pygame.draw.line(window, COLORS['grid'], (0, y), (WINDOW_WIDTH, y))


def draw_snake_eyes(x, y):
    # Calculating the positions for the snake's eyes
    left_eye_pos = (x * 20 + 5, y * 20 + 5)
    right_eye_pos = (x * 20 + 15, y * 20 + 5)

    # Drawing the eyes
    pygame.draw.circle(window, COLORS['black'], left_eye_pos, 3)
    pygame.draw.circle(window, COLORS['black'], right_eye_pos, 3)


def draw_game(state):
    window.fill(COLORS['black'])

    game_data = state.split("|")
    if len(game_data) < 2:  # Handling unexpected game state format
        return

    snake_positions, snack_positions = game_data
    snake_positions = snake_positions.split("*") if snake_positions else []
    snack_positions = snack_positions.split("*") if snack_positions else []

    # Drawing snakes
    for i, position in enumerate(snake_positions):
        if position:  # Checking if the position string is not empty
            x, y = map(int, position.strip("()").split(", "))
            pygame.draw.rect(window, random.choice(['red', 'yellow', 'green', 'blue']), (x * 20, y * 20, 20, 20))

            # Drawing eyes for the snake's head (first segment)
            if i == 0:  # The first segment is the head
                draw_snake_eyes(x, y)

    # Drawing snacks
    for position in snack_positions:
        if position:  # Checking if the position string is not empty
            x, y = map(int, position.strip("()").split(", "))
            pygame.draw.rect(window, COLORS['green'], (x * 20, y * 20, 20, 20))

    draw_grid()
    pygame.display.update()


def receive_msg(conn, client_private_key):
    while True:
        msg = conn.recv(500)
        try:
            msg = conn.recv(500)
            if not msg:
                break  # Exit the loop if no data is received
            else:
                decrypted_msg = rsa.decrypt(msg, client_private_key).decode()
                print(decrypted_msg)
        except:
            # Draw the game if decryption is successful
            draw_game(msg.decode())



def run_snake(client_socket, server_public_key):
    clock = pygame.time.Clock()

    while True:
        clock.tick(10)  # Frame rate
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                command = 'quit'
                pygame.quit()
            keys = pygame.key.get_pressed()
            command = "get"  # Default command

            if keys[pygame.K_UP]:
                command = "up"
            elif keys[pygame.K_DOWN]:
                command = "down"
            elif keys[pygame.K_LEFT]:
                command = "left"
            elif keys[pygame.K_RIGHT]:
                command = "right"
            elif keys[pygame.K_r]:
                command = "reset"
            elif keys[pygame.K_q]:
                command = "quit"
            elif keys[pygame.K_a]:
                command = "Hello!"
            elif keys[pygame.K_s]:
                command = "Good Game!"
            elif keys[pygame.K_d]:
                command = "Bye!"

        client_socket.send(rsa.encrypt(command.encode(), server_public_key))


if __name__ == "__main__":
    # Establish connection to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    client_public_key, client_private_key = rsa.newkeys(512)
    print(client_public_key.e, client_public_key.n)
    client_socket.send(str(client_public_key.n).encode())
    client_socket.send(str(client_public_key.e).encode())
    server_n_data = client_socket.recv(1024)
    server_e_data = client_socket.recv(1024)

    try:
        server_n = int(server_n_data.decode())
    except Exception as e:
        print(f"Error decoding server_e: {e}")
    try:
        server_e = int(server_e_data.decode())
    except Exception as e:
        print(f"Error decoding server_e: {e}")
    server_public_key = rsa.PublicKey(server_n, server_e)

    threading.Thread(target=receive_msg, args=(client_socket, client_private_key), daemon=True).start()
    run_snake(client_socket, server_public_key)
