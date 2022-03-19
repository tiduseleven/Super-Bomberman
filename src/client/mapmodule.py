# Module gérant la génération du plateau ainsi que son affichage à l'écran

###########################
# Importation des modules #
###########################

import pygame
from math import *
from pygame.constants import *
import sys
from os import listdir
sys.path.append("../commonmodules")
from objects import *
from variables import *

##########################
# Définitions de classes #
##########################

class Tile(pygame.sprite.Sprite):
    """ Attributs de base d'une case du plateau"""

    def __init__(self, x, y, w, h, image, color):
        super().__init__()
        #attributs de classe:
        self.x, self.y, self.w, self.h = x, y, w, h # Coordonnées et taille de la case
        self.color = color # Couleur utilisée dans le cas où aucune image n'est communiquée
        
        #Création de l'objet:
        if image!=[]:
            self.image = image
        else:
            self.image = pygame.Surface([w,h])
            self.image.fill(color)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = x,y

    def render(self, screen):
        """
        Tile.render(pygame.Surface screen)
        Affiche la case sur l'écran
        """
        self.image.render(screen,self.rect)
    
class Block(Tile):
    """Un bloc incassable bloquant le joueur"""
    def __init__(self, x, y, w, h, image = [], color=colors["BLUE"]):
        super().__init__(x,y,w,h, image, color)
    
    def destroy(self):
        """
        Block.destroy() --> False
        Fonction gérant la destruction d'un bloc incassable, évitant des erreurs lors des explosions.
        """
        return 0
        
class Brick(Tile):
    """Une brique que le joueur peut casser avec une bombe"""
    def __init__(self, master, app, x, y, w, h, powerup, images=[], color=colors["GREEN"],):
        super().__init__(x,y,w,h,images[0],color)
        self.master = master # Référence au plateau
        self.app = app
        self.images = images
        self.i = 0 # indice comptant le nombre d'images passées (quand la brique est en train de se détruire)
        self.destroyed = 0 # Flag gérant la destruction de la brique
        if powerup:
            self.powerup = PowerUp(self,powerup,Image(PowerUp.images[powerup],h))
        else:
            self.powerup = None

    def destroy(self):
        """
        Brick.destroy() --> None
        Gère la destruction de la brique
        """
        self.destroyed = 1
        self.master.allGrounds.add(Ground( self.x, self.y, self.w, self.h)) # Ajout d'un sol en-dessous de la brique détruite

    def update(self):
        """
        Brick.update() --> None
        Gère la mise à jour de la brique une fois qu'elle a été en contact avec une explosion
        """
        if self.destroyed:
            self.changeImage()
            if self.i>= self.app.fps/2:
                if self.powerup:
                    self.master.allPowerups.add(self.powerup)
                self.kill()
            
    def changeImage(self):
        """
        Brick.changeImage() --> None
        Gère la mise à jour de l'image de la brique
        """
        self.i += 1
        newImage = self.images[min(int(self.i/self.app.fps*2*len(self.images)),6)]
        if newImage != self.image:
            self.image = newImage

class Ground(Tile):
    """Le sol, sur lequel le joueur peut marcher et poser des bombes"""
    def __init__(self, x, y, w, h, image=[], color=colors["PALEGREEN"]):
        super().__init__(x,y,w,h,image, color)
    
    def render(self, screen):
        """
        Ground.render(pygame.Surface screen)
        Affiche la case sur l'écran
        """
        screen.blit(self.image,self.rect)

class PowerUp(Tile):
    """Les améliorations que le joueur peut ramasser"""
    images = {
        "speedup":"./images/sprites/powerups/speedup.png",
        "rangeup":"./images/sprites/powerups/rangeup.png",
        "bombup":"./images/sprites/powerups/bombup.png"
        }

    def __init__(self, origin, powerup, image = [], color = colors["RED"]):
        super().__init__(origin.x, origin.y, origin.w, origin.h, image, color)
        if powerup == "bombup":
            self.func = lambda takenby: self.BombUp(takenby)
        elif powerup == "rangeup":
            self.func = lambda takenby: self.RangeUp(takenby)
        elif powerup == "speedup":
            self.func = lambda takenby: self.SpeedUp(takenby)

    def handleCollision(self, players):
        usefulPlayers = pygame.sprite.spritecollide(self, players, False)
        for player in usefulPlayers: # on donne la powerup à tous les joueurs s'il y en a plusieurs en même temps
            self.taken(player)
        if usefulPlayers: # on détruit la powerup une fois prise
            self.kill()

    def taken(self, takenBy):
        """
        PowerUp.destroy(Player.player takenBy) --> None
        Gère la disparition de la PowerUp et l'attribution du bonus au joueur
        """
        self.func(takenBy)
    
    def RangeUp(self, taker):
        """
        Powerup.RangeUp(player taker) --> None
        Augmente la portée des bombes du joueur <taker>
        """
        taker.range_up()
    
    def BombUp(self, taker):
        """
        Powerup.RangeUp(player taker) --> None
        Augmente le nombre de bombes du joueur <taker>
        """
        taker.bomb_up()
    
    def SpeedUp(self, taker):
        """
        Powerup.SpeedUp(player taker) --> None
        Augmente la vitesse du joueur <taker>
        """
        taker.speed_up()
    
