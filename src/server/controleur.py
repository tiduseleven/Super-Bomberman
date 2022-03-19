# Contrôleur du serveur, gérant toute la partie logique

##########################
# Importation de modules #
##########################

import time 
from gestionSQL import *
import random, os

#########################
# Définition de classes #
#########################

class Timer(threading.Thread):
    """Thread gérant le minuteur de la partie"""
    def __init__(self, master, func, time = 2):
        super().__init__()
        self.master = master
        self.totalTime = time * 60 # Temps total à attendre, en secondes
        self.function = func # Fonction enclenchée à la fin
    def run(self):
        """
        Timer.run() --> None
        Attends le temps indiqué par self.totalTime en secondes puis arrête la partie si ce temps est dépassé
        """
        self.time = self.totalTime
        while self.master.get_timer_running() and self.time!=0:
            self.time-=1
            time.sleep(1)
        
        if self.time == 0:
            self.function()

class Controleur:
    "Contrôleur gérant l'administration de la partie et la gestion des fichiers"
    def __init__(self, master, librairie, joueursRequis = 2, temps = 2, victoires = 3):
        self.master = master
        self.gestionSQL = GestionSQL(librairie) # Connexion à la librairie SQL
        self.joueursRequis = joueursRequis # Nombre de joueurs requis pour commencer la partie
        self.requiredWins = victoires # Nombre de matchs gagnés requis pour terminer la partie
        self.maxTime = temps # Durée maximale d'un match en minutes
        self.settingsReceived = 0 # Témoin de réception des réglages, nécessaires pour commencer la partie
        self.timer_running = 1 # flag indiiquant si le minuteur doit toujours continuer.
        self.game_ongoing = 0 # flag indiquant si une partie est en jeu; empêche un joueur de se connecter si une partie se joue déjà

    def set_settings(self, options):
        """
        Controleur.set_settings(list options) --> None
        Met à jour les paramètres de la partie par rapport aux options (ordre: joueurs requis, temps max, matchs à gagner)
        """
        self.joueursRequis = int(options[0])
        self.maxTime = int(options[1])
        self.requiredWins = int(options[2])
        self.settingsReceived = 1

        # Vérif des conditions de début de la partie:
        if self.checkPlayers():
            self.initGame()

    def get_ingamePlayers(self):
        """
        Controleur.get_ingamePlayers() --> int
        Retourne le nombre de joueurs connectés au jeu
        """
        nPlayers = 0 # Compteur de joueurs en jeu
        for player in self.master.threads.values():
            if player.inGame:
                nPlayers +=1
        return nPlayers
        
    def get_bestPlayers(self):
        """
        Controleur.get_bestPlayers() --> list
        Retourne les 10 meilleurs joueurs de la base de donnée
        """
        return self.gestionSQL.get_bestPlayers()
    
    def get_podium(self):
        """
        Controleur.get_podium(self) --> list
        Retourne la liste des 3 meilleurs joueurs de la partie passée, contenant des tuples composés de leur score et leur pseudo
        """
        # création de la liste des joueurs en jeu:
        activePlayers = []
        for cle in self.master.threads:
            if self.master.threads[cle].inGame and not self.master.threads[cle].spectate:
                activePlayers.append(self.master.threads[cle])
        
        # Liste contenant le score et le pseudo des joueurs en jeu:
        infosList = []
        for player in activePlayers:
            infosList.append((player.currentScore, player.pseudo))
        
        # tri des joueurs:
        infosList.sort()
        infosList.reverse()
        
        # retour des joueurs:
        return infosList

    def get_player_data(self,pseudo):
        """
        Controleur.get_player_data(str pseudo) --> dict
        Retourne le pseudo, la position dans le classement, le score, le nombre de parties et de matchs gagnés du joueur au pseudo <pseudo>
        """
        return self.gestionSQL.get_player_data(pseudo)

    def get_timer_running(self):
        """
        Controleur.get_timer_running() --> int
        Retourne le flag indiquant si le minuteur est toujours activé
        """
        return self.timer_running

    def get_status(self):
        """
        Controleur.get_status() -> int
        Retourne le status du jeu
        """
        return self.game_ongoing

    def checkPlayers(self):
        """
        Controleur.checkPlayers() --> boolean
        Vérifie s'il y a assez de joueurs pour commencer la partie
        """
        nPlayers = self.get_ingamePlayers()
        if nPlayers >=  self.joueursRequis:
            return True
        else:
            return False
    
    def alreadyTakenQ(self, pseudo):
        """
        Controleur.alreadyTakenQ(str pseudo) --> bool
        Vérifie si le joueur au pseudo <pseudo> est déjà connecté sur une instance
        """
        for player in self.master.threads:
            if pseudo == self.master.threads[player].pseudo :
                return True

    def sendPlayers(self):
        """
        Controleur.sendPlayers() --> None
        Envoie la liste des joueurs présents aux différents clients en jeu
        """
        # Mise à jour du statut du jeu
        self.game_ongoing = 1

        inGamePlayers = []
        for cle in self.master.threads:
            if self.master.threads[cle].inGame:
                inGamePlayers.append(self.master.threads[cle].pseudo)
        # choix aléatoire de la position des joueurs:
        random.shuffle(inGamePlayers)
        chosenPlayers = inGamePlayers[:self.joueursRequis]
        
        # mise en vie / en spectateur des joueurs
        for cle in self.master.threads:
            if self.master.threads[cle].pseudo in chosenPlayers:
                self.master.threads[cle].spectate = 0
                self.master.threads[cle].alive = 1
            else:
                self.master.threads[cle].spectate = 1
                self.master.threads[cle].alive = 0

        # Création du message:
        message = "joueurs:"
        for pseudo in chosenPlayers:
            message+=pseudo+";"

        # Envoi du message:
        self.master.lock.acquire()
        for cle in self.master.threads:
            if self.master.threads[cle].inGame:
                self.master.threads[cle].connexion.send((message[:-1]+"/").encode("Utf8")) #[:-1] pour enlever le dernier ;
        self.master.lock.release()

    def sendDraw(self):
        """
        Controleur.sendDraw() --> None
        Envoie aux joueurs l'information d'une égalité
        """
        self.timer_running = 0
        msg = "match_fini:egalite:/"
        self.master.lock.acquire()
        for cle in self.master.threads:
            self.master.threads[cle].connexion.send(msg.encode("Utf8"))
        self.master.lock.release()
        self.engageNewMatch()

    def checkMatchEnding(self):
        """
        Controleur.checkMatchEnding() --> None
        Regarde si le match/la partie est finie à la mort d'un nouveau joueur et agit en conséquence
        """
        alivePlayers = {} #Dictionnaire des joueurs encore en vie
        partieFinie = 0

        for cle in self.master.threads:
            player = self.master.threads[cle]
            if player.inGame and player.alive:
                alivePlayers[cle] = player

        # Un joueur en vie --> vainqueur:
        if len(alivePlayers) == 1:
            self.timer_running = 0
            for cle in alivePlayers:
                player = alivePlayers[cle]

                # Mise à jour du score du joueur:
                player.currentMatchesWon+=1
                self.gestionSQL.winNewMatch(player.pseudo) # Mise à jour dans la base de données
                player.currentScore+=1

                # Vérification de fin de partie:
                if player.currentMatchesWon == self.requiredWins:
                    partieFinie = 1
                    winningPlayer = player
                    self.gestionSQL.winNewGame(player.pseudo) # Mise à jour dans la base de données
                    player.currentScore+=2
            
            if partieFinie :
                msg = "partie_finie:"
                self.game_ongoing = 0 # mise à jour du statut de la partie
                # création du podium:
                bestplayers = self.get_podium()
                for player in bestplayers:
                    msg+="{}-{};".format(player[1],player[0])
                msg = msg[:-1]+"/" # enlèvement du ; final et rajout du /
            else:
                    msg = "match_fini:"+player.pseudo+"/"
            
            # Envoi du message:
            if msg.split(":")[0] == "partie_finie":
                self.master.lock.acquire()
                for cle in self.master.threads:
                    self.master.threads[cle].connexion.send(("match_fini:"+winningPlayer.pseudo+"/").encode("Utf8"))
                self.master.lock.release()
                time.sleep(3)
            
                self.master.lock.acquire()
                for cle in self.master.threads:
                    self.master.threads[cle].connexion.send(msg.encode("Utf8"))
                self.master.lock.release()

                for cle in self.master.threads:
                    self.master.threads[cle].inGame = 0

            elif msg.split(":")[0] == "match_fini":
                self.master.lock.acquire()
                for cle in self.master.threads:
                    self.master.threads[cle].connexion.send(msg.encode("Utf8"))
                self.master.lock.release()
                self.engageNewMatch()
        
    def inscription(self, prenom, nom, pseudo, mdp):
        """
        Controleur.inscription(str pseudo, str nom, str prenom, str mdp) --> dict
        Gère l'inscription du joueur et lui retourne son pseudo
        """
        if not self.gestionSQL.get_players({"pseudo":pseudo}): # vérifie que le pseudo n'est pas déjà pris
            return self.gestionSQL.inscription(pseudo, nom, prenom, mdp)

    def connexion(self, pseudo, mdp):
        """
        Controleur.connexion(str pseudo, str mdp) --> dict
        Gère la connexion du joueur à son compte et retourne son pseudo s'il est bien inscrit dans la base de données
        """
        return self.gestionSQL.get_players({"pseudo":pseudo,"mdp":mdp}) # il ne peut pas y avoir plusieurs résultats car un joueur avec un pseudo déjà dans la base de données ne peut pas s'inscrire
    
    def engageNewMatch(self):
        """
        Controleur.engageNewMatch() --> None
        Gère le lancement d'une nouvelle partie
        """
        time.sleep(3) # Pause de 3 secondes
        
        """ Envoi du plateau de jeu """

        self.envoiPlateau(17,17)
        
        """ Début du match """
        for cle in self.master.threads:
            if not self.master.threads[cle].spectate:
                self.master.threads[cle].alive = 1 # Remise en vie des joueurs
        
        msg = "nouveau_match:/"
        self.master.lock.acquire()
        for cle in self.master.threads:
            self.master.threads[cle].connexion.send(msg.encode("Utf8"))
        self.master.lock.release()

        # Relance du minuteur:
        self.timer_running = 1
        Timer(self, lambda: self.stop_game(), self.maxTime).start()
    
    def stop_game(self):
        """
        Controleur.stop_game() --> None
        Arrête la partie quand le minuteur est écoulé
        """
        self.timer_running = 0
        msg = "match_fini:temps_ecoule:/"
        self.master.lock.acquire()
        for cle in self.master.threads:
            self.master.threads[cle].connexion.send(msg.encode("Utf8"))
        self.master.lock.release()
        self.engageNewMatch()

    def initGame(self):
        """
        Controleur.initGame() --> None
        Lancement d'une partie de jeu
        """

        """ Communication du plateau de jeu """
        
        self.envoiPlateau(17,17)

        """ Communication de la liste de joueurs """

        self.sendPlayers()
        
        """ Début du jeu """
        time.sleep(5)

        # Lancement du minuteur
        Timer(self, lambda: self.stop_game(), self.maxTime).start()

        # Envoi du début de partie:
        msg = "start_game:{}/".format(self.maxTime)
        self.master.lock.acquire()
        for cle in self.master.threads:
            self.master.threads[cle].connexion.send(msg.encode("Utf8"))
        self.master.lock.release()
    
    def envoiPlateau(self, w, h):
        """
        Controleur.envoiPlateau(int w, int h) --> None
        Crée et envoie le texte définissant le plateau aux joueurs
        """
        # création du plateau
        lines = []
        for j in range(h):
            line = []
            for i in range(w):
                if j in [0,h-1] or i in [0,w-1]: # Tour du plateau en blocs incassables
                    line.append(1)
                elif j in [1,h-2] and i in [1,w-2]: # Points d'apparitions aux coins du plateau
                    line.append(3)
                elif (j in [1,h-2] and i in [2,w-3]) or (j in [2,h-3] and i in [1,w-2]) : # Sols à côté du joueur, nécessaires pour que le joueur puisse se déplacer sans se tuer avec sa bombe
                    line.append(0)
                elif i%2 == 0 and j%2 == 0: # grille de blocs incassables
                    line.append(1)
                else :
                    line.append(random.choices([20,21,22,23,0],[6,1,2,2,10])[0]) # autres blocs entre sol et briques cassables (2x, avec x!=0 donnant une amélioration dans la brique: rangeup, bombup, speedup)
            lines.append(line)
        # Création du message:
        linesString = ""
        for line in lines:
            for case in line:
                linesString+=str(case)+","
            linesString = linesString[:-1]+";" # [:-1] pour enlever la dernière ,
        msg = "create_map:"+linesString[:-1]+"/" # [:-1] pour enlever le dernier ;
        
        # Envoi du plateau:
        self.master.lock.acquire()
        for cle in self.master.threads:
            self.master.threads[cle].connexion.send(msg.encode("Utf8"))
        self.master.lock.release()
