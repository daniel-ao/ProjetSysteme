import socket
import select
import os
import sys
import threading
import logging
logging.basicConfig(filename='client.log', filemode='a', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def connect_to_server(server_ip, server_port):
    """Connect to the server and handle the connection."""
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, int(server_port)))
        print(f"Connected to the server at {server_ip}:{server_port}.")

        # Prompt for pseudonym
        pseudonym = input("Enter your pseudonym: ")
        while not pseudonym.strip():
            print("Pseudonym cannot be empty. Please enter a valid pseudonym.")
            pseudonym = input("Enter your pseudonym: ")
        client_socket.send(pseudonym.encode('utf-8'))

        return client_socket
    except Exception as e:
        print(f"Failed to connect to the server at {server_ip}:{server_port}: {e}")
        sys.exit()
    

def send_message(sock, message):
    """Send a message to the server."""
    try:
        sock.send(message.encode('utf-8'))
    except socket.error as e:
        print(f"Socket error: {e}")
        logging.error(f"Socket error while sending message: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.error(f"Unexpected error while sending message: {e}")
    finally:
        if 'e' in locals():  # Check if an exception was caught
            sock.close()
            sys.exit("Disconnected due to an error. Please restart the client.")



def clear_line():
    """Clear the current line in the terminal."""
    sys.stdout.write('\r')
    sys.stdout.write('\033[K')  # ANSI escape sequence to clear the line


def receive_messages(sock):
    """Continuously listen for messages from the server."""
    try:
        while True:
            message = sock.recv(1024)
            if message:
                clear_line()  # Clear the input line before showing the new message
                print("Received:", message.decode('utf-8'))
                sys.stdout.write("Enter your message or command: ")
                sys.stdout.flush()  # Make sure the prompt is displayed
            else:
                # Server has likely closed the connection
                raise ConnectionAbortedError("Server has disconnected.")
    except ConnectionAbortedError as e:
        print(e)
        logging.error(f"Connection aborted: {e}")
    except socket.error as e:
        print(f"Socket error: {e}")
        logging.error(f"Socket error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        logging.error(f"Unexpected error during message reception: {e}")
    finally:
        sock.close()
        sys.exit("Disconnected. Please restart the client.")



def handle_user_input(sock):
    """Handle user input without blocking the display of incoming messages."""
    while True:
        sys.stdout.write("Enter your message or command: ")
        sys.stdout.flush()
        message = input()
        if message.lower() == 'quit':
            send_message(sock, "logout")
            break
        send_message(sock, message)



if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python chat_killer_client.py <server_ip> <server_port>")
        sys.exit()

    server_ip = sys.argv[1]
    server_port = sys.argv[2]
    
    sock = connect_to_server(server_ip, server_port)
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()
    handle_user_input(sock)