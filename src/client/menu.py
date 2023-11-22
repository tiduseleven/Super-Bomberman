# Menu principal du jeu

###########################
# Importation des modules #
###########################
import pygame
import sys

from variables import *
from objects import *
import game


##########################
# Définitions de classes #
##########################



class TableLine(object):
    """ Ligne apparaissant dans un tableau """
    def __init__(self,x,y,w,h,texts,color):
        # Attributs stylistiques:
        self.font = pygame.font.Font("freesansbold.ttf",round(h*0.8))
        self.textColor = color
        self.lineColor = colors["ORANGE"]

        # Grandeurs:
        self.linewidth = round(h/20)
        self.width = w

        # Objets:
        self.lines = [[(x,y),(x+w,y)],[(x,y+h),(x+w,y+h)]]
        self.textSurfaces = []
        self.textRects = []

        # Création des textes:
        for text,i in zip(texts,range(len(texts))):
            textSurface = self.font.render(text,True,self.textColor)
            self.textSurfaces.append(textSurface)
            textRect = textSurface.get_rect()
            textRect.x,textRect.y = x+w/len(texts)*i,y+h/10
            self.textRects.append(textRect)
    
    def render(self,screen):
        """
        TableLine.render(pygame.Surface screen) --> None
        Affiche la ligne du tableau à l'écran
        """
        for line in self.lines:
            pygame.draw.line(screen,self.lineColor,line[0],line[1],self.linewidth)
        for text,textRect in zip(self.textSurfaces,self.textRects):
            screen.blit(text,textRect)

