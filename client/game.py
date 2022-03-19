# Boucle principale du jeu, gérant les joueurs et le plateau

###########################
# Importation des modules #
###########################

import pygame
from pygame.constants import *
import time
import threading

from mapmodule import Plateau
from variables import *
from player import Player
from objects import *
import menu
import client

##########################
# Définitions de classes #
##########################

class StartScreen(BasicScreen):
    " Ecran de début de partie "
    def __init__(self,master):
        super().__init__(master)
        self.configLines = [] # Lignes de l'écran de configuration
        self.fontSize, self.font = master.fontSize, master.font
        
    def setConfigUI(self):
        """
        StartScreen.setConfigUI() --> None
        Affiche l'écran de configuration pour le premier joueur qui s'est connecté
        """
        self.reset()
        texts = ["Nombre de joueurs", "Durée", "Matchs gagnants"]
        options = [["2","3","4"],["1:00","2:00","3:00","4:00","5:00"],["1","2","3","4","5"]]
        for i, text, opts in zip(range(0,len(texts)), texts, options):
            self.configLines.append(ConfigLine(self, self.app.get_screenW()*1/8,self.app.get_screenH()*(2+i)/8,self.app.get_screenW()*6/8,self.app.get_screenH()*1/10,text,opts))
        
        # Bouton de confirmation:
        self.buttons.append(Button(self,self.app.get_screenW()/8*7,self.app.get_screenH()/10*9,0.05*self.app.get_screenH(),BasicScreen.buttons["confirmer"], lambda:self.confirmer()))
        # Bouton retour:
        self.set_menu_button()

    def setWaitingSettingsUI(self):
        """
        StartScreen.setWaitingSettingsUI() --> None
        Affiche l'écran d'attente des réglages faits par le premier joueur connecté
        """
        self.reset()
        self.paragraphs.append(Paragraph(self.app.get_screenW()/2,self.app.get_screenH()/2,"En attente de configuration de la partie...","freesansbold.ttf", self.fontSize, colors["ORANGE"],self.app.get_screenW()/2))
        # Bouton retour:
        self.set_menu_button()

    def setWaitingPlayersUI(self):
        """
        StartScreen.setwaitingPlayersUI() --> None
        Affiche l'écran d'attente des joueurs nécessaires
        """
        self.reset()
        text = self.font.render("En attente des autres joueurs...", True, colors["ORANGE"])
        textRect = text.get_rect()
        textRect.center = self.app.get_screenW()/2, self.app.get_screenH()/2
        self.texts.append(text)
        self.textRects.append(textRect)
        # Bouton retour:
        self.set_menu_button()

    def setPlayerText(self, color):
        """
        StartScreen.setPlayerText(str color) --> None
        Affiche le texte indiquant la couleur du joueur
        """
        self.reset()
        text = self.font.render("Vous êtes le joueur "+color+".",True,colors["ORANGE"])
        textRect = text.get_rect()
        textRect.center = self.app.get_screenW()/2, self.app.get_screenH()/2
        self.texts.append(text)
        self.textRects.append(textRect)

    def setSpectatorText(self):
        """
        StartScreen.setSpectatortText() --> None
        Affiche le texte indiquant que le joueur connecté sera spectateur
        """
        self.reset()
        text = self.font.render("Vous êtes spectateur.", True, colors["ORANGE"])
        textRect = text.get_rect()
        textRect.center = self.app.get_screenW()/2, self.app.get_screenH()/2
        self.texts.append(text)
        self.textRects.append(textRect)

    def set_menu_button(self):
        """
        StartScreen.set_menu_button() --> None
        Ajoute le bouton menu à l'écran
        """
        self.buttons.append(Button(self,self.app.get_screenW()/8,self.app.get_screenH()/10*9,0.05*self.app.get_screenH(),Jeu.buttons["menu"],lambda:self.app.quitter()))

    def reset(self):
        """
        StartScreen.reset() --> None
        Remet à zéro l'affichage de l'écran
        """
        super().reset()
        self.configLines = []

    def confirmer(self):
        """
        StartScreen.confirmer() --> None
        Envoie le message de confirmation des réglages au serveur
        """
        msg = "settings:"
        for config in self.configLines:
            msg+=config.get_chosenOption()[0]+";"
        msg = msg[:-1]+"/"
        self.app.thread.send(msg)

    def render(self, screen):
        """
        StartScreen.render(pygame.Surface screen) --> None
        Affiche le menu à l'écran
        """
        for configLine in self.configLines:
            configLine.render(screen)
        super().render(screen)

    def handleEvents(self, events):
        """
        StartScreen.handleEvents(pygame.Eventlist events) --> None
        Gère les événements transmis
        """
        if self.popup:
            self.popup.handleEvents(events)
        else:
            cursor = pygame.mouse.get_pos()
            for event in events:
                for button in self.buttons:
                    button.detectCursor(cursor)
                    button.handleEvent(event)
                for configLine in self.configLines:
                    for button in configLine.buttons:
                        button.detectCursor(cursor)
                        button.handleEvent(event)

