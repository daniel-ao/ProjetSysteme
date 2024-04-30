import socket
import select
import sys
import threading


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
    except Exception as e:
        print(f"Error sending message: {e}")
        if sock:
            sock.close()
        sys.exit()


def receive_messages(sock):
    """Continuously listen for messages from the server."""
    try:
        while True:
            message = sock.recv(1024)
            if message:
                print("Received:", message.decode('utf-8'))
            else:
                # Server has likely closed the connection
                print("Server has disconnected.")
                sock.close()
                break
    except Exception as e:
        print(f"Lost connection to the server: {e}")
        sock.close()


def handle_user_input(sock):
    """Handle user input to send messages to the server."""
    while True:
        message = input("Enter your message or command: ")
        if message.lower() == 'quit':
            send_message(sock, "logout")  # Notify server of the intention to disconnect
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