class MainMenu(BasicScreen):
    """ Le menu principal du jeu """
    buttons = {
    "jouer":{"passive":"./images/menu/jouer.png","active":"./images/menu/jouer_hovering.png"},
    "classement":{"passive":"./images/menu/classement.png", "active":"./images/menu/classement_hovering.png"},
    "connexion":{"passive":"./images/menu/connexion.png", "active":"./images/menu/connexion_hovering.png"},
    "inscription":{"passive":"./images/menu/inscription.png", "active":"./images/menu/inscription_hovering.png"},
    "deconnexion":{"passive":"./images/menu/deconnexion.png", "active":"./images/menu/deconnexion_hovering.png"},
    "regles":{"passive":"./images/menu/regles.png", "active":"./images/menu/regles_hovering.png",},
    "commandes":{"passive":"./images/menu/commandes.png", "active":"./images/menu/commandes_hovering.png"},
    "quitter":{"passive":"./images/menu/quitter.png", "active":"./images/menu/quitter_hovering.png"},
    "audio":{"passive":"./images/menu/speaker_unmuted.png","active":"./images/menu/speaker_muted.png"}}
    titleImage = "./images/menu/title.png"
    def __init__ (self,master) :
        super().__init__(master)
        # Image titre du jeu:
        title = Image(MainMenu.titleImage,0.3*self.app.get_screenH())
        self.images.append(title)
        rect = title.get_rect()
        rect.center = self.app.get_screenW()/2,self.app.get_screenH()/4
        self.imageRects.append(rect)

        # Création des différents boutons:
        self.setButtons()

    def afficherPopUp(self, text = ""):
        """
        MainMenu.afficherPopUp() --> None
        Gère l'affichage d'un popup après que l'inscription est gérée
        """
        if text == "":
            if self.app.playerUsername:
                self.app.running = False
            else:
                self.popup=PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3),"Veuillez vous connecter d'abord!")
        else:
            self.popup = PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3),text)
    
    def setButtons(self):
        """
        MainMenu.setButtons() --> None
        Change les boutons affichés si le joueur est connecté ou non
        """
        self.buttons = []
        if self.app.playerUsername: # Le joueur est connecté --> affiche les boutons joueur, classement, déconnexion, règles, commandes, quitter avec leurs fonctions lambda associées
            for i,buttonName, func in zip(range(0,6),["jouer","classement","deconnexion","regles","commandes","quitter"],[lambda:self.askGameStatus(), lambda:self.app.classement.setActive(), lambda:self.handleDeconnexion(), lambda:self.app.regles.setActive(), lambda:self.app.commandes.setActive(), lambda:self.app.stop()]):
                self.buttons.append(Button(self,self.app.get_screenW()/2,self.app.get_screenH()/4+(i+3)*self.app.get_screenH()/15,0.05*self.app.get_screenH(),MainMenu.buttons[buttonName],func))
        else: # Le joueur n'est pas connecté --> affiche les boutons joueur, classement, connexion, inscription, règles, commandes, quitter avec leurs fonctions lambda associées
            for i,buttonName,func in zip(range(0,7),["jouer","classement","connexion","inscription","regles","commandes","quitter"],[lambda:self.askGameStatus(), lambda:self.app.classement.setActive(), lambda:self.app.connexion.setActive(), lambda:self.app.inscription.setActive(), lambda:self.app.regles.setActive(), lambda:self.app.commandes.setActive(), lambda:self.app.stop()]):
                self.buttons.append(Button(self,self.app.get_screenW()/2,self.app.get_screenH()/4+(i+3)*self.app.get_screenH()/15,0.05*self.app.get_screenH(),MainMenu.buttons[buttonName],func))

        # Bouton audio:
        self.buttons.append(AudioButton(self,self.app.get_screenH()*1/8,self.app.get_screenH()*7/8,self.app.get_screenH()*1/10,MainMenu.buttons["audio"],lambda volume: self.setVolume(volume)))

    def askGameStatus(self):
        """
        MainMenu.askGameStatus() --> None
        Demande au serveur le status du jeu; permet au joueur de rejoindre le jeu si la partie n'a pas encore commencé
        """
        self.app.thread.send("ask_status:/")

    def handleDeconnexion(self):
        """
        MainMenu.handleDeconnexion() --> None
        Gère la déconnexion du joueur, activée par un bouton
        """
        self.app.playerUsername = None
        self.setButtons()
        self.app.thread.send("deconnexion:/")
    
    def get_volume(self):
        """
        MainMenu.get_volume() --> int
        retourne le volume de l'application
        """
        return self.app.get_volume()

    def setVolume(self, volume):
        """
        MainMenu.setAudio(int volume) --> None
        Met à jour le volume des sons (n.b ne peut être que muet ou activé, c-à-d 0 ou 1)
        """
        self.app.setVolume(volume)