class EndScreen(BasicScreen):
    " Ecran de fin de partie "
    
    def __init__(self, master):
        super().__init__(master)
        self.font = self.master.font
        # Texte de partie terminée:
        text = self.font.render("Partie terminée!", True, colors["ORANGE"])
        textRect = text.get_rect()
        self.texts.append(text)
        self.textRects.append(textRect)

        # Boutons:
        self.buttons.append(Button(self,self.app.get_screenW()/8,self.app.get_screenH()/10*9,0.05*self.app.get_screenH(),Jeu.buttons["menu"],lambda:self.app.quitter()))
        self.buttons.append(Button(self,self.app.get_screenW()/8*7,self.app.get_screenH()/10*9,0.05*self.app.get_screenH(),Jeu.buttons["rejouer"], lambda:self.askGameStatus()))
    
    def afficherPopUp(self, text = ""):
        """
        EndScreen.afficherPopUp() --> None
        Gère l'affichage d'un popup
        """
        self.popup = PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3),text, func = lambda:self.removePopUp())
    
    def removePopUp(self):
        """
        EndScreen.removePopUp() --> None
        Enlève la fenêtre intempestive
        """
        self.popup = []

    def placeTexts(self):
        """
        EndScreen.placeTexts() --> None
        Place les textes sur l'écran de manière centrée
        """
        for i in range(len(self.texts)):
            self.textRects[i].center = self.app.get_screenW()/2, self.app.get_screenH()/2 + ((1-len(self.texts))/2+i)*self.app.fontSize*1.5

    def askGameStatus(self):
        """
        EndSCreen.askGameStatus() --> None
        Demande au serveur le status du jeu; permet au joueur de rejouer le jeu si la partie n'a pas encore commencé
        """
        self.app.thread.send("ask_status:/")

    def showPodium(self, joueurs):
        """
        EndScreen.showPodium(list joueurs) --> None
        Affiche le podium des meilleurs joueurs avec leurs scores respectifs pour la partie
        """
        # Suppression de tous les textes sauf le texte d'entête:
        del(self.texts[1:])
        del(self.textRects[1:])
        # Création des nouveaux textes:
        for place,player in zip(["Vainqueur","Deuxième","Troisième","Dernier"],joueurs):
            text = self.font.render("{}: {} avec {} points!".format(place,player[0],player[1]), True, colors["ORANGE"])
            textRect = text.get_rect()
            self.texts.append(text)
            self.textRects.append(textRect)
        # Placement des textes:
        self.placeTexts()

class Timer:
    " Chronomètre montrant le temps restant dans la partie "
    def __init__(self, master, x, y, font, time=2):
        self.master = master
        self.font = font
        self.initialTime = time
        self.minutesLeft = time
        self.secondsLeft = 0
        self.i = 0 # compteur d'images passées
        self.updateText()
        self.textRect = self.text.get_rect()
        self.textRect.center = x, y
    
    def reset(self):
        """
        Timer.reset() --> None
        Remise à zéro du timer
        """
        self.minutesLeft = self.initialTime
        self.secondsLeft = 0
        self.updateText()

    def set_maxtime(self, temps):
        """
        Timer.set_maxtime(int temps) --> None
        Change le temps maximal du minuteur
        """
        self.initialTime = temps
        self.reset()

    def update(self):
        """
        Timer.countDown() --> None
        Gère la mise à jour du temps restant
        """
        if self.i < self.master.fps:
            self.i+=1
        else:
            self.i = 0
            if self.secondsLeft == 0:
                if self.minutesLeft > 0:
                    self.minutesLeft -= 1
                    self.secondsLeft = 59
            else:
                self.secondsLeft -=1
            self.updateText()
        
    def updateText(self):
        """
        Timer.updateTexts() --> None
        Met à jour les textes par rapport au temps restant
        """
        # Formatage du texte des secondes
        if self.secondsLeft < 10:
            secondsText = "0"+str(self.secondsLeft)
        else:
            secondsText = str(self.secondsLeft)
        
        self.text = self.font.render("{}:{}".format("0"+str(self.minutesLeft),secondsText),True,colors["ORANGE"])

    def render(self, screen) :
        """
        Timer.render(pygame.Surface screen) --> None
        Affiche le chronomètre à l'écran
        """
        screen.blit(self.text, self.textRect)

