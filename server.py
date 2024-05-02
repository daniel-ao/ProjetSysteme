# Import necessary libraries
import socket
import select
import threading
import os
import sys
from collections import defaultdict
import logging

# Setup basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Server configuration variables
SERVER_IP = '127.0.0.1'  # Listen on all network interfaces
SERVER_PORT = 2024  # Port to listen on
MAX_CONNECTIONS = 10  # Maximum number of simultaneous client connections
MODERATOR_PSEUDONYM = "Admin"


# Client management variables
clients = {}  # Dictionary to store client socket objects along with additional information
client_states = defaultdict(lambda: "active")  # Tracks the current state ('active', 'suspended', etc.) of each client

# Socket setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(MAX_CONNECTIONS)

logging.info(f"Server started on {SERVER_IP}:{SERVER_PORT}")


def get_client_by_pseudonym(pseudonym):
    """Retrieve client socket based on pseudonym."""
    for client, details in clients.items():
        if details['pseudonym'] == pseudonym:
            return client
    return None


def handle_start_game(client_socket, parts):
    """Handle the !start command to begin the game."""
    global game_active
    if not game_active:
        game_active = True
        broadcast_message("Game has started. No new players can join.")
        logging.info("Game started")
    else:
        client_socket.send(b"Game has already started.")

def handle_ban(target_client):
    """Ban a player specified by the client socket."""
    if target_client in clients:
        target_client.send("You have been banned from the game.".encode('utf-8'))
        ban_message = f"Player {clients[target_client]['pseudonym']} has been banned."
        broadcast_message(target_client, ban_message.encode('utf-8'))
        logging.info(f"{ban_message} by {clients[target_client]['pseudonym']}")
        target_client.close()
        clients.pop(target_client, None)
    else:
        logging.error("Attempted to ban a non-existent client.")

def handle_suspend(target_client):
    """Instruct the client to suspend (freeze) its input terminal."""
    if target_client in clients:
        # Send a command to the client that will be interpreted as an instruction to suspend its input process
        try:
            message = "suspend_input"  # The client will need logic to handle this command
            target_client.send(message.encode('utf-8'))
            logging.info(f"Sent suspend command to {clients[target_client]['pseudonym']}")
        except Exception as e:
            logging.error(f"Failed to send suspend command to {clients[target_client]['pseudonym']}: {str(e)}")
    else:
        logging.error("Attempted to suspend a non-existent client.")

def handle_forgive(target_client):
    """Resume a suspended client's input terminal."""
    if target_client in clients:
        try:
            message = "resume_input"  # The client should handle this command
            target_client.send(message.encode('utf-8'))
            logging.info(f"Sent resume command to {clients[target_client]['pseudonym']}")
        except Exception as e:
            logging.error(f"Failed to resume {clients[target_client]['pseudonym']}: {str(e)}")
            target_client.close()
            clients.pop(target_client, None)
    else:
        logging.error("Attempted to resume a non-existent client.")

def handle_direct_command(client_socket, parts):
    sender_pseudonym = clients[client_socket]['pseudonym']  # Retrieve sender's pseudonym
    pseudo = parts[0][1:]  # Extract the target pseudonym from the command
    '''
        @        -> error
        @NotUser -> NO user found
        @User    -> give msg
        @User msg
        @User !command
        @User !    -> error
    '''
    #If @ only without enterering a pseudonym following the @ symbol:
    if len(parts[0]) == 1:
        client_socket.send("Enter a pseudonym.".encode('utf-8'))
        return

    #If User is not admin:
    if sender_pseudonym != MODERATOR_PSEUDONYM:
        client_socket.send("Unauthorized command execution.".encode('utf-8'))
        return
    #If user is not found
    target_client = get_client_by_pseudonym(pseudo)
    if target_client is None:
        client_socket.send(f"No such user: {pseudo}".encode('utf-8'))
        return
    #If the code execution reached here, then we have an input of the form @User untill now and waitinf for an input of @User msg or @User !command
    if len(parts) == 1:
        client_socket.send("You didn't enter neither a command nor a PM.".encode('utf-8'))
    elif len(parts) == 2 or len(parts) == 3:
        #Next: If we have 3 arguments, we need to deal with them. And if we have more, we need to give an error message
        command = parts[1]
        if command == '!':
            client_socket.send("Enter a command".encode('utf-8'))
        elif command == '!ban':
            handle_ban(target_client)
        elif command == '!suspend':
            handle_suspend(target_client)
        elif command == '!forgive':
            handle_forgive(target_client)
        else:
            client_socket.send("Unknown command.".encode('utf-8'))
    
    else:
        client_socket.send("You entered an extra argument".encode('utf-8'))
            