class Classement(BasicScreen):
    """ Ecran du classement des joueurs """
    def __init__(self, master):
        super().__init__(master)
        # Mise à jour de la liste des joueurs
        self.classementJoueurs = []
        self.tableLines = []
        # Bouton retour:
        self.buttons.append(Button(self,self.app.get_screenW()/8,self.app.get_screenH()/10*9,0.05*self.app.get_screenH(),BasicScreen.buttons["retour"], lambda: self.retour()))

    def updateClassement(self,players):
        """
        Classement.updateClassement(list players) --> None
        Met à jour le classement des joueurs
        """
        self.classementJoueurs = []
        for player in players:
            self.classementJoueurs.append(player)
        self.creerTableau()
       
    def creerTableau(self):
        """
        Classement.creerTableau() --> None
        Crée le tableau des 10 meilleurs joueurs, avec en-dessous les données du joueur connecté s'il n'est pas dans le top 10
        """
        self.tableLines = []
        # Ligne d'en-tête:
        self.tableLines.append(TableLine((self.app.get_screenW()-self.app.get_screenH()/3*5)/2,self.app.get_screenH()/10,self.app.get_screenH()/3*5,self.app.get_screenH()/20,["Place","Pseudo","Score","Matchs gagnés","Parties gagnées"],colors["LIGHTORANGE"]))
        
        flag = 0 # flag regardant si le joueur est déjà sur le tableau de classement
        i=0
        lastScore = 0
        lastPlace = i+1

        while i < min(10,len(self.classementJoueurs)):
            player = self.classementJoueurs[i]
            pseudo, score, matchGagnes, partiesGagnees = player.split(",")

            if self.app.playerUsername == None or pseudo != self.app.playerUsername: # Si ce n'est pas le joueur connecté:
                color = colors["ORANGE"]
            else: #Si c'est le joueur connecté:
                color = colors["LIGHTORANGE"]
                flag = 1
            if score == lastScore: # Egalité avec le joueur précédent
                place = lastPlace
            else:
                place = i+1
            self.tableLines.append(TableLine((self.app.get_screenW()-self.app.get_screenH()/3*5)/2,self.app.get_screenH()/10+self.app.get_screenH()/20*(i+1),self.app.get_screenH()/3*5,self.app.get_screenH()/20,[str(place),pseudo,score,matchGagnes,partiesGagnees],color))
            lastScore = score
            lastPlace = place
            i+=1
        
        # si le joueur est connecté et n'est pas dans les 10 premiers, demander au serveur les données du joueur
        if not flag and self.app.playerUsername:
            self.askPlayerPos()
        
    def setActive(self):
        """
        Classement.setActive() --> None
        Définit cet écran comme celui à afficher, et actualise le tableau
        """
        self.app.thread.send("classement:/")
        super().setActive()
    
    def render(self,screen):
        """
        Classement.render(screen) --> None
        Affiche le classement à l'écran
        """
        super().render(screen)
        for tableLine in self.tableLines:
            tableLine.render(screen)
    
    def drawPlayerTableLine(self,donnees):
        """
        Classement.drawPlayerTableline(str place) --> None
        Crée la ligne de tableau correspondant au joueur connecté; ne se passe que s'il n'est pas dans les 10 premiers
        """
        pseudo, score, matchsGagnes, partiesGagnees, place = donnees
        self.tableLines.append(TableLine((self.app.get_screenW()-self.app.get_screenH()/3*5)/2,self.app.get_screenH()/10+self.app.get_screenH()/20*(i+1),self.app.get_screenH()/3*5,self.app.get_screenH()/20,[place,pseudo,score,matchsGagnes,partiesGagnees],colors["LIGHTORANGE"]))
    def askPlayerPos(self):
        """
        Classement.askPlayerPos() --> None
        Demande au serveur la position dans le classement du joueur connecté
        """
        self.app.thread.send("get_player_pos:/")
    
class Connexion(BasicScreen):
    """ Menu gérant la connexion d'un joueur qui a déjà créé un compte """
    def __init__(self, master):
        super().__init__(master)

        # Bouton retour:
        self.buttons.append(Button(self,self.app.get_screenW()/7,self.app.get_screenH()/10*9,0.05*self.app.get_screenH(),BasicScreen.buttons["retour"], lambda: self.retour()))

        # Création des champs d'entrée:
        for text,i in zip(["Pseudo","Mot de passe"],range(0,2)):
            if i<1:
                self.inputFields.append(InputField(self,i,self.app.get_screenW()/6,self.app.get_screenH()/15*(i+2),self.app.get_screenH()/20*12,self.app.get_screenH()/20,[colors["ORANGE"],colors["LIGHTORANGE"]],12,text))
            else:
                self.inputFields.append(InputField(self,i,self.app.get_screenW()/6,self.app.get_screenH()/15*(i+2),self.app.get_screenH()/20*12,self.app.get_screenH()/20,[colors["ORANGE"],colors["LIGHTORANGE"]],12,text,censored=1))

        # Bouton de confirmation:
        self.buttons.append(Button(self,self.app.get_screenW()/7*6,self.app.get_screenH()/10*9, 0.05*self.app.get_screenH(),BasicScreen.buttons["confirmer"], lambda: self.sendMessage())) 
    
    def sendMessage(self):
        """
        Connexion.sendMessage() --> None
        Envoie une requête de connexion si tous les champs sont remplis, affiche un pop-up s'ils ne le sont pas tous
        """
        flag = 1 # flag vérifiant que tous les champs de texte sont remplis
        for inputField in self.inputFields:
            if inputField.text == "":
                flag = 0
        
        if flag == 0:
            self.popup=PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3),"Veuillez remplir tous les champs")
        else:
            self.app.thread.send("connexion:"+self.inputFields[0].text+","+self.inputFields[1].text+"/")
    
    def afficherPopUp(self):
        """
        Connexion.afficherPopUp() --> None
        Gère l'affichage d'un popup après que l'inscription est gérée
        """
        if self.app.playerUsername:
            self.popup=PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3),"Connecté avec succès!")
        else:
            self.popup=PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3), "Mot de passe ou pseudo incorrect!")

