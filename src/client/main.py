# Boucle de base du jeu, l'initialisant et gérant le passage entre les différents écrans du programme (menu, jeu, scores de fin de partie)

###########################
# Importation des modules #
###########################

import pygame
import menu
import game
import client
import sys
from os import listdir

##########################
# Définitions de classes #
##########################

class Main:
    def __init__(self, width, height, fps, fullscreen = False):
        pygame.init()
        self.running = True # Condition de la boucle principale du programme
        self.volume = 1 # volume des sons
        if fullscreen: # Gestion de l'affichage en plein écran
            self.flags = pygame.FULLSCREEN
        else:
            self.flags = 0
        self.screenw, self.screenh, self.fps = width, height, fps # Dimensions de la fenêtre et fréquence de rafraîchissement
        self.thread = client.ThreadClient(self, HOST, PORT) # Thread client gérant la connexion au serveur
        self.app = menu.Application(self) # Application affichée au départ, ici le menu principal
        
        
    def run(self):
        """
        Main.run() --> None
        Boucle principale de l'application, gérant le passage du menu au jeu
        """
        self.thread.start()
        self.thread.send("client OK:/")
        while self.running:
            self.app.start()
        try: self.thread.send("FIN")
        except: pass
        pygame.quit()
        exit()
    
    def get_screenW(self):
        """
        Main.get_screenW() --> int
        Retourne la largeur de l'écran
        """
        return self.screenw
    
    def get_screenH(self):
        """
        Main.get_screenH() --> int
        Retourne la hauteur de l'écran
        """
        return self.screenh
    
    def get_fps(self):
        """
        Main.get_fps() --> int
        Retourne la fréquence de rafraîchissement de l'écran
        """
        return self.fps

    def get_volume(self):
        """
        Main.get_volume() --> int
        Retourne le volume des sons
        """
        return self.volume

    def setVolume(self, volume):
        """
        Main.setVolume(int volume) --> None
        Met à jour le volume
        """
        self.volume = volume

#####################
# Partie principale #
#####################
 
HOST, PORT = "localhost", 50000
width, height, fps = 1280,720, 60

Main(width, height, fps).run()