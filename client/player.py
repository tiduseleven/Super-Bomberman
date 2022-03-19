# Module gérant le joueur, les bombes et leur explosion

###########################
# Importation des modules #
###########################

import pygame
from pygame.constants import *
from os import listdir
import time

from variables import *
from objects import *

##########################
# Définitions de classes #
##########################

class Player(pygame.sprite.Sprite):
    """Sprite d'un joueur"""
    # Dictionnaire des sprites des joueurs
    playerSprites = {}
    for i in range(1,5):
        playerAllSprites = {}
        playerFolders = listdir("./images/sprites/players/player"+str(i))
        for playerFolder in playerFolders:
            playerFolderImageList = []
            for image in listdir("./images/sprites/players/player"+str(i)+"/"+playerFolder):
                playerFolderImageList.append("./images/sprites/players/player"+str(i)+"/"+playerFolder+"/"+image)
            playerAllSprites[playerFolder]=playerFolderImageList
        playerSprites["player"+str(i)]=playerAllSprites
    
    def __init__(self, master, pseudo, xTile, yTile, w, h, speed, images):
        super().__init__()

        # Attributs d'instances de base:
        self.app = master
        self.i = 0 # Compteur d'images passées
        self.alive = 1 # Flag indiquant si le joueur est en vie
        self.frequency = self.app.fps/4 #Fréquence de changement d'image 
        self.maxBombs = 1 # Bombes maximales que le joueur peut poser en même temps
        self.bombsLeft = self.maxBombs # Bombes que le joueur peut encore poser
        self.baseExplodeLength = 2 # Longueur d'explosion de base
        self.explodeLength = self.baseExplodeLength # Longueur d'explosion actuelle

        # Attributs de mouvement et de position:
        self.tileSize = self.app.get_tileSize()
        self.xTile, self.yTile = xTile, yTile
        self.w, self.h = w, h
        self.setCoordsFromTiles(self.xTile, self.yTile) # Définition des coordonnées du joueurs --> définit self.x et self.y
        
        self.baseSpeed = speed
        self.speed = self.baseSpeed
        self.speedX, self.speedY = 0,0

        # Sprites:
        #dictionnaire répertoriant les sprites:
        self.renderedImages = {}

        for key,elem in zip(images,images.values()):
            renderedElem = []
            for image in elem:
                renderedImage = Image(image,h)
                renderedElem.append(renderedImage)
            self.renderedImages[key] = renderedElem

        #images actives:
        self.activeImages = [self.renderedImages["down"][0]]
        self.image = self.activeImages[self.i]

        self.imageRect = self.image.get_rect()

        self.imageRect.topleft = self.x,self.y-(h-w)
        self.rect= pygame.Rect(self.x, self.y, w, w) # hitbox carrée aux pieds du personnage

        # Pseudo:
        self.fontSize = round(self.app.screenh/40)
        font = pygame.font.Font("freesansbold.ttf",self.fontSize)
        self.pseudo = pseudo
        self.text = font.render(self.pseudo,True,colors["WHITE"],colors["DARKERGRAY"])
        self.textRect = self.text.get_rect()
        self.textRect.center = self.imageRect.centerx, self.imageRect.top- 0.5*self.fontSize

    def setCoordsFromTiles(self, xTile, yTile):
        """
        Player.setCoordsFromTiles(float xTile, float yTile) --> None
        Met à jour les coordonnées du joueur à partir de coordonnées sous forme de cases de plateau.
        """
        x, y = self.convertToCoords(xTile, yTile) # coordonnées du centre du joueur
        # Modifications pour obtenir le coin en haut à gauche de la zone de collision:
        self.x = x + (self.tileSize-self.w)/2
        self.y = y + (self.tileSize-self.w)/2

    def convertToCoords(self, xTile, yTile):
        """
        Player.convertToCoords(float xTile, float yTile) --> Tuple
        Convertit les coordonnées sous forme de cases de plateau en coordonnées sous valeur de pixel.
        """
        x = self.app.screenw/2+(xTile-8.5)*self.tileSize
        y = self.app.screenh/2+(yTile-8.5)*self.tileSize
        return (x,y)

    def handleEvent(self,event):
        """
        Player.handleEvent(pygame.Event event) --> None
        Méthode gérant les différentes actions faites par le joueur et transmettant le message au serveur
        """
        
        if self.alive:
            msg = ""
            if event.type == pygame.KEYDOWN:
                # Mouvement:
                if event.key == pygame.K_w:
                    msg = "start_move:up"
                elif event.key == pygame.K_s:
                    msg = "start_move:down"
                elif event.key == pygame.K_a:
                    msg = "start_move:left"
                elif event.key == pygame.K_d:
                    msg = "start_move:right"
                
                # Pose de bombe:
                elif event.key == pygame.K_e:
                    msg = "drop_bomb"
            
            elif event.type == pygame.KEYUP:
                # Arrêt de mouvement:
                if event.key == pygame.K_w:
                    msg = "stop_move:up"
                elif event.key == pygame.K_s:
                    msg = "stop_move:down"
                elif event.key == pygame.K_a:
                    msg = "stop_move:left"
                elif event.key == pygame.K_d:
                    msg = "stop_move:right"
            
            # Envoi du message:
            if msg != "":
                # Ajout des coordonnées (en cases de plateau) à la fin du message si c'est en lien avec du mouvement: pour éviter des problèmes de synchronisation
                if len(msg.split(":")) > 1 and msg.split(":")[1] in ["up","down","left","right"]:
                    xTile = (self.x - (self.app.screenw/2-8.5*self.tileSize + (self.tileSize-self.w)/2)) / self.tileSize
                    yTile = (self.y - (self.app.screenh/2-8.5*self.tileSize + (self.tileSize-self.w)/2)) / self.tileSize
                    msg+=","+str(xTile)+","+str(yTile)
                elif msg == "drop_bomb":
                    # Coordonnées du coin supérieur gauche de la case sur laquelle le joueur se trouve:
                    xTile = int((self.rect.centerx-(self.app.screenw/2-8.5*self.tileSize))/self.tileSize)
                    yTile = int((self.rect.centery-(self.app.screenh/2-8.5*self.tileSize))/self.tileSize)
                    msg+=":"+str(xTile)+","+str(yTile)

                
                self.app.thread.send(msg+"/")
    
    def startMove(self,direction):
        """
        Player.startMove(str direction) --> None
        Active le mouvement du joueur dans la direciton spécifiée
        """
        # Changement de la vitesse:
        if direction == "up":
            self.speedY -= self.speed
        elif direction == "down":
            self.speedY += self.speed
        elif direction == "left":
            self.speedX -= self.speed
        elif direction == "right":
            self.speedX += self.speed

        self.setImages(direction)

    def stopMove(self,direction):
        """
        Player.stopMove(str direction) --> None
        Stoppe le mouvement du joueur dans la direction spécifiée
        """
        # Changement de la vitesse:
        if direction == "up" or direction == "down":
            if direction == "up":
                self.speedY += self.speed
                opposite = "down"
            else:
                self.speedY -= self.speed
                opposite = "up"
        else:
            if direction == "left":
                self.speedX += self.speed
                opposite = "right"
            else:
                self.speedX -= self.speed
                opposite = "left"
        
        self.setImages(opposite)
    
    def setImages(self, direction):
        """
        Player.setImages(str direction) --> None
        Met à jour la liste Player.activeImages avec les images correspondant à la direction dans laquelle il va
        """
        if direction == "mort": # that's kinda dark... direction la mort!
            self.activeImages = self.renderedImages["death"]
        elif self.speedY == 0:
            if self.speedX == 0: #Caractère à l'arrêt
                self.activeImages = [self.activeImages[0]]
            elif self.speedX < 0:
                self.activeImages = self.renderedImages["left"]
            elif self.speedX > 0:
                self.activeImages = self.renderedImages["right"]
        elif self.speedX == 0:
            if self.speedY < 0:
                self.activeImages = self.renderedImages["up"]
            elif self.speedY > 0:
                self.activeImages = self.renderedImages["down"]
        else: # Mouvement diagonal
            self.activeImages = self.renderedImages[direction]

    def move(self, walls, bombs):
        """
        Player.move(list walls) --> None
        Gère le mouvement du joueur, dont la collision avec les briques
        """
        if self.alive:
            "Mouvement horizontal"
            if self.speedX != 0:
                # Mise à jour des coordonnées
                self.x += self.speedX*self.app.fps/self.app.clock.get_fps()
                self.updateCoords(self.x, self.y)
            
                # Détection des collisions
                self.handleCollision("X", walls, bombs)
                        

            
            "Mouvement vertical"
            if self.speedY != 0:
                #Mise à jour des coordonnées
                self.y += self.speedY*self.app.fps/self.app.clock.get_fps()
                self.updateCoords(self.x, self.y)

                # Détection des collisions
                self.handleCollision("Y", walls, bombs)
           
    def updateCoords(self, x, y):
        """
        Player.updateCoords(float x, float y) --> None
        Met à jour les coordonnées des différents objets visuels du joueur
        """
        self.rect.x, self.rect.y = x, y
        self.imageRect.topleft = x, y - (self.h - self.w)
        self.textRect.center = self.imageRect.centerx, self.imageRect.top-0.5*self.fontSize

    def handleCollision(self, direction, walls, bombs):
        """
        PLayer.handleCollisionX(str direction, pygame.sprite.Group walls, pygame.sprite.Group bombs) --> None
        Gère la collision horizontale ou verticale (selon <direction>) du joueur avec les murs et les bombes
        """
        # Définition des variables en fonction de la direction:
        if direction == "X":
            # 1 et 2 définissent respectivement dans la direction communiquée et dans la direction perpendiculaire
            speed1, speed2 = self.speedX, self.speedY
            coord1, coord2, center1 = self.x, self.y, self.rect.centerx
        else:
            # 1 et 2 définissent respectivement dans la direction communiquée et dans la direction perpendiculaire
            speed1, speed2 = self.speedY, self.speedX
            coord1, coord2, center1 = self.y, self.x, self.rect.centery
        # Collision avec les murs:
        usefulWalls = pygame.sprite.spritecollide(self, walls, False)
        for wall in usefulWalls :
            # Définition des variables utilisées du mur selon la direction:
            if direction == "X":
                # 1 et 2 définissent respectivement dans la direction communiquée et dans la direction perpendiculaire
                wallCoord1, wallCoord2 = wall.x, wall.y
                wallSides = [wall.rect.left,wall.rect.right]
            else:
                # 1 et 2 définissent respectivement dans la direction communiquée et dans la direction perpendiculaire
                wallCoord1, wallCoord2 = wall.y, wall.x
                wallSides = [wall.rect.top,wall.rect.bottom]
            
            if speed1 > 0 and center1 < wallSides[0] :
                coord1 = wallCoord1 - self.w
            elif speed1 < 0 and center1 > wallSides[1] :
                coord1 = wallCoord1 + wall.w

            # Mouvement automatique mettant le joueur dans une des lignes progresssivement, facilitant les carrefours; seulement si self.speedY est nul
            if speed2 == 0:
                if coord2 + self.w/2 - wallCoord2 < wall.w/4: #Centre vertical de la hitbox du joueur dans le quart supérieur du bloc / plus haut que le bloc
                    coord2 -= self.speed
                elif coord2 + self.w/2 - (wallCoord2+wall.w) > -wall.w/4: #Centre vertical de la hitbox du joueur dans le quart inférieur du bloc / plus bas que le bloc
                    coord2 += self.speed

        # Collisions avec les bombes 
        usefulBombs = pygame.sprite.spritecollide(self, bombs, False)
        
        for bomb in bombs:
            # Le joueur a quitté la bombe qu'il vient de poser:
            if bomb.master == self and bomb not in usefulBombs and bomb.stillOnBomb == 1:
                bomb.stillOnBomb = 0
            
            if bomb in usefulBombs:
                # Toujours sur la bombe:
                if bomb.stillOnBomb == 1 and bomb.master == self:
                    continue
                
                # Collision en soit:
                else:
                    # Définition des variables utilisées du mur:
                    if direction == "X":
                        coord = bomb.rect.x
                        sides = [bomb.rect.left, bomb.rect.right]
                    else:
                        coord = bomb.rect.y
                        sides = [bomb.rect.top, bomb.rect.bottom]
                    
                    if speed1 > 0 and center1 < sides[0]:
                        coord1 = coord-self.w
                    elif speed1 < 0 and center1 > sides[0]:
                        coord1 = coord+bomb.w
                    """elif speed2 < 0 and center1 > sides[1]:
                       coord1 =coord+bomb.w"""
        
        # Retransmission des changements à self.x et self.y
        if direction == "X":
            self.x, self.y = coord1, coord2
        else:
            self.y, self.x = coord1, coord2
        
        self.updateCoords(self.x, self.y)

    def dropBomb(self,xTile,yTile):
        """
        Player.dropBomb() --> None
        Pose une bombe aux pieds du joueur, au centre d'une case
        """
        if self.bombsLeft > 0 and pygame.sprite.spritecollide(self, self.app.plateau.allBombs, False) == []: # 2ème condition pour vérifier que le joueur ne soit pas sur une bombe
            x, y = self.convertToCoords(xTile, yTile)
            self.bombsLeft -= 1
            self.app.plateau.allBombs.add(Bomb(self,x,y,self.tileSize,self.explodeLength))

    def render(self,screen):
        """
        Player.render(pygame.Surface screen) --> None
        Affiche le joueur sur l'écran screen après avoir mis à jour son image
        """
        if self.alive:
            if not self.app.paused:
                self.changeImage()
            else:
                self.image = self.activeImages[0]
            self.image.render(screen, self.imageRect)
            screen.blit(self.text,self.textRect)
        else:
            if self.i < len(self.activeImages)*self.frequency - 1 :
                self.changeImage()
                self.image.render(screen, self.imageRect)
                screen.blit(self.text,self.textRect)
        
    def changeImage(self):
        """
        Player.changeImage() --> None
        Met à jour l'image à afficher 1 fois tous les quarts de seconde
        """
        self.i += 1
        if self.i >= len(self.activeImages)*self.frequency and self.alive:
            self.i = 0
        self.image = self.activeImages[int(self.i/self.frequency)]

    def bomb_up(self):
        """
        Player.bomb_up() --> None
        Augmente le nombre de bombes que le joueur peut poser s'il n'en a pas déjà 10 au maximum
        """
        if self.maxBombs < 10:
            self.bombsLeft += 1
            self.maxBombs += 1
    
    def speed_up(self):
        """
        Player.speed_up() --> None
        Augmente la vitesse du joueur s'il n'a pas déjà atteint la 2.5x la vitesse de base
        """
        if self.speed < 1.75*self.baseSpeed:
            self.speed += 0.125*self.baseSpeed
        
            # Si le joueur est déjà en mouvement, remise à jour de sa vitesse
            if self.speedX < 0:
                self.speedX -= 0.125*self.baseSpeed
            if self.speedX > 0:
                self.speedX += 0.125*self.baseSpeed
            
            if self.speedY < 0:
                self.speedY -= 0.125*self.baseSpeed
            if self.speedY > 0:
                self.speedY += 0.125*self.baseSpeed
    
    def range_up(self):
        """
        Player.range_up() --> None
        Augmente la portée des bombes du joueur, jusqu'à un maximum de 10
        """
        if self.explodeLength < 10:
            self.explodeLength += 1

    def resetPlayer(self):
        """ 
        Player.resetPlayer() --> None
        Réinitialise les propriétés du joueur
        """
        self.alive = 1
        self.setCoordsFromTiles(self.xTile, self.yTile)
        self.speedX, self.speedY = 0, 0
        self.activeImages = [self.renderedImages.get("down")[0]]
        self.image = self.activeImages[0]
        self.updateCoords(self.x,self.y)
        self.speed = self.baseSpeed
        self.maxBombs = 1
        self.bombsLeft = 1
        self.explodeLength = self.baseExplodeLength

    def destroy(self):
        """
        Player.destroy() --> None
        Déclenche la mort du joueur et son animation de mort
        """
        self.setImages("mort")
        self.alive = 0
        self.i = 0
        
