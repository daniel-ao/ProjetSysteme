import socket
import sys
import threading
import logging
logging.basicConfig(filename='client.log', filemode='a', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

#-------------------------------------------------#

def clear_line():
    """Clear the current line in the terminal."""
    sys.stdout.write('\r')
    sys.stdout.write('\033[K')  # ANSI escape sequence to clear the line

#-------------------------------------------------#

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
                    print(f"Socket errorTest: {e}")
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

#-------------------------------------------------#

def main():
    server_ip = "127.0.0.1"
    server_port = 2024
    #sock = None

    try:
        # Create a socket and connect to the server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((server_ip, server_port))
        print(f"Connected to {server_ip} on port {server_port}")

        # Get the pseudonym before creating the socket
        pseudonym = input("Enter your pseudonym: ")
        while not pseudonym.strip():
            print("Pseudonym cannot be empty. Please enter a valid pseudonym.")
            pseudonym = input("Enter your pseudonym: ")
        sock.send(pseudonym.encode('utf-8'))  # Send pseudonym immediately after connecting

        run_flag = {'active': True}
        receiver_thread = threading.Thread(target=receive_messages, args=(sock, run_flag))
        receiver_thread.start()

        try:
            while True:
                try:
                    message = input("Enter your message or command: ")
                    if message.lower() == 'quit':
                        sock.send("logout".encode('utf-8'))
                        logging.info("User has quit.")
                        break
                    sock.send(message.encode('utf-8'))
                except socket.error as e:
                    logging.error(f"Socket error during send operation: {str(e)}")
                    break
                except Exception as e:
                    logging.error(f"Unexpected error during send operation: {str(e)}")
                    break

        except KeyboardInterrupt:
            logging.info("Interrupted by user, exiting.")
        except Exception as e:
            logging.error(f"Critical error: {str(e)}")
        finally:
            if sock:
                sock.close()
                logging.info("Socket closed.")
    except Exception as e:
        print(f"Failed to connect to the server at {server_ip} : {server_port} : {e}")
        sys.exit()


#-------------------------------------------------#
if __name__ == "__main__":                        #
    main()                                        #                
#-------------------------------------------------#