# Python Super Bomberman
## Short description
This is a reproduction of Super Bomberman for SNES made using python.  
The game has been adapted to a server-based multiplayer architecture via socket.  
The graphical interface uses pygame.  
I made this game as a project in High School besides my classes.  
The rest of the project is mostly in French due to my classes being in French.
## How to run
On the client machines, install the module pygame:  
```bash
pip install pygame
```
For the server and the client, change the IP address in `main.py` file to the one of your server machine.  
Start the server by running its `main.py` file  
Start your clients by running their `main.py` file
## Additional settings
On the client, you can change the resolution of the game in `main.py`. You can also pass a `fullscreen=True` argument if you want the game to show in fullscreen.
