# Définition d'un serveur réseau gérant la communication entre les différents joueurs de Super Bomberman.
# Utilise les threads pour gérer les connexions clientes en parallèle.
 
# Tiré en grande partie du script "Communications à travers un réseau et multithreading"

##########################
# Importation de modules #
##########################

import socket, sys, threading, time, random
from controleur import *

#########################
# Définition de classes #
#########################

class ThreadClient(threading.Thread):
    """dérivation d'un objet thread pour gérer la connexion avec un client"""
    def __init__(self, main, conn):
        super().__init__()
        self.main = main 
        self.connexion = conn # Connexion serveur
        self.pseudo = None # Pseudo du joueur
        self.running = 1 # flag de la boucle du thread
        self.inGame = 0 # flag vérifiant si le joueur est en jeu ou non; modifié lors de la réception d'un message "player_ingame"
        self.currentScore = 0 #score actuel du joueur durant la partie en cours
        self.currentMatchesWon = 0 #matchs gagnés par le joueur pendant cette partie
        self.alive = 0 #flag vérifiant si le joueur est toujours en vie
        self.spectate = 0 #flag indiquant si le joueur est un spectateur, c-à-d s'il n'a pas d'impact sur la partie mais qu'il la regarde.
        self.gameAdmin = 0 #si le joueur est celui qui gère les réglages
    def run(self):
        """
        ThreadClient.run() --> None
        Boucle principale du thread gérant la réception et l'envoi de messages
        """
        # Dialogue avec le client :
        nom = self.getName()	    # Chaque thread possède un nom
        while self.running:
            try:
                msgClient = self.connexion.recv(1024).decode("Utf8")
            except: # fermeture abrupte de la connexion
                break
            print(nom+":"+msgClient)
            if not msgClient or msgClient.upper() =="FIN":
                    break
            
            messages = msgClient[:-1].split("/") #[:-1] pour enlever le dernier /

            for msgClient in messages:
                l = msgClient.split(":")
                action, attributs = l

                "Gestion dans le menu"
                
                # Connexion du client:
                if action == "client OK":
                    continue
                               
                elif action in ["inscription","connexion","classement","get_player_pos","ask_status"]: # commandes n'impactant que le joueur les envoyant
                     # Gestion d'inscription:
                    if action == "inscription":
                        attributsList = attributs.split(",")
                        self.pseudo = self.main.controleur.inscription(attributsList[0], attributsList[1], attributsList[2], attributsList[3]) # dans l'ordre: prénom, nom, pseudo, mot de passe;
                        if self.pseudo: # Joueur inscrit avec succès:
                            msg = "player_username:" + self.pseudo + "/" # création du message
                        else :
                            msg = "failed:/"
                    
                    # Gestion de connexion:
                    elif action == "connexion":
                        attributsList = attributs.split(",")
                        playerData = self.main.controleur.connexion(attributsList[0], attributsList[1])
                        if playerData : # Valeurs correctes:
                            if self.main.controleur.alreadyTakenQ(playerData[0]["pseudo"]): # Joueur avec ce pseudo déjà connecté:
                                 msg = "failed:alreadyconnected/"
                            else:
                                self.pseudo = playerData[0]["pseudo"]
                                msg = "player_username:" + self.pseudo + "/" # création du message
                        else:
                            msg = "failed:/"
                    
                    # Envoi du classement:
                    elif action == "classement":
                        classement = self.main.controleur.get_bestPlayers()
                        msg = "classement:" # Création du message classement:
                        for player in classement:
                            msg+=player["pseudo"] +  "," + str(player["score"]) + "," + str(player["matchsGagnes"]) + ","+ str(player["partiesGagnees"]) + ";"
                        msg = msg[:-1]+"/"
                    
                    # Envoi des données de classement du joueur actuel:
                    elif action == "get_player_pos":
                        donnees = self.main.controleur.get_player_data(self.pseudo)
                        msg = "donnees_joueur_classement:{},{},{},{},{}/".format(donnees["pseudo"],str(donnees["score"]),str(donnees["matchsGagnes"]),str(donnees["partiesGagnees"]),str(donnees["place"]+1)) # +1 pour la place car on compte les joueurs en-dessus de celui-ci

                    # Demande du statut du jeu:
                    elif action == "ask_status":
                        msg = "game_status:"
                        if self.main.controleur.get_status():
                            msg+="started/"
                        else:
                            msg+="notstarted/"

                    self.main.lock.acquire()
                    self.connexion.send(msg.encode("Utf8"))
                    self.main.lock.release()

                # Déconnexion du joueur:
                elif action == "deconnexion":
                    self.pseudo = None

                    """ Gestion du jeu """
                
                # Connexion du client au jeu:
                elif action == "player_ingame" or action == "player_replay":
                    self.currentMatchesWon, self.currentScore, self.inGame = 0, 0, 1
                    if self.main.controleur.get_ingamePlayers() == 1: # Joueur gérant les options
                        self.main.controleur.settingsReceived = 0 # remise à zéro du flag vérifiant si les réglages ont été transmis
                        self.gameAdmin = 1
                        self.main.lock.acquire()
                        self.connexion.send("configPlayer:/".encode("Utf8"))
                        self.main.lock.release()
                    elif self.main.controleur.settingsReceived: # Ecran d'attente des joueurs
                        self.main.lock.acquire()
                        self.connexion.send("waitingForPlayers:/".encode("Utf8"))
                        self.main.lock.release()
                    else:                                       # Ecran d'attente des paramètres
                        self.main.lock.acquire()
                        self.connexion.send("waitingForSettings:/".encode("Utf8"))
                        self.main.lock.release()
                    if self.main.controleur.checkPlayers() and self.main.controleur.settingsReceived: # regarder si le nombre de joueurs correspond au nombre attendu
                        self.main.controleur.initGame()
                
                # Déconnexion du client du jeu:
                elif action == "player_outgame":
                    # Reset des attributs:
                    self.inGame = 0
                    self.spectate = 0
                    self.alive = 0
                    if self.gameAdmin: # Réattribution du rôle des réglages si ce joueur devait s'en occuper
                        self.gameAdmin = 0
                        self.main.controleur.settingsReceived = 0
                        inGamePlayers = []
                        for cle in self.main.threads:
                            if self.main.threads[cle].inGame:
                                inGamePlayers.append(self.main.threads[cle])
                        if len(inGamePlayers) != 0:
                            randPlayer = random.choice(inGamePlayers)
                            randPlayer.gameAdmin = 1
                            self.main.lock.acquire()
                            randPlayer.connexion.send("configPlayer:/".encode("Utf8"))
                            self.main.lock.release()

                # Réception des réglages:
                elif action == "settings":
                    self.main.controleur.set_settings(attributs.split(";"))
                    self.main.lock.acquire()
                    for cle in self.main.threads:
                        self.main.threads[cle].connexion.send("waitingForPlayers:/".encode("Utf8"))
                    self.main.lock.release()

                elif action == "all_dead":
                    self.main.controleur.sendDraw()

                # Mort d'un joueur:
                elif action == "player_death":
                    self.alive = 0
                    message = action+":"+self.pseudo+"/"
                    self.main.lock.acquire()
                    for cle in self.main.threads:
                        if cle != nom: #la mort du joueur pour le client qui est mort est directement gérée localement
                            self.main.threads[cle].connexion.send(message.encode("Utf8"))
                    self.main.lock.release()
                    self.main.controleur.checkMatchEnding()
                
                # Déconnexion abrupte d'un joueur:
                elif action == "abrupt_quit":
                    # Reset des attributs:
                    self.inGame = 0
                    self.gameAdmin = 0
                    self.alive = 0
                    if not self.spectate: #si le joueur est spectateur, ça ne fait rien pour les autres
                        # Arrêt de la partie sur le contrôleur:
                        self.main.controleur.game_ongoing = 0
                        self.main.controleur.settingsReceived = 0
                        self.main.controleur.timer_running = 0
                        msg = "abrupt_quit:{}/".format(self.pseudo)
                        self.main.lock.acquire()
                        for cle in self.main.threads:
                            if self.main.threads[cle].inGame:
                                self.main.threads[cle].connexion.send(msg.encode("Utf8"))
                        self.main.lock.release()
                    else:
                        self.spectate = 0
                # Autres actions: début de déplacement, fin de déplacement, pose de bombe
                else:
                    message = action+":"+self.pseudo+","+attributs+"/"
                    # Faire suivre le message à tous les clients :
                    self.main.lock.acquire()
                    for cle in self.main.threads:
                        self.main.threads[cle].connexion.send(message.encode("Utf8"))
                    self.main.lock.release()

        # Confirmation de déconnexion au client:
        self.main.lock.acquire()
        self.connexion.send("FIN".encode("Utf8"))
        self.main.lock.release()
        # Fermeture de la connexion :
        self.connexion.close()	  # couper la connexion côté serveur
        del self.main.threads[nom] # supprimer lui-même
        print("Client %s déconnecté." % nom)
        # Le thread se termine ici
 
