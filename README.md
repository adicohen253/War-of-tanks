Welcome to War Of Tanks (Wot) setup guide!, in this guide you will be able to set your own server of the game and play with your friends.
=================================================================================================================================================

the project is made of 4 parts:
1.The Game's client, Can be downloaded using an installer from the game website (see 3. )
2.MYSQL database to handle all the data of the server-side of the project
3.Django based web application to handle traffic to the server website
4.The game server itself, allows you to manage accounts of the server and other settings

=================================================================================================================================================

As of now the game server only has a GUI option for managing purposes, therefore requires the host OS to be linux based (Windows wsl works too)
With graphic display capabilities, On other systems the server will run as well but wont be accessible to manage,
For the GUI to work simply run the following command on you Host machine: "xhost +local:docker"

Note: An API for the server management without the gui is currently on development and will be added to the versio 2.0 of the server Docker image

=================================================================================================================================================
To run the Game's server and services simply change the SERVER_ADDRESS setting in the Docker compose file under the "web" service
to the ip of the host machine, Than just run the docker compose file, you will be able to install the client from that ip and port 8001
{http:<yourip>:8001/downloads} on your web browser

Start play with your friends and become the #1! 😀