class Bomb(pygame.sprite.Sprite):
    "Sprite d'une bombe"
    # Liste des sprites d'une bombe:
    bombSprites = []
    for i in range(1,5):
        bombSprites.append("./images/sprites/bomb/bomb"+str(i)+".png")
    
    def __init__(self, master, x, y, w, explodeLength):
        super().__init__()

        # Attributs d'instance de base:
        self.master = master
        self.app = master.app
        self.i = 0
        self.frequency = self.master.frequency
        self.stillOnBomb = 1 # vérifie si le joueur ayant posé la bombe est toujours dessus
        # Dimensions:
        self.x, self.y, self.w = x, y, w
        self.explodeLength = explodeLength

        # Images:
        self.images = []
        for elem in Bomb.bombSprites:
            self.images.append(Image(elem,w))
        
        self.image = self.images[0]
        self.rect = pygame.Rect(x,y,w,w)

        # Son:
        self.sound = pygame.mixer.Sound("./sounds/Explosion.wav")
        self.sound.set_volume(self.app.get_volume())

        # Gestion des flammes de l'explosion:
        self.fires = pygame.sprite.Group()
        self.exploded = 0

    def update(self, screen):
        """
        Bomb.update(pygame.Surface screen) --> None
        Gère la mise à jour de la bombe (dont son explosion) et l'affiche à l'écran
        """
        if self.exploded:
            if len(self.fires)>0:
                self.handleCollision()
                for fire in self.fires:
                    fire.update(screen)
            else:
                self.kill()
        else:
            self.changeImage()
            self.image.render(screen, self.rect)
            if self.i/self.app.fps>2:
                self.explode()
     
    def changeImage(self):
        """
        Bomb.changeImage() --> None
        Met à jour l'image à afficher 1 fois tous les quarts de seconde
        """
        self.i += 1
        self.image = self.images[int((self.i/self.frequency)%len(self.images))]
    
    def makeExplode(self):
        """
        Bomb.makeExplode() --> None
        Fait exploser la bombe après 0.25 secondes
        """
        # too lazy to create thread just for some simple wait so gonna use self.i instead with some math magic
        self.i = self.app.fps*1.75 # bing bong black magic hehe

    def explode(self):
        """
        Bomb.explode() --> None
        Active l'explosion de la bombe
        """
        self.sound.play()
        self.exploded = 1
        self.master.bombsLeft += 1
        self.fires.add(FlameCenter(self,self.app,self.x,self.y,self.w,self.explodeLength))

    def handleCollision(self):
        """
        Bomb.handleCollision() --> None
        Gère la collision des flammes avec les joueurs et les briques
        """
        if self.exploded and self.app.player: # Effectue ses actions seulement si l'application n'est pas en spectateur
            # Collision avec les joueurs:
            if not self.app.paused:
                if pygame.sprite.spritecollide(self.app.player,self.fires, False) and self.app.player.alive:
                    self.app.player.destroy()
                    if self.allPlayersDeadQ():
                        if self.master == self.app.player:
                            self.app.thread.send("all_dead:/")
                    else:
                        self.app.thread.send("player_death:/")
            # Collision avec les briques:
            for fire in self.fires:
                fire.handleCollision(self.app.plateau.allWalls, self.app.plateau.allPowerups, self.app.plateau.allBombs)

    def allPlayersDeadQ(self):
        """
        Bomb.allPlayersDeadQ() --> bool
        Regarde si tous les joueurs sont morts par l'explosion de cette bombe
        """
        deadPlayers = 0
        for player in self.app.allPlayers:
            if pygame.sprite.spritecollide(player,self.fires, False) or not player.alive:
                deadPlayers += 1
        if deadPlayers == len(self.app.players):
            return True
        else:
            return False
        
