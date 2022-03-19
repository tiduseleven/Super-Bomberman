# Définition d'un client réseau gérant en parallèle l'émission
# et la réception des messages (utilisation de 2 THREADS).

# Tiré en grande partie du script "Communications à travers un réseau et multithreading"

###########################
# Importation des modules #
###########################

import socket, sys, threading
 
##########################
# Définitions de classes #
##########################

class ThreadClient(threading.Thread):
    """objet thread gérant la réception et l'émission des messages"""
    def __init__(self, app, ip, port):
        threading.Thread.__init__(self)
        self.connexion = self.create_conn(ip,port)
        self.app = app
  
    def run(self):
        """
        ThreadClient.run() --> None
        Boucle principale du thread gérant la réception de messages
        """
        while 1:
            message_recu = self.connexion.recv(1024).decode("Utf8")
            if message_recu.upper() =="FIN":
                try: self.app.handleServerStop()
                except: pass
                break
            messages = message_recu[:-1].split("/") # [:-1] pour enlever le dernier /
            for message in messages:
                if message == "":
                        continue
                self.app.handleMessage(message)
        # Le thread se termine ici.
        print("Client arrêté. Connexion interrompue.")
        self.connexion.close()
        
    def send(self,msg):
        """
        ThreadClient.send(str msg) --> None
        Envoi des messages au serveur
        """
        self.connexion.send(msg.encode("Utf8"))
    
    def set_app(self,app):
        """
        ThreadClient.set_app(Application app) --> None
        Met à jour la valeur de self.app pour cette instance
        """
        self.app = app
    
    def create_conn(self,ip,port):
        """
        ThreadClient.createThread(str ip, int port) --> None
        Création du thread gérant les messages entrant et sortant du client
        """
        connexion = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            connexion.connect((ip, port))
        except socket.error:
            print("La connexion a échoué.")
            sys.exit()
        print("Connexion établie avec le serveur.")
        return connexion


