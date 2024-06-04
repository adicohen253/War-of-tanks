Welcome to War Of Tanks setup guide!, in this guide you will be able to set your own server of the game and play with your friends.
=================================================================================================================================================
This project provides a Docker-based setup for hosting a War of Tanks multiplayer server using Docker compose file hence only require Docker installed.
The project includes the following components:

1.The Game's client, Can be downloaded using an installer from the game website (see 3. )
2.MYSQL database to handle all the data of the server-side of the project
3.Django based web application which allows you to install the game's client and watch the top 5 players
4.The game server itself, allows you to manage accounts of the server and other settings
5.A controller container that can be used to manage the game server when there is no graphical display available (optional)

Note: The server's GUI is only available on linux based systems with graphical display to perform as the Docker host
by running the following command before running the docker compose file: "xhost +local:docker"
In any other case you can use The controller container which allows you to perform administrative actions on the server via API,
the controller itself isn't mandatory for the continuous of the server and the game and can be commented while running the compose.yaml file



=================================================================================================================================================
This project includes several features like:
1.RSA-based Encryption: To safeguard the sessions of the clients and the server, a basic RSA encryption is implemented communication between the server and each client. The server's public key is distributed to the clients, and the clients' public keys are distributed to the server. Data sent between the server and client is encrypted using the respective public keys and decrypted using the private keys.

2.The game includes a voice chat when you fighting against your friends which can be turn on/off by pressing the escape key

3.Players can change their tank's color to any color in the color palette

4.The server admin can create its own new maps to play with (Only available with the server's GUI)

=================================================================================================================================================
To run the Game's server and services simply change the SERVER_ADDRESS setting in the Docker compose file under the "web" service section
to the ip of the host machine, Than run the docker compose file, you will be able to install the client from that ip and port 8001
{http:<yourip>:8001/downloads} on your web browser

Start play with your friends and become the #1! 😀


![Test](MapBuilder_icon.png)