class FlameCenter(pygame.sprite.Sprite):
    "Centre de l'explosion d'une bombe"
        
    def __init__(self, bomb, app, x, y, w, explodeLength):
        super().__init__()
        
        # Attributs d'instance de base:
        self.bomb = bomb
        self.app = app
        self.frequency = app.fps/2/5 # Fréquence de changement d'image; la flamme reste 0.5 secondes à l'écran
        self.i = 0

        # Dimensions:
        self.x, self.y = x, y
        self.rect = pygame.Rect(x,y,w,w)

        # Images:
        self.images = []
        for imageString in Flame.fireSprites["center"]:
            self.images.append(Image(imageString, w))
        
        self.handleCollision(self.app.plateau.allWalls,self.app.plateau.allPowerups,self.app.plateau.allBombs)

        # Gestion des flammes sous-jacentes:
        for direction in ["left","right","up","down"]:
            bomb.fires.add(Flame(bomb,self.app,x,y,w,direction,explodeLength-1))
    
    def handleCollision(self, walls, powerups, bombs):
        """
        FlameCenter.handleCollision(pygame.sprite.Group walls, pygame.sprite.Group powerups, pygame.sprite.Group bombs) --> None
        Méthode ne servant qu'à permettre des simplifications dans le code; en effet, le centre apparaissant où la bombe était avant, elle n'aura aucune collision avec murs, bombes ou améliorations.
        """
        return None 

    def update(self, screen):
        """
        FlameCenter.update(pygame.Surface screen) --> None
        Affiche la flamme à l'écran et gère son extinction
        """
        self.changeImage()
        if self.i >= self.app.fps/2:
            self.kill()
        self.image.render(screen, self.rect)

    def changeImage(self):
        """
        FlameCenter.changeImage() --> None
        Gère la mise à jour de l'image
        """
        self.i += 1
        self.image = self.images[min(int(self.i/self.frequency),len(self.images)-1)]