class Plateau(object):
    """Le plateau de jeu"""
    # Dictionnaire des sprites de cases
    tiles = {} # dictionnaire répertoriant les différentes images des cases.
    tiles["block"] = "./images/sprites/battle1/tiles/block.png"
    brickList = []
    for img in listdir("./images/sprites/battle1/tiles/brick"):
        brickList.append("./images/sprites/battle1/tiles/brick"+"/"+img)
    tiles["brick"] = brickList

    def __init__(self, master, w, h):
        
        # Attributs de base:
        self.master = master
        self.w, self.h = w, h #Largeur et hauteur du plateau
        self.playerSpawns = [] #Points d'apparition des joueurs
        
        # Création des images
        self.brickImages = []
        for imageString in Plateau.tiles["brick"]:
            self.brickImages.append(Image(imageString,h/17))

        self.blockImage = Image(Plateau.tiles["block"],h/17)
        
        # Groupes de sprites
        self.allBombs = pygame.sprite.Group()   # groupe des sprites des bombes
        self.allGrounds = pygame.sprite.Group() # groupe des sprites des sols
        self.allBlocks = pygame.sprite.Group()  # groupe des sprites des blocs
        self.allBricks = pygame.sprite.Group()  # groupe des sprites des briques
        self.allWalls = pygame.sprite.Group()   # groupe des sprites de tous les murs (blocs + briques)
        self.allPowerups = pygame.sprite.Group() # groupe des sprites des bonus
    
    def createTiles(self,tilesList):
        """
        Plateau.createTiles(list tilesList) --> None
        Crée le plateau de jeu selon les indications de tilesList
        """
        self.allBombs.empty()
        self.allGrounds.empty()
        self.allBlocks.empty()
        self.allBricks.empty()
        self.allWalls.empty()
        self.allPowerups.empty()
        # Dimensions:
        width, height = self.w/17, self.h/17 # dimensions d'une case
        initialx, initialy = self.master.screenw/2-width*8.5, self.master.screenh/2-height*8.5 # coordonnées de la première case

        # Création des images:
        for line,j in zip(tilesList,range(0,len(tilesList))) :
            elements=line.split(",")
            for elem,i in zip(elements,range(0,len(elements))) :
                if elem == "0": #Sol vide:
                    self.allGrounds.add(Ground(initialx+i*width, initialy+j*height, width, height))
                elif elem == "1": #Bloc incassable:
                    self.allBlocks.add(Block(initialx+i*width, initialy+j*height, width, height, image=self.blockImage))
                elif elem[0] == "2": #Briques cassables:
                    if elem[1] == "1":
                        powerup = "rangeup"
                    elif elem[1] == "2":
                        powerup = "bombup"
                    elif elem[1] == "3":
                        powerup = "speedup"
                    else:
                        powerup = None
                    self.allBricks.add(Brick(self, self.master, initialx+i*width, initialy+j*height, width, height, powerup, images=self.brickImages))
                elif elem == "3": #Points d'appartion des joueurs
                    self.allGrounds.add(Ground(initialx+i*width, initialy+j*height, width, height))
                    self.playerSpawns.append([i,j])

        self.allWalls.add(self.allBricks)
        self.allWalls.add(self.allBlocks)

    def update(self, screen):
        """
        Plateau.update(pygame.Surface screen) --> None
        Met à jour les différents éléments du plateau et les affiche à l'écran
        """
        for ground in self.allGrounds:
            ground.render(screen)
        for brick in self.allBricks:
            brick.update()
        for wall in self.allWalls:
            wall.render(screen)
        for powerup in self.allPowerups:
            powerup.handleCollision(self.master.get_players())
            powerup.render(screen)
        for bomb in self.allBombs: # mise a jour des bombes selon la classe Bomb définie dans <player.py>
            bomb.update(screen)
    
    def render(self, screen):
        """
        Plateau.render(pygame.Surface screen) --> None
        Affiche le plateau à l'écran
        """