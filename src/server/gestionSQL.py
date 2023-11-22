# Module gérant la connexion à la base de donnée SQL liée au jeu

##########################
# Importation de modules #
##########################

import sqlite3
import threading

#########################
# Définition de classes #
#########################

class GestionSQL:
    "Objet gérant la connexion à la base de données"
    def __init__(self,librairie):
        self.conn = sqlite3.connect(librairie, check_same_thread=False) # connexion à la base de données
        self.conn.row_factory = sqlite3.Row # changement des données sélectionnées pour recevoir des dictionnaires
        self.cur = self.conn.cursor()

        # Création de la table Players si elle n'existe pas
        try:
            self.execute("SELECT * FROM Players")
        except:
            self.create_table_players()

    def inscription(self, pseudo, nom, prenom, mdp):
        """
        GestionSQL.inscription(str pseudo, str nom, str prenom, str mdp) --> list
        Inscrit le joueur dans la base de données et retourne son pseudo, score, nombre de matchs gagnés et nombre de parties gagnées.
        """

        # Création de l'entrée du joueur dans la base de données:
        requete = """INSERT INTO Players (pseudo, nom, prenom, mdp) VALUES ("{}", "{}", "{}", "{}")""".format(pseudo, nom, prenom, mdp)
        self.execute(requete)

        # Communication des du pseudo
        return pseudo
    
    def get_players(self, criteres):
        """
        GestionSQL.get_players(dict criteres) --> list
        Retourne la liste des joueurs correspondant aux critères communiqués
        """
        requete = "SELECT * FROM Players WHERE "

        # Implémentation des critères communiqués
        for c in criteres:
            requete += """{}="{}" AND """.format(c,criteres[c])
        
        requete= requete[:-4] #enlever le AND final
        self.execute(requete)
        return self.cur.fetchall()
    
    def get_bestPlayers(self):
        """
        GestionSQL.get_players() --> list
        Retourne la liste des 10 meilleurs joueurs
        """
        requete = "SELECT pseudo, score, matchsGagnes, partiesGagnees FROM Players ORDER BY score DESC, pseudo ASC"
        self.execute(requete)
        return self.cur.fetchall()[:10]
    
    def get_player_data(self, pseudo):
        """
        GestionSQL.get_player_data(str pseudo) --> None
        Retourne le pseudo, la position dans le classement, le score, le nombre de parties et de matchs gagnés du joueur au pseudo <pseudo>
        """
        # Création des requêtes
        requeteDonnees = """ Select pseudo, score, matchsGagnes, partiesGagnees FROM Players WHERE Pseudo = "{}" """.format(pseudo)
        requetePlace = """ SELECT COUNT(*) AS "place"
        FROM PLAYERS
        WHERE Score > (SELECT Score FROM Players WHERE Pseudo = "{}")
        """.format(pseudo) # whoa such fancy much sqls
        #Exécution des requêtes
        self.execute(requeteDonnees)
        donnees = self.cur.fetchall()
        self.execute(requetePlace)
        place = self.cur.fetchall()

        # Fusion des deux dictionnaires et retour des données
        return {**donnees[0], **place[0]}
    
    def winNewMatch(self,pseudo):
        """
        GestionSQL.winNewMatch(str pseudo) --> None
        Ajoute un match gagné ainsi qu'un point au joueur correspondant à <pseudo> dans la base de données
        """
        requete = """UPDATE Players SET score=score+1, matchsGagnes=matchsGagnes+1 WHERE pseudo = "{}" """.format(pseudo)
        self.execute(requete)
    
    def winNewGame(self, pseudo):
        """
        GestionSQL.winNewGame(str pseudo) --> None
        Ajoute une partie gagnée ainsi que 2 points au joueur correspondant à <pseudo> dans la base de données
        """
        requete = """UPDATE Players SET score=score+2, partiesGagnees=partiesGagnees+1 WHERE pseudo = "{}" """.format(pseudo)
        self.execute(requete)
    
    def create_table_players(self):
        """
        GestionSQL.create_table_players() --> None
        Crée la table de données Players dans la base de données
        """
        requete = """CREATE TABLE Players 
            (playerID INT AUTO_INCREMENT PRIMARY KEY,
            pseudo VARCHAR(12) NOT NULL,
            mdp VARCHAR(12) NOT NULL,
            nom VARCHAR(12) NOT NULL,
            prenom VARCHAR(12) NOT NULL,
            score INT DEFAULT 0,
            matchsGagnes INT DEFAULT 0,
            partiesGagnees INT DEFAULT 0
        )"""
        self.execute(requete)
    
    def execute(self,requete):
        """
        GestionSQL.execute(str requete) --> None
        Exécute la requête SQL et l'affiche dans la console
        """
        print("Requête exécutée: ",requete)
        self.cur.execute(requete)
        self.conn.commit()