class Inscription(BasicScreen):
    """Menu gérant l'inscription du joueur"""
    def __init__(self,master):
        super().__init__(master)

        # Bouton retour:
        self.buttons.append(Button(self,self.app.get_screenW()/7,self.app.get_screenH()/10*9,0.05*self.app.get_screenH(),BasicScreen.buttons["retour"], lambda: self.retour()))

        # Création des champs d'entrée:
        for text,i in zip(["Prénom","Nom","Pseudo","Mot de passe","Confirmer le mot de passe"],range(0,5)):
            if i<3:
                self.inputFields.append(InputField(self,i,self.app.get_screenW()/6,self.app.get_screenH()/15*(i+2),self.app.get_screenH()/20*12,self.app.get_screenH()/20,[colors["ORANGE"],colors["LIGHTORANGE"]],12,text))
            else:
                self.inputFields.append(InputField(self,i,self.app.get_screenW()/6,self.app.get_screenH()/15*(i+2),self.app.get_screenH()/20*12,self.app.get_screenH()/20,[colors["ORANGE"],colors["LIGHTORANGE"]],12,text,censored=1))

        # Bouton de confirmation:
        self.buttons.append(Button(self,self.app.get_screenW()/7*6,self.app.get_screenH()/10*9, 0.05*self.app.get_screenH(),BasicScreen.buttons["confirmer"], lambda: self.sendMessage()))

    def sendMessage(self):
        """
        Inscription.sendInscription() --> None
        Envoie la requête d'inscription au serveur si les champs sont remplis et que les mots de passe sont les mêmes
        """
        flag = 1 # Flag vérifiant que tous les champs de texte sont remplis
        for inputField in self.inputFields:
            if inputField.text == "":
                flag = 0
        
        if flag == 0:
            self.popup=PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3),"Veuillez remplir tous les champs")
        elif self.inputFields[3].text != self.inputFields[4].text:
            self.popup=PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3),"La vérification ne correspond pas au mot de passe!")
        else :
            self.app.thread.send("inscription:"+self.inputFields[0].text+","+self.inputFields[1].text+","+self.inputFields[2].text+","+self.inputFields[3].text+"/")
    def afficherPopUp(self):
        """
        Inscription.afficherPopUp() --> None
        Gère l'affichage d'un popup après que l'inscription est gérée
        """
        if self.app.playerUsername:
            self.popup=PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3),"Compte créé avec succès!")
        else:
            self.popup=PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3), "Ce pseudonyme est déjà pris!")

