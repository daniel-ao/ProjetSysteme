# Import necessary libraries
import socket
import select
import os
from collections import defaultdict
import logging
import sys


#--------------------------------------------------------------------------------------------############################
# Setup basic logging                                                                        #                          #
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s') #     @            @       #
#--------------------------------------------------------------------------------------------#                          #
# Server configuration variables                                                             #                          #
SERVER_IP = '127.0.0.1'  # Listen on all network interfaces                                  #                          #
#SERVER_PORT = 2024  # Port to listen on                                                     #           ^              #
# Check for command-line arguments for the port number                                       #                          #             
if len(sys.argv) != 2:                                                                       #         ^   ^            #                         
    print("Usage: python3 server.py <port_number>")                                          #                          #        
    sys.exit()                                                                               #                          #                                                             
SERVER_PORT = int(sys.argv[1])  # Use the port number provided from command-line arguments   #                          #                             
MAX_CONNECTIONS = 10  # Maximum number of simultaneous client connections                    #      --------------      #
MODERATOR_USERNAME = "Admin"                                                                 #                          #
#-----------------------------------------------------------------------------------------------------------------------#
# Client management variables                                                                                           
# Client management variables                                                                                           
clients = {}  # Dictionary to store client socket objects along with additional information                             
client_states = defaultdict(lambda: "active")  # Tracks the current state ('active', 'suspended', etc.) of each client  
game_active = False # Flag to indicate if the game has started                                                          
#-----------------------------------------------------------------------------------------------------------------------#
# Socket setup                                                                                                          
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                                                       
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)                                                     
server_socket.bind((SERVER_IP, SERVER_PORT))                                                                            
server_socket.listen(MAX_CONNECTIONS)                                                                                   
#-----------------------------------------------------------------------------------------------------------------------#
logging.info(f"Server started on {SERVER_IP} : {SERVER_PORT}.")                                                         
#-----------------------------------------------------------------------------------------------------------------------#

   
#-------------------------------------------------#
# Helper functions

def get_client_by_USERNAME(USERNAME):
    """Retrieve client socket based on USERNAME."""
    for client, details in clients.items():
        if details['USERNAME'] == USERNAME:
            return client
    return None

def close_client_connection(client_socket):
    try:
        client_socket.close()
        clients.pop(client_socket, None)
        logging.info(f"Closed connection from {clients[client_socket]['address'][0]}.")
    except Exception as e:
        logging.error("Error closing client connection: " + str(e))


#-------------------------------------------------#
# Command handling functions

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
        if target_client == get_client_by_USERNAME(MODERATOR_USERNAME):
            logging.info("Admin cannot ban themselves.")
            return
        target_client.send("You have been banned from the game.".encode('utf-8'))
        ban_message = f"Player {clients[target_client]['USERNAME']} has been banned"
        broadcast_message(target_client, ban_message.encode('utf-8'))
        logging.info(f"{ban_message} by Admin")
        target_client.close()
        clients.pop(target_client, None)
    else:
        logging.error("Attempted to ban a non-existent client.")

def handle_suspend(client_socket):
    if client_socket in clients:
        # Check if the target is the moderator or if the client is already suspended
        if client_socket == get_client_by_USERNAME(MODERATOR_USERNAME):
            #client_socket.send("Admin cannot be suspended.".encode('utf-8'))
            logging.info("Attempt to suspend the admin was blocked.")
            return

        if client_states[client_socket] == 'suspended':
            client_socket.send(f"Admin tried to suspend you again.".encode('utf-8'))
            broadcast_message_to_all(f"{clients[client_socket]['USERNAME']} is already suspended.", client_socket)
            logging.info(f"Attempt to re-suspend {clients[client_socket]['USERNAME']} was blocked.")
            return

        try:
            clients[client_socket]['state'] = 'suspended'
            client_states[client_socket] = 'suspended'  # Update the state in the dictionary
            client_socket.send("You have been suspended.".encode('utf-8'))
            broadcast_message_to_all(f"{clients[client_socket]['USERNAME']} has been suspended.", client_socket)
            logging.info(f"{clients[client_socket]['USERNAME']} has been suspended.")
        except Exception as e:
            logging.error(f"Failed to suspend {clients[client_socket]['USERNAME']}: {str(e)}")

