# Import necessary libraries
import socket
import select
import os
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
game_active = False # Flag to indicate if the game has started

# Socket setup
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen(MAX_CONNECTIONS)

logging.info(f"Server started on {SERVER_IP} : {SERVER_PORT}.")

#-------------------------------------------------#


def get_client_by_pseudonym(pseudonym):
    """Retrieve client socket based on pseudonym."""
    for client, details in clients.items():
        if details['pseudonym'] == pseudonym:
            return client
    return None


#-------------------------------------------------#

def handle_start_game():
    """Handle the !start command to begin the game."""
    global game_active
    logging.info("Received a request to start the game.")
    if game_active == False:
        game_active = True
        broadcast_message_to_all("Game has started. No new players can join.")
        logging.info("Game started!")
    else:
        broadcast_message_to_all("Game has already started.")
        logging.info("Attempt to start an already active game.")

def handle_ban(target_client):
    """Ban a player specified by the client socket."""
    if target_client in clients:
        target_client.send("You have been banned from the game.".encode('utf-8'))
        ban_message = f"Player {clients[target_client]['pseudonym']} has been banned"
        broadcast_message(target_client, ban_message.encode('utf-8'))
        logging.info(f"{ban_message} by Admin")
        target_client.close()
        clients.pop(target_client, None)
    else:
        logging.error("Attempted to ban a non-existent client.")

def handle_suspend(client_socket):
    if client_socket in clients:
        try:
            clients[client_socket]['state'] = 'suspended'
            client_states[client_socket] = 'suspended'  # Update the state in the dictionary
            client_socket.send("You have been suspended.".encode('utf-8'))
            logging.info(f"{clients[client_socket]['pseudonym']} has been suspended.")
        except Exception as e:
            logging.error("Failed to suspend client: " + str(e))

def handle_forgive(client_socket):
    if client_socket in clients:
        try:
            clients[client_socket]['state'] = 'active'
            client_states[client_socket] = 'active'  # Update the state back to active
            client_socket.send("You have been forgiven and can participate again.".encode('utf-8'))
            logging.info(f"{clients[client_socket]['pseudonym']} has been forgiven.")
        except Exception as e:
            logging.error("Failed to lift suspension: " + str(e))

def handle_list_command(client_socket):
    """Handle the !list command to display the status of all clients."""
    status_message = "Current clients:\n"
    for client, details in clients.items():
        pseudonym = details['pseudonym']
        state = client_states[client]
        status_message += f"{pseudonym} - {state}\n"
    client_socket.send(status_message.encode('utf-8'))
    #client_socket.send(f"Active clients: {', '.join([clients[sock]['pseudonym'] for sock in clients])}".encode('utf-8'))

def handle_direct_command(client_socket, parts):
    sender_pseudonym = clients[client_socket]['pseudonym']  # Retrieve sender's pseudonym
    # Start by identifying if the message is a private message or a command.
    recipients = []
    message = []
    command_flag = False
    if len(parts[0]) == 1:
        client_socket.send("Enter a pseudonym.".encode('utf-8'))
        return
    for part in parts:
        if part.startswith('!') and len(message) == 0:  # command detected
            command_flag = True
            break
        elif part.startswith('@'):
            recipients.append(part[1:])
        else:
            message.append(part)

    if not recipients:
        client_socket.send("Enter a valid pseudonym after '@'.".encode('utf-8'))
        return

    if command_flag:
        # This is a command to a specific user.
        if sender_pseudonym != MODERATOR_PSEUDONYM:
            client_socket.send("Unauthorized command execution.".encode('utf-8'))
            return
        target_client = get_client_by_pseudonym(recipients[0])  # Assuming command to first user only
        if target_client is None:
            client_socket.send(f"No such user: {recipients[0]}".encode('utf-8'))
            return

        command = parts[1]
        if command == '!ban':
            handle_ban(target_client)
        elif command == '!suspend':
            handle_suspend(target_client)
        elif command == '!forgive':
            handle_forgive(target_client)
        else:
            client_socket.send("Unknown command.".encode('utf-8'))
    else:
        # Handling private message to one or more users including Moderator
        if len(message) == 0:
            client_socket.send("You didn't enter a message.".encode('utf-8'))
            return

        final_message = f"PM from {sender_pseudonym}: {' '.join(message)}"
        # Send message to all recipients and Moderator (if not already included)
        recipients.append(MODERATOR_PSEUDONYM)  # Ensure moderator gets the PM
        recipients = set(recipients)  # Remove duplicates
        for recipient in recipients:
            target_client = get_client_by_pseudonym(recipient)
            if target_client:
                target_client.send(final_message.encode('utf-8'))
            elif recipient != MODERATOR_PSEUDONYM:
                client_socket.send(f"No such user: {recipient}".encode('utf-8'))
            #else:
            #   client_socket.send(f"No such user: {recipient}".encode('utf-8'))
            
def handle_logout(client_socket):
    """Handle the logout command."""
    logging.info(f"Client {clients[client_socket]['pseudonym']} has disconnected.")
    client_socket.send(b"Goodbye!")
    client_socket.close()
    clients.pop(client_socket, None)