class Regles(BasicScreen):
    """Menu affichant les règles de base du jeu"""
    
    texts = [
    "Chaque joueur apparaît à un coin du plateau.",
    "Chaque joueur possède une seule vie et une seule bombe au départ.",
    "Le but est de piéger l'autre joueur à l'aide de ses propres bombes.",
    "Les bombes peuvent casser les briques, mais pas les murs.",
    "Une fois qu'une brique est cassée, il est possible qu'elle fasse apparaître un bonus!",
    "Les bonus peuvent accélérer le joueur, lui fournir plus de bombe ou augmenter leur portée.",
    "Le jeu est chronométré: si le minuteur atteint 0, c'est égalité!",
    "Pour remporter une partie, il faut gagner un certain nombre de matchs. Celui-ci est défini avant la partie."
    ]

    def __init__(self, master):
        super().__init__(master)

        # Attributs d'instance:
        self.fontSize = round(self.app.get_screenH()/40)
        self.font = pygame.font.Font("freesansbold.ttf",self.fontSize)

        # Bouton retour:
        self.buttons.append(Button(self,self.app.get_screenW()/8,self.app.get_screenH()/10*9,0.05*self.app.get_screenH(),BasicScreen.buttons["retour"], lambda: self.retour()))

        # Création des différents textes:
        for text,i in zip(Regles.texts,range(0,len(Regles.texts))):
            # Indicateur de liste:
            text1 = self.font.render("•", True, colors["ORANGE"])
            text1Rect = text1.get_rect()
            text1Rect.x, text1Rect.y = self.app.get_screenW()/8, 1.5*self.fontSize*i+0.1*self.app.get_screenH()
            self.texts.append(text1)
            self.textRects.append(text1Rect)

            # Texte de la règle:
            text2 = self.font.render(text, True, colors["ORANGE"])
            text2Rect = text2.get_rect()
            text2Rect.x, text2Rect.y = self.app.get_screenW()/7, 1.5*self.fontSize*i+0.1*self.app.get_screenH()
            self.texts.append(text2)
            self.textRects.append(text2Rect)

class Commandes(BasicScreen):
    """Menu montrant au joueurs les différentes commandes du jeu"""
    controls = "./images/menu/controls.png"

    def __init__(self, master):
        super().__init__(master)

        # Attributs d'instance:
        self.fontSize = round(self.app.get_screenH()/30)
        self.font = pygame.font.Font("freesansbold.ttf",self.fontSize)

        # Bouton retour:
        self.buttons.append(Button(self,self.app.get_screenW()/8,self.app.get_screenH()/10*9,0.05*self.app.get_screenH(),BasicScreen.buttons["retour"], lambda: self.retour()))

        # Image montrant les commandes:
        self.images.append(Image(Commandes.controls,self.app.get_screenH()*2/3))
        rect = self.images[0].get_rect()
        rect.center = self.app.get_screenW()/2,self.app.get_screenH()/2
        self.imageRects.append(rect)