def handle_logout(client_socket):
    """Handle the logout command."""
    logging.info(f"Client {clients[client_socket]['pseudonym']} has disconnected.")
    client_socket.send(b"Goodbye!")
    client_socket.close()
    clients.pop(client_socket, None)



def process_command(client_socket, message):
    """Process commands from a client based on the message received."""
    parts = message.decode('utf-8').strip().split()   # parts is something like ['@User', 'msg'] so it is 2D array
    command = parts[0]
    sender_pseudonym = clients[client_socket]['pseudonym']  # Retrieve sender's pseudonym

    # Check if the client is suspended
    if client_states[client_socket] == "suspended":
        if command.startswith('@') or command == "logout":
            # Suspended clients should not be able to execute commands
            client_socket.send("You are suspended and cannot execute commands.".encode('utf-8'))
            return
        else:
            # Allow suspended clients to receive messages but not send
            logging.info(f"Suspended user {sender_pseudonym} attempted to send a message.")
            return

    # Process commands or logout requests
    if command == "logout":
        handle_logout(client_socket)
    elif command.startswith('@'):
        handle_direct_command(client_socket, parts)
    else:
        logging.info("Unknown command received")

def broadcast_message(sender_socket, message):
    """Broadcast a message to all clients except the sender."""
    for client_socket in clients:
        if client_socket != sender_socket:  # Exclude the sender from receiving the message
            try:
                client_socket.send(message)  # Send message to each client
            except Exception as e:
                logging.error(f"Failed to send message to {clients[client_socket]['address'][0]}: {str(e)}")
                client_socket.close()
                clients.pop(client_socket, None)



# Main function to start the server
def start_server():
    try:
        while True:
            # Use select to handle multiple clients
            read_sockets, _, exception_sockets = select.select([server_socket] + list(clients.keys()), [], list(clients.keys()))

            for notified_socket in read_sockets:
                if notified_socket == server_socket:
                    client_socket, client_address = server_socket.accept()
                    pseudonym = client_socket.recv(1024).decode('utf-8').strip()  # Assume the first message is the pseudonym
                    if pseudonym in [clients[sock]['pseudonym'] for sock in clients]:
                        client_socket.send(b"Pseudonym already in use.")
                        client_socket.close()
                    else:
                        clients[client_socket] = {'address': client_address, 'data': [], 'pseudonym': pseudonym}
                        logging.info(f"Accepted new connection from {client_address[0]}:{client_address[1]} with pseudonym: {pseudonym}")
                else:
                    try:
                        message = notified_socket.recv(1024)
                        if message:
                            if message.startswith(b'!') or b'@' in message:   #data from the socket is in the form b'xyz'
                                process_command(notified_socket, message)
                            else:
                                # Broadcast the message to other clients
                                broadcast_message(notified_socket, message)
                                logging.debug(f"Broadcasted message from {clients[notified_socket]['address'][0]}")
                        else:
                            # No message means the client has disconnected
                            logging.info(f"Closed connection from {clients[notified_socket]['address'][0]}")
                            clients.pop(notified_socket)
                            notified_socket.close()
                    except Exception as e:
                        logging.error(f"Error handling message from {clients[notified_socket]['address'][0]}: {str(e)}")
                        clients.pop(notified_socket)
                        notified_socket.close()

            for notified_socket in exception_sockets:
                # Safely handle client disconnection and remove them from the client list
                if notified_socket in clients:
                    logging.error(f"Handling exception for {clients[notified_socket]['address'][0]}")
                    clients.pop(notified_socket)
                    notified_socket.close()
                
    except KeyboardInterrupt:
        logging.info("Server shutting down...")
        for client_socket in clients:
            client_socket.close()
        server_socket.close()


if __name__ == "__main__":
    start_server()