def handle_shutodwn():
    logging.info("Server is shutting down on admin command.")
    for client_socket in list(clients.keys()):
        try:
            client_socket.send("Server is shutting down.".encode('utf-8'))
            client_socket.close()
        except socket.error as e:
            logging.error(f"Error closing client socket: {e}")
    global server_socket
    server_socket.close()
    os._exit(0)  # Forcefully stop the program


#-------------------------------------------------#


def process_command(client_socket, message):
    try:
        """Process commands from a client based on the message received."""
        parts = message.decode('utf-8').strip().split()   # parts is something like ['@User', 'msg'] so it is 2D array
        command = parts[0]
        sender_pseudonym = clients[client_socket]['pseudonym']  # Retrieve sender's pseudonym
        # Check if the client is suspended


        if client_states[client_socket] == 'suspended':
            #TODO to be fixed
            logging.info("T1")
            if command.startswith('@') or command == "logout":
                logging.info("T2")
                # Suspended clients should not be able to execute commands
                client_socket.send("You are suspended and cannot execute commands.".encode('utf-8'))
                return
            else:
                # Allow suspended clients to receive messages but not send
                logging.info(f"Suspended user {sender_pseudonym} attempted to send a message.")
                return

        # Process commands or logout requests
        if command == '!start':
            handle_start_game()
        elif command == "!logout":
            handle_logout(client_socket)
        elif command == "!shutdown":
            if sender_pseudonym == MODERATOR_PSEUDONYM:
                handle_shutodwn()
            else:
                client_socket.send("Unauthorized to shut down the server.".encode('utf-8'))
        elif command == "!list":
            handle_list_command(client_socket)
        elif command.startswith('@'):
            handle_direct_command(client_socket, parts)
        else:
            logging.info("Unknown command received.")
    except socket.error as e:
        logging.error("Socket error: " + str(e))
        close_client_connection(client_socket)
    except ValueError as e:
        logging.error("Value error: " + str(e))
        # Handle specific errors like decoding errors or data type issues
    except Exception as e:
        logging.error("Unexpected error: " + str(e))
        # Handle unexpected exceptions

def broadcast_message(sender_socket, message):
    """Broadcast a message to all clients except the sender, including the sender's pseudonym."""
    sender_pseudonym = clients[sender_socket]['pseudonym']  # Get the pseudonym of the sender
    full_message = f"{sender_pseudonym}: {message.decode('utf-8')}".encode('utf-8')  # Prepend pseudonym to the message
    closed_clients = []
    for client_socket in clients:
        if client_socket != sender_socket:  # Exclude the sender from receiving the message
            try:
                client_socket.send(full_message)  # Send the message to each client
            except Exception as e:
                logging.error(f"Failed to send message to {clients[client_socket]['address'][0]}: {str(e)}.")
                client_socket.close()
                closed_clients.append(client_socket)
    # Clean up closed client sockets
    for client_socket in closed_clients:
        clients.pop(client_socket, None)
    return sender_pseudonym

def broadcast_message_to_all(message):
    """Broadcast a message to all connected clients."""
    full_message = message.encode('utf-8')
    for client_socket in clients:
        try:
            client_socket.send(full_message)
        except Exception as e:
            logging.error(f"Failed to send message to {clients[client_socket]['address'][0]}: {str(e)}")
            client_socket.close()
            clients.pop(client_socket, None)

def close_client_connection(client_socket):
    try:
        client_socket.close()
        clients.pop(client_socket, None)
        logging.info(f"Closed connection from {clients[client_socket]['address'][0]}.")
    except Exception as e:
        logging.error("Error closing client connection: " + str(e))


#-------------------------------------------------#

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
                        logging.info("Attempted to use an existing pseudonym.")
                        client_socket.close()
                        #logging.info("test2")
                    elif game_active == True:
                        client_socket.send(b"Game has already started. Cannot join now.")
                        logging.info("Attempted to join after game has started.")
                        client_socket.close()
                    else:
                        clients[client_socket] = {'address': client_address, 'data': [], 'pseudonym': pseudonym}
                        logging.info(f"Accepted new connection from {client_address[0]} : {client_address[1]} with pseudonym: {pseudonym}.")
                else:
                    try:
                        message = notified_socket.recv(1024)
                        if message:
                            if message.startswith(b'!') or b'@' in message or client_states[client_socket] == "suspended":   #data from the socket is in the form b'xyz'
                                #logging.info("TEST12")
                                process_command(notified_socket, message)
                            else:
                                # Broadcast the message to other clients
                                sender = broadcast_message(notified_socket, message)
                                logging.debug(f"Broadcasted message from {sender}, message: {message.decode('utf-8')}.")
                        else:
                            # No message means the client has disconnected
                            logging.info(f"Closed connection from {pseudonym} of address {clients[notified_socket]['address'][0]}.")
                            clients.pop(notified_socket)
                            notified_socket.close()
                    except Exception as e:
                        logging.error(f"Error handling message from {pseudonym} of address {clients[notified_socket]['address'][0]}: {str(e)}.")
                        clients.pop(notified_socket)
                        notified_socket.close()

            for notified_socket in exception_sockets:
                close_client_connection(notified_socket)
                
    except Exception as e:
        logging.error(f"Fatal error in server main loop: {str(e)}.")
    finally:
        logging.info("Server shutting down...")
        server_socket.close()
        for client_socket in list(clients.keys()):
            close_client_connection(client_socket)



if __name__ == "__main__":
    start_server()

#-------------------------------------------------#