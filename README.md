# ProjetSysteme
Project on Operating systems

## ABOU ORM Daniel:

For this project, I worked alone on it, and it was one of the best projects I worked on, as I was too passion about it, and I would just stay up to 4 am to fix a small bug of this project.


## Points Stuck on:

    For the part on which I remained stuck, it was the command '!suspend' where it took from me more than 2 days just trying to fix it, and the bugs that appears everytime after it works.
    Another point which was when the client disconnects, or the server disconnects he still got the prompt to enter a message or execute a command, so I added a feature when the client disconnects, he is prompted to press 'enter' which will get him to normally use his terminal again without having to use 'Ctrl-C'


## Different versions:

    For the different stable/unstable versions of my project I am gonna share with you my 'git repository' and you can check there the different commits I had on my project.
    [GitHub](https://github.com/daniel-ao/ProjetSysteme "Visit my GitHub Repo")


### Extra Comment:

    I would like to invite you to explore the server and client scripts developed for this project. Much effort and attention to detail have been devoted to ensure robust and efficient functionality. Your feedback and insights on the work presented would be greatly appreciated, as they are invaluable to my learning and improvement.


#--------------------------------------------------------------------------------#
# Manual of the project:

The execution of the server script will only run the server, and if someone chooses to be the Moderator, he should run the client script and login as the Admin(Moderator)

## To login with Admin:

    USERNAME: Admin

    Password: admin123

## Execute the following command to start the server:

    'python3 chat_killer_server.py PORT'

    You should see a message indicating that the server has started. 
    "Server started on 127.0.0.1 : PORT."

## Run the Client Script by executing the following command:

    python3 chat_killer_client.py ADDRESS PORT

    The script will then prompt you to enter a USERNAME. If the USERNAME is already taken or if the game has started, you will be informed and disconnected.

## Command Manual for Chat/Game Server:

    Admin Credentials:

        To perform administrative actions. The Admin must first log in using the special USERNAME 'Admin' and the correct password.

    Actions and Commands Available for the clients:

        • Sending normal messages 
        • !list
        •'!logout' AND 'quit'(A client can use 'quit' to quit if he was suspended)
        • Private messages with form of (@USR1 @USR2 Private Message)

    Action and Commands Available for the Admin:

        • All the actions available for the client
        • !start (Start the game)
        • !shutdown (Shutdown the sever)
        • @USR !ban 
        • @USR !suspend
             (Checks first if the player is suspended, if yes Admin will be notified that the player is suspended, suspend him otherwise)
        • @USR !forgive
             (Checks first if the player is active, if yes Admin will be notified that the player is active, forgive him otherwise)

    If a USER for example mistakenly put '@USR !bam' or '@USR !suspemd' or '@USR !forgove'.
        The user will get a message "Command {command} not found, did you mean: {suggestion}?"


#--------------------------------------------------------------------------------#

# General Information of the project:

The server script is designed to handle multiple client connections, manage client statuses, and process various commands in a chat/game environment. The server operates on IP 127.0.0.1 and optional PORT, supporting up to 10 simultaneous connections. It utilizes socket programming, select for handling I/O multiplexing, and includes extensive logging for debugging and monitoring activities.

## Key Features:

    1)Basic Configuration and Logging:

        Logging is set up to track events with timestamps, severity levels, and messages to help in debugging and monitoring server activities.

    2)Client Management:

        Clients are managed through a dictionary that stores each client's socket object along with their USERNAME and current state (active, suspended, etc.).
        The server tracks game states, determining whether new players can join.

    3)Command Handling:

        • Start Game: Initiates the game and prevents new players from joining. It broadcasts that the game has started to all connected clients.
        
        • Ban: Allows the Admin to ban a player, which disconnects them from the server and announces this action to all clients.
        
        • Suspend/Unsuspend (Forgive): Admin can suspend a client from sending messages or commands, and forgive them later. These state changes are communicated directly to the affected client and logged, and the state of this player will be broadcasted to all connected clients.
        
        • Private Messaging: Handles private messages sent from one client to another or a group of others, and the Admin will be able to see the messages even if he wasn't mentioned.
        
        • Logout: Processes client disconnections cleanly, ensuring all resources are freed and other clients are notified.
        
        • Shutdown: An Admin command that cleanly shuts down the server, closing all connections and the server socket itself.
        
        • List: Lists all currently connected clients along with their statuses to the requesting client.

## Security Features:

    The Admin login requires a password (hardcoded as Admin123). This process is secured by not allowing other commands until the password is validated.

## Robust Error Handling:

    The server robustly handles various potential errors such as socket errors, value errors, and other exceptions, ensuring the server remains stable and responsive.

## Message Broadcasting:

    Two broadcasting functions are included to send messages to all clients or all except specified clients, useful for announcements and command responses.

        ```def broadcast_message(sender_socket, message):``` This will send a message to all the connected clients on the server except the sender.

        ```def broadcast_message_to_all(message, *excluded_clients):``` This will send a message to all the connected clients, but we can exclude some clients, by adding them to the parameters.

## Command Processing:

    Commands from clients are parsed and executed based on their type and sender privileges.
    Only the Admin can execute the sensitive commands which are: start, shutdown, ban, suspend, forgive
    Regular clients can send private messages, request client lists, and disconnect using !logout or quit.

## Connection Management:

    The server handles new connections by accepting them only if the game hasn't started and the USERNAME isn't already in use. It also handles disconnections and errors during message handling, ensuring clients are removed from the management structures appropriately.

## Startup and Shutdown:

    The server starts by setting up the socket and entering a loop where it waits for client connections or messages. It can be gracefully shut down by an Admin command, which ensures all clients are properly disconnected before stopping the server process.