class Application(object):
    """Application principale gérant le menu"""

    def __init__(self, main, playerUsername=None):
        
        self.main = main
        self.app = self

        # Différents flags:
        self.running = True # Gestionnaire de la boucle principale de l'application
        self.paused = False # Si l'application principale est en pause ou non; mis à jour par la création d'un popup

        # Création de l'écran:
        flags = self.main.flags # modificateurs des propriétés de l'écran
        self.screenw, self.screenh, self.fps = self.main.get_screenW(), self.main.get_screenH(), self.main.get_fps() # données de l'écran + fréquence de rafraîchissement
        self.playerUsername = playerUsername # Pseudo du joueur, None s'il n'est pas encore connecté
        self.screen = pygame.display.set_mode((self.screenw, self.screenh), flags) # Ecran

        self.clock = pygame.time.Clock() # Horloge permettant de réguler le rafraîchissement de l'écran 
        self.currentScreen = None # Ecran actuemment affiché
        self.thread = self.main.thread # Thread client gérant les messages

        self.volume = self.main.get_volume() # Volume des sons

        # Création des menus:
        self.mainMenu = MainMenu(self)
        self.classement = Classement(self)
        self.connexion = Connexion(self)
        self.inscription = Inscription(self)
        self.regles = Regles(self)
        self.commandes = Commandes(self)
    
    def get_screenW(self):
        """
        Application.get_screenW() --> int
        Retourne la largeur de l'écran
        """
        return self.screenw
    
    def get_screenH(self):
        """
        Application.get_screenH() --> int
        Retourne la hauteur de l'écran
        """
        return self.screenh
    
    def get_volume(self):
        """
        Application.get_volume() --> int
        Retourne le volume de l'application
        """
        return self.volume

    def get_cursorPos(self):
        """
        Application.get_cursorPos() --> tuple
        Retourne la position du curseur
        """
        return self.cursorPos

    def get_app(self):
        """
        Application.get_app() --> Application
        Retourne l'application lancée actuellement, c-à-d self.app
        """
        return self.app

    def set_currentScreen(self, screen):
        """
        Application.set_currentScreen(screen, BasicScreen screen) --> None
        Affiche l'écran <screen>
        """
        self.currentScreen = screen

    def run(self):
        """
        Application.run() --> None
        Boucle principale de l'application
        """
        while self.running: # mis à False par l'appui du bouton Jouer ou Quitter
            
            # Remise à zéro de l'application:
            self.screen.fill(colors["DARKERGRAY"])

            # Mise à jour de la position du curseur:
            self.cursorPos = pygame.mouse.get_pos()

            # Gestion des événements par l'écran affiché
            self.currentScreen.handleEvents(pygame.event.get())
            
            # Affichage de l'écran actuel
            self.currentScreen.render(self.screen)
            pygame.display.update()

            self.clock.tick(self.fps)

        if self.main.running: # Dans le cas où le bouton Jouer est pressé et les conditions sont remplies, lancer la partie.
            self.main.app = game.Jeu(self.main, self.playerUsername)

    def start(self):
        """
        Application.start() --> None
        Lancement de la boucle principale de l'application
        """
        self.mainMenu.setActive()
        self.thread.set_app(self)
        self.run()
    
    def stop(self):
        """
        Application.quitter() --> None
        Gère l'initialisation de la fermeture de l'application
        """
        self.main.running = False
        self.running = False

    def handleServerStop(self):
        """
        Application.handleServerStop() --> None
        Gère l'arrêt abrupt du serveur
        """
        self.currentScreen.popup = PopUp(self, self.screenh/2, self.screenh/3,"Le serveur a été fermé. Le jeu doit être fermé", func = lambda:self.stop())

    def setVolume(self, volume):
        """
        Application.setVolume(int volume) --> None
        Met à jour le volume
        """
        self.main.setVolume(volume)
        self.volume = volume
        self.updateAllVolumes()
    
    def updateAllVolumes(self):
        """
        Application.updateAllVolumes() --> None
        Met à jour le volume des différents sons
        """
        for screen in [self.mainMenu, self.classement, self.connexion, self.inscription, self.regles, self.commandes]:
            for button in screen.buttons:
                button.sound.set_volume(self.volume)
        
    def handleMessage(self, msg):
        """
        Application.handleMessage(str msg) --> None
        Gestion de messages de l'application
        """
        msgList = msg.split(":")
        action = msgList[0]
        
        # Pseudo du joueur:
        if action == "player_username":
            pseudo = msgList[1]
            self.playerUsername = pseudo
            self.currentScreen.afficherPopUp()
        
        # Erreur à la connexion:
        elif action == "failed":
            self.playerUsername = None
            if msgList[1] == "alreadyconnected":
                self.currentScreen.set_popup("Ce joueur est déjà connecté!")
            else:
                self.currentScreen.afficherPopUp()
        
        # Réception du classement:
        elif action == "classement":
            players = msgList[1].split(";")
            self.classement.updateClassement(players)
        
        # Donnée du joueur connecté dans le classement:
        elif action == "donnees_joueur_classement":
            donnees = msgList[1].split(",")
            self.currentScreen.drawPlayerTableLine(donnees)
        
        elif action == "game_status":
            attribut = msgList[1]
            if attribut == "started":
                self.currentScreen.afficherPopUp("Une partie a déjà commencé!")
            else:
                self.currentScreen.afficherPopUp()