def handle_forgive(client_socket):
    if client_socket in clients:
        if client_socket == get_client_by_USERNAME(MODERATOR_USERNAME):
            logging.info("Admin cannot forgive themselves.")
            return
        if client_states[client_socket] == 'active':
            broadcast_message_to_all(f"{clients[client_socket]['USERNAME']} is not suspended to be forgiven.")
            logging.info(f"Attempt to forgive {clients[client_socket]['USERNAME']} which is not suspended was blocked.")
            return
        try:
            clients[client_socket]['state'] = 'active'
            client_states[client_socket] = 'active'  # Update the state back to active
            client_socket.send("You have been forgiven and can participate again.".encode('utf-8'))
            broadcast_message_to_all(f"{clients[client_socket]['USERNAME']} has been forgiven.", client_socket)
            logging.info(f"{clients[client_socket]['USERNAME']} has been forgiven.")
        except Exception as e:
            logging.error("Failed to lift suspension: " + str(e))
            
def handle_PM(message, recipients, sender_USERNAME, client_socket):
    # Handling private message to one or more users including Moderator
        if len(message) == 0:
            client_socket.send("You didn't enter a message.".encode('utf-8'))
            return

        final_message = f"PM from {sender_USERNAME}: {' '.join(message)}"
        # Send message to all recipients and Moderator (if not already included)
        recipients.append(MODERATOR_USERNAME)  # Ensure moderator gets the PM
        recipients = set(recipients)  # Remove duplicates
        for recipient in recipients:
            target_client = get_client_by_USERNAME(recipient)
            if target_client:
                target_client.send(final_message.encode('utf-8'))
            elif recipient != MODERATOR_USERNAME:
                client_socket.send(f"No such user: {recipient}".encode('utf-8'))
            #else:
            #   client_socket.send(f"No such user: {recipient}".encode('utf-8'))

def handle_logout(client_socket):
    """Handle the logout command."""
    logging.info(f"Client {clients[client_socket]['USERNAME']} has disconnected.")
    client_socket.send(f"Goodbye {clients[client_socket]['USERNAME']}!".encode('utf-8'))
    broadcast_message_to_all(f"{clients[client_socket]['USERNAME']} has left the chat.", client_socket)
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

def handle_list_command(requesting_client_socket):
    """
    Handle the !list command to display the status of all clients in a tabular format.
    Send the list back to the client who requested it.
    """
    header = f"{'USERNAME':<20} | {'State':<10}\n" + "-" * 32
    status_message = [header]

    sorted_clients = sorted(clients.items(), key=lambda item: item[1]['USERNAME'])

    for client_socket, details in sorted_clients:
        USERNAME = details['USERNAME']
        state = client_states[client_socket]
        row = f"{USERNAME:<20} | {state:<10}"
        status_message.append(row)

    final_message = "\n".join(status_message)
    requesting_client_socket.send(final_message.encode('utf-8'))


#-------------------------------------------------#
# Command processing functions

def handle_direct_command(client_socket, parts):
    sender_USERNAME = clients[client_socket]['USERNAME']  # Retrieve sender's USERNAME
    # Start by identifying if the message is a private message or a command.
    recipients = []
    message = []
    command_flag = False
    if len(parts[0]) == 1:
        client_socket.send("Enter a USERNAME.".encode('utf-8'))
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
        client_socket.send("Enter a valid USERNAME after '@'.".encode('utf-8'))
        return

    if command_flag:
        # This is a command to a specific user.
        if sender_USERNAME != MODERATOR_USERNAME:
            client_socket.send("Unauthorized command execution.".encode('utf-8'))
            return
        target_client = get_client_by_USERNAME(recipients[0])  # Assuming command to first user only
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
            # Suggest corrections for common command typos or prefix matches
            if 'b' in command:
                suggestion = "!ban"
            elif 's' in command:
                suggestion = "!suspend"
            elif 'f' in command:
                suggestion = "!forgive"
            else:
                suggestion = None

            if suggestion:
                client_socket.send(f"Command {command} not found, did you mean: {suggestion}?".encode('utf-8'))
            else:
                client_socket.send("Unknown command.".encode('utf-8'))

    else:
        handle_PM(message, recipients, sender_USERNAME, client_socket)