class PlayerScoreText:
    " Affichage du score actuel du joueur "
    def __init__(self, x, y, h, side, pseudo, score=0):
        # Eléments de positionnement
        self.x, self.y, self.h = x, y, h
        self.side = side # left ou right, les textes à droite affiche le score à gauche du pseudo
        
        # score du joueur
        self.score = score
        # Police d'affichage
        self.font = pygame.font.Font("freesansbold.ttf",self.h)

        # Création des textes:
        self.playerText = self.font.render(pseudo,True,colors["ORANGE"])
        self.playerTextRect = self.playerText.get_rect()
        self.scoreText = self.font.render(str(score),True,colors["ORANGE"])
        self.scoreTextRect = self.scoreText.get_rect()

        # Distinction gauche et droite pour les positionnements:
        if self.side == "right":
            # pseudo du joueur tout à droite; x est dans ce cas donné pour le côté droite du positionnement
            self.playerTextRect.right = x - h/3
            #  score à côté
            self.scoreTextRect.right = self.playerTextRect.left - h/3
        else:
            # pseudo du joueur tout à gauche; x est dans ce cas donné pour le côté gauche du positionnement
            self.playerTextRect.left = x + h/3
            # score à côté
            self.scoreTextRect.left = self.playerTextRect.right + h/3
        
        # Coordonnée verticale:
        self.playerTextRect.centery = y
        self.scoreTextRect.centery = self.playerTextRect.centery
    
    def updateScore(self):
        """
        PlayerScoreText.updateScore() --> None
        Met à jour le score du joueur
        """
        self.score += 1
        self.scoreText = self.font.render(str(self.score),True,colors["ORANGE"])

    def render(self, screen):
        """
        PlayerScoreText.render(pygame.Surface screen) --> None
        Affiche les textes à l'écran
        """
        screen.blit(self.playerText, self.playerTextRect)
        screen.blit(self.scoreText, self.scoreTextRect)