class Flame(pygame.sprite.Sprite):
    "Sprite de la flamme générée par l'explosion"
    # Dictionnaire des sprites du feu
    fireSprites = {}
    for direction in listdir("./images/sprites/fire"):
        directionSprites = []
        for file in listdir("./images/sprites/fire"+"/"+direction):
            directionSprites.append("./images/sprites/fire"+"/"+direction+"/"+file)
        fireSprites[direction]=directionSprites

    def __init__(self, bomb, app, x, y, w, direction, explodeLength):
        super().__init__()
        
        # Attributs d'instance de base
        self.app = app
        self.frequency = app.fps/2/5 # Fréquence de changement d'image; la flamme reste 0.5 secondes à l'écran
        self.i = 0
        self.collided = 0
        # Dimensions
        #mise à jour des coordonnées par rapport à la direction:
        if direction in ["left","right"]:
            if direction == "left":
                x -= w
            else:
                x += w
        else:
            if direction == "up":
                y -= w
            else:
                y += w

        self.x, self.y = x, y
        self.rect = pygame.Rect(self.x,self.y,w,w)
        
        # Sprites:
        self.images = []

        if explodeLength == 0: # Bout de flamme
            for imageString in Flame.fireSprites[direction]:
                self.images.append(Image(imageString,w))
        
        elif direction in ["up","down"]: # Flamme verticale
            for imageString in Flame.fireSprites["vert"]:
                self.images.append(Image(imageString, w))
        
        else: # Flamme horizontale
            for imageString in Flame.fireSprites["hori"]:
                self.images.append(Image(imageString, w))
        
        # Détection des collisions:
        self.handleCollision(self.app.plateau.allWalls, self.app.plateau.allPowerups, self.app.plateau.allBombs)
        
        # Création récursive des flammes sous-jacentes
        if explodeLength > 0 and not self.collided:
            bomb.fires.add(Flame(bomb, self.app, self.x, self.y, w, direction, explodeLength-1))
            # Haha recursion go brrr
    
    def update(self, screen):
        """
        Flame.update(pygame.Surface screen) --> None
        Affiche la flamme à l'écran et génère son extinction
        """
        self.changeImage()
        if self.i >= self.app.fps/2:
            self.kill()
        if not self.collided:
            self.image.render(screen, self.rect)

    def changeImage(self):
        """
        Flame.changeImage() --> None
        Gère la mise à jour de l'image active
        """
        self.i += 1
        self.image = self.images[min(int(self.i/self.app.fps*2*len(self.images)),len(self.images)-1)]

    def handleCollision(self,walls, powerups, bombs):
        """
        Flame.handleCollision(pygame.sprite.Group walls, pygame.sprite.Group powerups, pygame.sprite.Group bombs) --> None
        Gère la collision du feu avec les murs, les bonus les bombes (faisant donc exploser celles-ci après un petit moment)
        """
        if walls:
            wallCollisions = pygame.sprite.spritecollide(self, walls, False)
            for collision in wallCollisions:
                collision.destroy()
                self.kill()
                self.collided = 1
        
        # Destruction des améliorations touchées:
        if powerups:
            pygame.sprite.spritecollide(self,powerups,True)

        if bombs:
            bombCollisions = pygame.sprite.spritecollide(self, bombs, False)
            for collision in bombCollisions:
                collision.makeExplode()
                self.kill()
                self.collided = 1
            