class ConsoleServeur(threading.Thread):
    " Console de communication du serveur "
    def __init__(self, master):
        threading.Thread.__init__(self)
        self.master = master
    
    def run(self):
        """
        ConsoleServeur.run() --> None
        Boucle principale de la console du serveur
        """
        while self.master.loopingflag:
            self.handleMessage(input("Entrez stop pour arrêter le serveur: "))

    def handleMessage(self, msg):
        """
        ConsoleServeur.handleMessage(str msg) --> None
        S'occupe de gérer les messages transmis par la console du serveur
        """
        if msg == "stop":
            for cle in self.master.threads:
                self.master.threads[cle].connexion.send("FIN".encode("Utf8"))
            print("Arrêt du serveur")
            self.master.exit()

class ServerMain(object):
    """ Application principale du serveur """
    def __init__(self,ip,port):
        self.mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mySocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.threads = {} # Dictionnaire répertoriant les threads
        self.ip, self.port = ip, port
        self.lock = threading.Lock() # Verrou
        self.controleur = Controleur(self,"Bomberman.sq3") # Contrôleur de partie
        self.loopingflag = 1 # condition de la boucle, modifiée par la console serveur
        
    def run(self):
        """
        ServerMain.run() --> None
        Boucle principale du serveur
        """
        try:
            self.mySocket.bind((self.ip, self.port))
        except socket.error:
            print("La liaison du socket à l'adresse choisie a échoué.")
            sys.exit()
        print("Serveur prêt, en attente de requêtes ...")
        self.mySocket.listen(10)
        self.console = ConsoleServeur(self) # Console permettant d'entrer directement des commandes pour le serveur
        self.console.start()
        # Attente et prise en charge des connexions demandées par les clients :
        while self.loopingflag:
            try :
                connexion, adresse = self.mySocket.accept()
                # Créer un nouvel objet thread pour gérer la connexion :
                th = ThreadClient(self,connexion)
                th.start()
                # Mémoriser la connexion dans le dictionnaire :
                it = th.getName()	  # identifiant du thread
                self.threads[it] = th
                print("Client %s connecté, adresse IP %s, port %s." %\
                    (it, adresse[0], adresse[1]))
            except:
                continue
        while len(self.threads)!=0:
            continue
        print("Serveur fermé avec succès!")
    
    def exit(self):
        """
        ServerMain.exit() --> none
        Stoppe le serveur
        """
        for cle in self.threads:
            self.threads[cle].running = 0
        self.loopingflag = 0
        self.mySocket.close()

#####################
# Partie principale #
#####################

HOST, PORT = "localhost", 50000 
ServerMain(HOST,PORT).run()