class Jeu(object):
    """Application principale gérant le jeu"""
    buttons = {"menu":{"passive":"./images/menu/menu.png", "active":"./images/menu/menu_hovering.png"},
        "rejouer":{"passive":"./images/menu/rejouer.png", "active":"./images/menu/rejouer_hovering.png"}
        }
    
    def __init__(self, main, username):
        
        self.main = main
        self.app = self
        self.volume = self.main.get_volume() # volume de l'application
        # Création de l'écran:
        flags = self.main.flags
        self.screenw, self.screenh, self.fps = self.main.get_screenW(), self.main.get_screenH(), self.main.get_fps()
        self.tileSize = round(self.screenh/20)
        self.screen = pygame.display.set_mode((self.screenw, self.screenh), flags)

        # Attributs d'instance:
        self.running = True # Flag de la boucle principale; mis à False par la méthode Jeu.stop()
        self.ingame = 0 # Flag de la partie elle-même; mis à 1 par les messages start_game et nouveau_match; remis à 0 par le message partie_finie
        self.paused = 1 # Flag gérant la pause du jeu (c-à-d pendant les fins de matchs et avant que la partie ait commencé); mis à 0 par les messages start_game et nouveau_match; remis à 1 par match_fini
        self.clock = pygame.time.Clock()
        self.pseudo = username
        self.players = {} # dict répertoriant les joueurs, permettant d'accéder aux joueurs différents facilement
        self.player = None # sprite du joueur connecté sur cette instance du jeu
        self.allPlayers = pygame.sprite.Group()
        
        # Mise en place du texte de fin de match:
        self.fontSize = round(self.screenh/20)
        self.font = pygame.font.Font("freesansbold.ttf",self.fontSize)
        self.text = None
        self.textRect = None

        # Eléments graphiques:
        self.startScreen = StartScreen(self)                                # écran initial
        self.endScreen = EndScreen(self)                                    # écran final
        self.plateau = Plateau(self,w = self.tileSize*17, h = self.tileSize*17) # plateau de jeu
        self.frame = pygame.Surface((self.tileSize*19,self.tileSize*19))    # cadre du plateau
        self.frame.fill(colors["DARKGRAY"])
        self.frameRect = pygame.Rect(self.screenw/2-self.tileSize*9.5, self.screenh/2-self.tileSize*9.5, self.tileSize*19, self.tileSize*19)
        self.popup = [] # Fenêtre intempestive qui apparaît si un joueur se déconnecte abruptement durant la partie
        self.timer = Timer(self, self.screenw/2, self.screenh/2-self.tileSize*9, self.font) #Affichage du minuteur
        self. playerScores = {} # Affichage des scores des joueurs avec leur pseudo

        # Gestion serveur:
        self.thread = self.main.thread

        # Sons:
        self.waitingSong = pygame.mixer.Sound("./sounds/WaitingSong.wav")
        self.gamemusic = pygame.mixer.Sound("./sounds/GameSong.wav")
        self.endScreenMusic = {"vainqueur":pygame.mixer.Sound("./sounds/EndingWinnerSong.wav"), "pasVainqueur":pygame.mixer.Sound("./sounds/EndingNotWinnerSong.wav")}

        # Mise à jour du volume:
        self.waitingSong.set_volume(self.volume)
        self.gamemusic.set_volume(self.volume)
        for music in self.endScreenMusic:
            self.endScreenMusic[music].set_volume(self.volume)

    def get_cursorPos(self):
        """
        Jeu.get_cursorPos() --> tuple
        Retourne la position de la souris
        """
        return pygame.mouse.get_pos()

    def get_screenW(self):
        """
        Jeu.get_screenW() --> int
        Retourne la largeur de l'écran
        """
        return self.screenw
    
    def get_screenH(self):
        """
        Jeu.get_screenH() --> int
        Retourne la hauteur de l'écran
        """
        return self.screenh
    
    def get_volume(self):
        """
        Jeu.get_volume() --> int
        Retourne le volume de l'application
        """
        return self.volume

    def get_tileSize(self):
        """
        Jeu.get_tileSize() --> int
        Retourne la taille d'une case
        """
        return self.tileSize

    def get_players(self):
        """
        Jeu.get_players() --> pygame.sprite.Group
        Retourne le groupe de sprite des joueurs
        """
        return self.allPlayers

    def get_app(self):
        """
        jeu.get_app() --> Application
        Retourne l'application lancée actuellement, c-à-d self.app
        """
        return self.app
        
    def run(self):
        """
        Jeu.run() --> None
        Boucle principale de l'application
        """
        
        while self.running:
            """ Partie principale """
            # Remise à zéro de l'application:
            self.screen.fill(colors["DARKERGRAY"])
            if self.ingame:

                # Gestion des événements
                if self.popup:
                    self.popup.handleEvents(pygame.event.get())
                else:
                    if not self.paused:
                        for event in pygame.event.get():
                            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                                self.abrupt_quit()
                            elif self.player:   
                                self.player.handleEvent(event)
                        # Mise à jour du minuteur:
                        self.timer.update()
                
                # Déplacement des joueurs:
                for joueur in self.allPlayers:
                    if not self.paused:
                        joueur.move(self.plateau.allWalls, self.plateau.allBombs)

                """ Affichage des éléments graphiques """
                
                # Affichage du cadre:
                self.screen.blit(self.frame,self.frameRect)
                # Mise à jour du plateau et affichage:
                self.plateau.update(self.screen)

                # Affichage des joueurs:
                for joueur in self.allPlayers:
                    joueur.render(self.screen)
                
                # Affichage du chronomètre:
                self.timer.render(self.screen)

                # Affichage des scores des joueurs:
                for cle in self.playerScores:
                    self.playerScores[cle].render(self.screen)

                # Texte de fin de match:
                if self.paused:
                    for event in pygame.event.get():
                        if event.type == QUIT:
                            self.running = False
                    self.screen.blit(self.text, self.textRect)
                
                # Affichage du popup s'il y en a un:
                if self.popup:
                    self.popup.render(self.screen)
               
                """ Ecran d'attente """
            
            elif self.paused:
                self.startScreen.handleEvents(pygame.event.get())
                self.startScreen.render(self.screen)
                
            
                """ Ecran de fin """
            
            else:
                self.endScreen.handleEvents(pygame.event.get())
                self.endScreen.render(self.screen)
            
            self.clock.tick(self.fps)
            pygame.display.update()
        
        try:
            self.thread.send("player_outgame:/")
        except:
            pass
        self.main.app = menu.Application(self.main,self.pseudo)

    def start(self):
        """
        Jeu.start()
        Lancement de la boucle principale de l'application
        """
        self.thread.app = self
        self.thread.send("player_ingame:/")
        self.waitingSong.play(loops=-1)
        self.run()

    def restart(self):
        """
        Jeu.restart() --> None
        Remise à zéro du jeu et relancement de la boucle principale
        """
        pygame.mixer.stop()
        # Remise à zéro des attributs changés:
        self.paused = 1
        self.players = {}
        self.player = None
        self.allPlayers.empty()
        self.playerScores = {}
        # Communication au serveur:
        self.thread.send("player_replay:/")
        self.waitingSong.play(loops=-1)
    
    def abrupt_quit(self):
        """
        Jeu.abrupt_quit() --> None
        Arrête la partie abruptement et renvoie le joueur au menu
        """
        self.thread.send("abrupt_quit:/")
        self.running = 0

    def stop(self):
        """
        Jeu.stop() --> None
        Met fin à l'application
        """
        self.running = 0
        self.main.running = 0

    def handleServerStop(self):
        """
        Jeu.handleServerStop() --> None
        Gère la fin du serveur en affichant un popup
        """
        popup = PopUp(self,self.screenh/2,self.screenh/3,"Le serveur a été fermé. Le jeu doit être fermé.", func = lambda:self.stop())
        if self.ingame:
            self.popup = popup
        elif self.paused:
            self.startScreen.popup = popup
        else:
            self.endScreen.popup = popup
    def quitter(self):
        """
        Jeu.quitter() --> None
        Gère le retour à l'écran de menu
        """
        self.running = 0
        pygame.mixer.stop()

    def handleMessage(self, msg):
        """
        Jeu.handleMessage(str msg) --> None
        Gestion des messages reçus
        """

        msgList = msg.split(":")
        action = msgList[0]

        """ Gestion de partie """

        # Affichage de l'écran de configuration:
        if action == "configPlayer":
            self.startScreen.setConfigUI()
        
        # Affichage de l'écran d'attente des réglages:
        elif action == "waitingForSettings":
            self.startScreen.setWaitingSettingsUI()

        # Affichage de l'écran d'attente de joueurs:
        elif action == "waitingForPlayers":
            self.startScreen.setWaitingPlayersUI()
        
        # Affichage d'un popup si le jeu a déjà commencé
        elif action == "game_status":
            attribut = msgList[1]
            if attribut == "started":
                self.endScreen.afficherPopUp("Une partie a déjà commencé!")
            else:
                self.restart()
            """ Avant le début de la partie """
        # Création du plateau:
        elif action == "create_map":
            lines = msgList[1].split(";")
            self.plateau.createTiles(lines)

        # Ajout des joueurs au début de la partie:
        elif action == "joueurs":
            attributs = msgList[1]
            joueurs = attributs.split(";")
            couleurs = ["blanc","noir","rouge","bleu"]
            textX = [self.frameRect.left, self.frameRect.right] #coordonnées X des textes de score
            textY = [self.screenh/2-self.tileSize*9, self.screenh/2+self.tileSize*9] #coordonnées Y des textes de score
            # Création des combinaisons
            textCoords = []
            for y in textY:
                for x in textX:
                    textCoords.append((x,y))
            # côté de positionnement du texte:
            sides = ["left","right"]

            for i,pseudo,color in zip(range(0,len(joueurs)),joueurs, couleurs):
                xTile, yTile = self.plateau.playerSpawns[(i*3)%4]
                joueur = Player(self, pseudo, xTile, yTile, 0.9*self.tileSize, 0.9*self.tileSize*3/2, self.tileSize/self.fps*3, Player.playerSprites["player"+str(len(self.players)+1)])
                if pseudo == self.pseudo:
                    self.player = joueur
                    self.color = color
                    self.players[pseudo] = self.player
                    self.allPlayers.add(self.player)
                else: # autre joueur:
                    self.players[pseudo] = joueur
                    self.allPlayers.add(joueur)
                #Placement du texte de score:
                coords = textCoords[(i*3)%4]
                side = sides[i%2]
                self.playerScores[pseudo]=PlayerScoreText(coords[0],coords[1],round(self.fontSize*2/3),side,pseudo)

            # changement du texte d'attente pour montrer au joueur qui il est:
            self.waitingSong.stop()
            if self.player:
                self.startScreen.setPlayerText(self.color)
            else:
                self.startScreen.setSpectatorText()

        # Lancement du jeu:
        elif action == "start_game":
            if self.paused: # si le jeu n'est pas en pause, alors le joueur est sur l'écran final --> ne rien faire
                temps = int(msgList[1])
                self.timer.set_maxtime(temps)
                self.paused = 0
                self.ingame = 1
                self.gamemusic.play(loops=-1)
                """ Durant la partie """
        elif self.ingame:
            # Début d'un nouveau match:
            if action == "nouveau_match":
                self.gamemusic.play(loops=-1)
                for player in self.players:
                    self.players[player].resetPlayer()
                self.paused = 0
                self.ingame = 1
                self.timer.reset()
            
            # Fin d'un match:
            elif action == "match_fini":
                attribut = msgList[1]
                self.gamemusic.stop()
                self.timer.running = 0
                # Remise à zéro des textes et de leurs rectangles:
                if attribut == "egalite":
                    self.text = self.font.render("Egalité!",True, colors["ORANGE"],colors["DARKERGRAY"])
                    # Mort des joueurs encore en vie autres que le joueur de la partie:
                    for player in self.allPlayers:
                        if player != self.player and player.alive:
                            player.destroy()
                elif attribut == "temps_ecoule":
                    self.text = self.font.render("Egalité: temps écoulé!", True, colors["ORANGE"],colors["DARKERGRAY"])
                else:
                    self.text = self.font.render("Match gagné par "+attribut,True, colors["ORANGE"],colors["DARKERGRAY"])
                    self.playerScores[attribut].updateScore()
                self.textRect = self.text.get_rect()
                self.textRect.center = self.screenw/2, self.screenh/2
                self.paused = 1

            # Fin d'une partie:
            elif action == "partie_finie":
                attribut = msgList[1]
                meilleurs = attribut.split(";")
                meilleursList = []
                for joueur in meilleurs:
                    meilleursList.append(joueur.split("-"))
                
                self.gamemusic.stop()
                self.paused = 0
                self.ingame = 0
                texts = ["Partie terminée!"]
                self.endScreen.showPodium(meilleursList)
                for place,joueur in zip(["Vainqueur","Deuxième","Troisième","Dernier"],meilleursList):
                    texts.append("{}: {} avec {} points!".format(place,joueur[0],joueur[1]))
                # Remise à zéro des textes et de leurs rectangles:
                self.texts = []
                self.textRects = []
                for i,text in zip(range(0,len(texts)),texts):
                    self.texts.append(self.font.render(text, True, colors["ORANGE"]))
                    self.textRects.append(self.texts[i].get_rect())
                    self.textRects[i].center = self.screenw/2, self.screenh/2 + ((1-len(texts))/2+i)*self.fontSize*1.5
                # musique de l'écran de fin:
                if meilleursList[0][0]== self.pseudo:
                    self.endScreenMusic["vainqueur"].play()
                else:
                    self.endScreenMusic["pasVainqueur"].play()
            # Déconnexion abrupte d'un joueur:
            elif action == "abrupt_quit":
                pseudo = msgList[1]
                self.popup = PopUp(self, round(self.app.get_screenH()*2/3),round(self.app.get_screenH()/3),"Le joueur {} s'est déconnecté durant la partie! Vous allez être renvoyé au menu.".format(pseudo), func = lambda: self.quitter())
            
                """ Gestion d'actions """

            # Début du mouvement d'un joueur et synchronisation des coordonnées de celui-ci:
            elif action == "start_move":
                attributs = msgList[1].split(",")
                pseudo = attributs[0]
                direction = attributs[1]

                # Mise à jour des coordonnées:
                xTile, yTile = float(attributs[2]), float(attributs[3])
                self.players[pseudo].setCoordsFromTiles(xTile,yTile)

                # Début du mouvement:
                self.players[pseudo].startMove(direction)
            
            # Fin du mouvement d'un joueur et synchronisation des coordonnnées de celui-ci:
            elif action == "stop_move":
                attributs = msgList[1].split(",")
                pseudo = attributs[0]
                direction = attributs[1]

                # Mise à jour des coordonnées:
                xTile, yTile = float(attributs[2]), float(attributs[3])
                self.players[pseudo].setCoordsFromTiles(xTile,yTile)

                # Fin du mouvement:
                self.players[pseudo].stopMove(direction)

            # Pose d'une bombe:
            elif action == "drop_bomb":
                
                attributs = msgList[1].split(",")
                pseudo = attributs[0]
                xTile, yTile = int(attributs[1]), int(attributs[2])
                self.players[pseudo].dropBomb(xTile, yTile)

            # Mort d'un joueur
            elif action == "player_death":
                pseudo = msgList[1]
                self.players[pseudo].destroy()

            