def process_command(client_socket, message):
    try:
        """Process commands from a client based on the message received."""
        parts = message.decode('utf-8').strip().split()   # parts is something like ['@User', 'msg'] so it is 2D array
        command = parts[0]
        sender_USERNAME = clients[client_socket]['USERNAME']  # Retrieve sender's USERNAME

        # Check if the client is suspended
        if client_states[client_socket] == 'suspended':
            # Suspended clients should not be able to execute commands
            client_socket.send("You are suspended and cannot execute commands or send messages.".encode('utf-8'))
            return


        # Process commands or logout requests
        if command in ['!shutdown', '!start'] and sender_USERNAME != MODERATOR_USERNAME:
            if command == '!shutdown':
                client_socket.send("Unauthorized to shutdown the server".encode('utf-8'))
            if command == '!start':
                client_socket.send("Unauthorized to start the game".encode('utf-8'))
            return

        # Handling commands
        if command == "!start":
            handle_start_game()
        elif command == "!shutdown":
            handle_shutodwn()
        elif command == "!logout":
            handle_logout(client_socket)
        elif command == "!list":
            handle_list_command(client_socket)
        elif command.startswith('@'):
            handle_direct_command(client_socket, parts)
        else:
            logging.info(f"Unknown command received: {command}")
            client_socket.send("Unknown command.".encode('utf-8'))
    except socket.error as e:
        logging.error("Socket error: " + str(e))
        close_client_connection(client_socket)
    except ValueError as e:
        logging.error("Value error: " + str(e))
        # Handle specific errors like decoding errors or data type issues
    except Exception as e:
        logging.error("Unexpected error: " + str(e))
        # Handle unexpected exceptions


#-------------------------------------------------#
# Broadcast functions

def broadcast_message(sender_socket, message):
    """Broadcast a message to all clients except the sender, including the sender's USERNAME."""
    sender_USERNAME = clients[sender_socket]['USERNAME']  # Get the USERNAME of the sender
    full_message = f"{sender_USERNAME}: {message.decode('utf-8')}".encode('utf-8')  # Prepend USERNAME to the message
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
    return sender_USERNAME

def broadcast_message_to_all(message, *excluded_clients):
    """
    Broadcast a message to all connected clients, with optional exclusions.
    
    Parameters:
        message (str): The message to broadcast.
        *excluded_clients: Variable number of client sockets to exclude from the broadcast.
    """
    full_message = message.encode('utf-8')
    excluded_sockets = set(excluded_clients)  # Convert to set for O(1) look-up times
    
    for client_socket in clients:
        if client_socket not in excluded_sockets:  # Only send if not in the excluded list
            try:
                client_socket.send(full_message)
            except Exception as e:
                logging.error(f"Failed to send message to {clients[client_socket]['address'][0]}: {str(e)}")
                client_socket.close()
                clients.pop(client_socket, None)  # Safe removal from dictionary during iteration


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
                    USERNAME = client_socket.recv(1024).decode('utf-8').strip()  # Assume the first message is the USERNAME
                    
                    if USERNAME == MODERATOR_USERNAME:
                        client_socket.send(b"Enter the password for Admin:")
                        password = client_socket.recv(1024).decode('utf-8').strip()
                        if password != "admin123":  
                            client_socket.send(b"Incorrect password. Connection terminated.")
                            logging.info("Attempted to login as Admin with incorrect password.")
                            client_socket.close()
                            continue
                        else:
                            client_socket.send(b"Password correct. Welcome, Admin.\n")  # Append a newline to separate from future commands
                            clients[client_socket] = {'address': client_address, 'USERNAME': USERNAME, 'state': 'active'}
                            logging.info(f"Admin logged in from {client_address}")
                            continue  # Skip to the next iteration to prevent sending an extra prompt
                    
                    if USERNAME in [clients[sock]['USERNAME'] for sock in clients]:
                        client_socket.send(b"USERNAME already in use.")
                        logging.info("Attempted to use an existing USERNAME.")
                        client_socket.close()
                    elif game_active == True:
                        client_socket.send(b"Game has already started. Cannot join now.")
                        logging.info("Attempted to join after game has started.")
                        client_socket.close()
                    else:
                        clients[client_socket] = {'address': client_address, 'data': [], 'USERNAME': USERNAME}
                        logging.info(f"Accepted new connection from {client_address[0]} : {client_address[1]} with USERNAME: {USERNAME}.")
                else:
                    try:
                        message = notified_socket.recv(1024)
                        if message:
                            if client_states[notified_socket] == 'suspended':
                                process_command(notified_socket, message)
                            elif message.startswith(b'!') or b'@' in message: 
                                process_command(notified_socket, message)
                            else:
                                # Broadcast the message to other clients
                                sender = broadcast_message(notified_socket, message)
                                logging.debug(f"Broadcasted message from {sender}, message: {message.decode('utf-8')}.")
                        else:
                            # No message means the client has disconnected
                            logging.info(f"Closed connection from {USERNAME} of address {clients[notified_socket]['address'][0]}.")
                            clients.pop(notified_socket)
                            notified_socket.close()
                    except Exception as e:
                        logging.error(f"Error handling message from {USERNAME} of address {clients[notified_socket]['address'][0]}: {str(e)}.")
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


#-------------------------------------------------#



#-------------------------------------------------#
if __name__ == "__main__":                        #
    start_server()                                #
#-------------------------------------------------# 