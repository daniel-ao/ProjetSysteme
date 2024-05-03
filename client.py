import socket
import select
import os
import sys
import threading
import logging
import time
logging.basicConfig(filename='client.log', filemode='a', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def create_socket():
    """Create and return a new socket."""
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connect_to_server(sock, server_ip, server_port, pseudonym):
    """Connect to the server, send pseudonym, and handle the connection."""
    try:
        sock.connect((server_ip, int(server_port)))
        print(f"Connected to the server at {server_ip}:{server_port}.")
        sock.send(pseudonym.encode('utf-8'))  # Send the pseudonym right after connecting
    except Exception as e:
        print(f"Failed to connect to the server at {server_ip}:{server_port}: {e}")
        sys.exit()
    

'''def send_message(sock, message):
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
            sys.exit("Disconnected due to an error. Please restart the client.")'''



#-------------------------------------------------#

def clear_line():
    """Clear the current line in the terminal."""
    sys.stdout.write('\r')
    sys.stdout.write('\033[K')  # ANSI escape sequence to clear the line


def receive_messages(sock,run_flag):
    """Continuously listen for messages from the server using a non-blocking socket."""
    sock.setblocking(0)  # Set socket to non-blocking mode

    try:
        while run_flag['active']:
            try:
                message = sock.recv(1024)
                if message:
                    clear_line()  # Clear the input line before showing the new message
                    print(message.decode('utf-8'))
                    sys.stdout.write("Enter your message or command: ")
                    sys.stdout.flush()  # Make sure the prompt is displayed
                else:
                    # No more data from server
                    print("Server has disconnected.")
                    break
            except BlockingIOError:
                # No data available, yield control to allow typing or other operations
                continue
            except socket.error as e:
                if run_flag['active']:
                    print(f"Socket error: {e}")
                    break
            except Exception as e:
                if run_flag['active']:
                    print(f"Unexpected error: {e}")
                    break
    finally:
        print("Cleaning up connection...")
        sock.close()
        print("You are now disconnected. Please close the terminal manually or press Enter to exit.")
        input()  # Wait for the user to press Enter





'''def handle_user_input(sock):
    """Handle user input without blocking the display of incoming messages."""
    while True:
        sys.stdout.write("Enter your message or command: ")
        sys.stdout.flush()
        message = input()
        if message.lower() == 'quit':
            send_message(sock, "logout")
            break
        send_message(sock, message)'''



def main():
    server_ip = "127.0.0.1"
    server_port = 2024

    # Get the pseudonym before creating the socket
    pseudonym = input("Enter your pseudonym: ")
    while not pseudonym.strip():
        print("Pseudonym cannot be empty. Please enter a valid pseudonym.")
        pseudonym = input("Enter your pseudonym: ")

    # Create a socket and connect to the server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))
    print(f"Connected to {server_ip} on port {server_port}")
    sock.send(pseudonym.encode('utf-8'))  # Send pseudonym immediately after connecting

    run_flag = {'active': True}
    receiver_thread = threading.Thread(target=receive_messages, args=(sock, run_flag))
    receiver_thread.start()

    try:
        while True:
            message = input("Enter your message or command: ")
            if message.lower() == 'quit':
                logging.info("User has quit.")
                run_flag['active'] = False
                sock.send("logout".encode('utf-8'))  # Optionally send a logout message to the server
                break
            sock.send(message.encode('utf-8'))
    except KeyboardInterrupt:
        print("Interrupted by user.")
        logging.info("Interrupted by user.")
        run_flag['active'] = False
    finally:
        run_flag['active'] = False
        receiver_thread.join()  # Ensure the receiver thread has finished
        sock.close()
        print("Disconnected.")


if __name__ == "__main__":
    main()

#-------------------------------------------------#
