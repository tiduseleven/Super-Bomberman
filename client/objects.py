# Définitions de différents objets de l'interface graphique, utilisés dans le programme en général.

###########################
# Importation des modules #
###########################

import pygame
from variables import *

#########################
# Définition de classes #
#########################
class BasicScreen(object):
    """ Classe utilisée comme parent pour tous les menus, définissant les attributs et méthodes de base """
    buttons = {
        "confirmer":{"passive":"./images/menu/confirmer.png", "active":"./images/menu/confirmer_hovering.png"},
        "retour":{"passive":"./images/menu/retour.png", "active":"./images/menu/retour_hovering.png"},
        "terminer":{"passive":"./images/menu/terminer.png", "active":"./images/menu/terminer_hovering.png"},
    }

    def __init__(self, master):
        # Attributs d'instance
        self.master = master
        self.app = master.get_app()
        self.buttons = [] #liste des boutons
        self.inputFields = [] #liste des champs d'entrée
        self.images = [] #liste des images
        self.imageRects = [] #liste des rectangles donnant les coordonnées des images
        self.texts = [] #liste des textes
        self.textRects = [] #liste des rectangles associés aux textes
        self.paragraphs = [] #liste des paragraphes de textes
        self.popup = None
    
    def get_app(self):
        """
        BasicScreen.get_app() --> Application
        Retourne l'application lancée actuellement
        """
        return self.app

    def retour(self):
        """
        BasicScreen.retour() --> None
        Gère le retour à l'écran principal du jeu
        """
        self.resetTexts()
        self.app.set_currentScreen(self.app.mainMenu)

    def setActive(self):
        """
        BasicScreen.setActive() --> None
        Affiche le menu en question à l'écran
        """
        self.app.set_currentScreen(self)
    
    def handleEvents(self,events):
        """
        BasicScreen.handleEvent(pygame.EventList events) --> None
        Gère les événements communiqués
        """
        if self.popup: #si un popup est actif, seules les modifications du popup sont importantes
                self.popup.handleEvents(events)
        else:
            # Mise à jour des boutons par le curseur:
            for button in self.buttons:
                button.detectCursor(self.app.get_cursorPos())
            for event in events:
                for inputField in self.inputFields:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB and inputField.active:
                        inputField.handleEvent(event)
                        break
                    else:
                        inputField.handleEvent(event)
                for button in self.buttons:
                    button.handleEvent(event)
    
    def render(self,screen):
        """
        BasicScreen.render(pygame.Surface screen) --> None
        Affiche les différents éléments à l'écran
        """
        for button in self.buttons:
            button.render(screen)
        for inputField in self.inputFields:
            inputField.render(screen)
        for image,rect in zip(self.images,self.imageRects):
            image.render(screen, rect)
        for text,textRect in zip(self.texts, self.textRects):
            screen.blit(text,textRect)
        for paragraph in self.paragraphs:
            paragraph.render(screen)
        if self.popup:
            self.popup.render(screen)
    
    def set_popup(self, text):
        """
        BasicScreen.set_popup(str text) --> None
        Affiche sur l'écran actuel un popup avec le text <text>
        """
        self.popup = PopUp(self,round(self.app.get_screenH()/2),round(self.app.get_screenH()/3), text)

    def reset(self):
        """
        BasicScreen.reset() --> None
        Vide complètement l'écran
        """
        self.__init__(self.master)

    def resetTexts(self):
        """
        BasicScreen.resetTexts() --> None
        Remet à zéro les textes des zones d'entrée
        """
        for inputField in self.inputFields:
            inputField.text = ""
            inputField.textSurface = inputField.font.render(inputField.text, True, inputField.color)

class ConfigLine(BasicScreen):
    " Ligne de configuration de la partie"
    buttons = {"less":{"active":"./images/menu/less_usable_hovering.png","passive":"./images/menu/less_usable.png","disabled":"./images/menu/less_unusable.png"},
                "more":{"active":"./images/menu/more_usable_hovering.png","passive":"./images/menu/more_usable.png","disabled":"./images/menu/more_unusable.png"}
    }
    def __init__(self, master, x, y, w, h, text, options):
        super().__init__(master)


        self.font = master.font # police du texte
        self.options = options # Différents choix de la configuration
        self.chosenI = round((len(self.options)-1)/2)
        # Texte de description
        text = self.font.render(text,True,colors["ORANGE"])
        textRect = text.get_rect()
        textRect.x, textRect.centery = x, y + h/2
        self.texts.append(text)
        self.textRects.append(textRect)
        
        # Bouton <:
        button = ArrowButton(self, x + w/2, y+h/2, h*4/5, ConfigLine.buttons["less"],  lambda: self.choiceDown(), 1)
        self.buttons.append(button)
        # Texte changeant:
        self.changingText = self.font.render(self.options[self.chosenI],True,colors["ORANGE"])
        self.changingTextRect = self.changingText.get_rect()
        self.changingTextRect.centerx, self.changingTextRect.centery = x+w/2+h*2, y+h/2

        # Bouton >:
        button = ArrowButton(self, self.changingTextRect.centerx*2 - self.buttons[0].imageRect.centerx, y+h/2, h*4/5, ConfigLine.buttons["more"],  lambda: self.choiceUp(), 1)
        self.buttons.append(button)

    def get_chosenI(self):
        """
        ConfigLine.get_chosenI() --> int
        Retourne la valeur de l'indice de l'option choisie
        """
        return self.get_chosenI
    
    def get_chosenOption(self):
        """
        ConfigLine.get_chosenOption() --> str
        Retourne l'option choisie
        """
        return self.options[self.chosenI]
        
    def get_optionsLength(self):
        """
        ConfigLine.get_optionsLength() --> int
        Retourne la longueur de la liste des options
        """
        return len(self.options)

    def choiceDown(self):
        """
        ConfigLine.choiceDown() --> None
        Baisse l'indice choisi de 1
        """
        self.chosenI -= 1
        if self.chosenI == 0:
            self.buttons[0].enabled = 0
        self.buttons[1].enabled = 1
        self.updateText()

    def choiceUp(self):
        """
        ConfigLine.choiceDown() --> None
        Monte l'indice choisi de 1
        """
        self.chosenI += 1
        if self.chosenI == len(self.options)-1:
            self.buttons[1].enabled = 0
        self.buttons[0].enabled = 1
        self.updateText()

    def updateText(self):
        """
        ConfigLine.updateText() --> None
        Met à jour le texte indiquant l'option sélectionnée
        """
        self.changingText = self.font.render(self.options[self.chosenI],True,colors["ORANGE"])

    def render(self, screen):
        """
        ConfigLine.render(pygame.Surface screen) --> None
        Affiche la ligne de configuration à l'écran
        """
        super().render(screen)
        screen.blit(self.changingText, self.changingTextRect)

class PopUp(BasicScreen):
    """ Pop-up composé d'un texte et d'un bouton """
    def __init__(self,master, w, h, text, func = None):
        super().__init__(master)

        # Définition des attributs de style du popup:
        self.fontSize = round(h/10)
        self.accentColor = colors["ORANGE"]
        self.backgroundColor = colors["DARKGRAY"]
        
        # Création du fond du popup:
        self.image = pygame.Surface((w,h))
        self.rect = self.image.get_rect()
        self.rect.center = self.app.get_screenW()/2, self.app.get_screenH()/2

        # Création des éléments du popup:
        # Texte:
        self.paragraphs.append(Paragraph(round(self.app.get_screenW()/2), round(self.app.get_screenH()/5*2),text,"freesansbold.ttf",self.fontSize,self.accentColor,round(self.rect.width/5*4)))
        # Bouton:
        #fonction du bouton:
        if func:
            function = func
        else:
            function = lambda: self.resetPopUps()
        self.buttons.append(Button(self,self.app.get_screenW()/2,self.app.get_screenH()/2+self.rect.height*1/4,self.rect.height/5,BasicScreen.buttons["terminer"], function))

    def render(self,screen):
        """
        PopUp.render(pygame.Surface screen) --> None
        Affiche le popup sur l'écran
        """
        pygame.draw.rect(screen,self.backgroundColor,self.rect, border_radius = round(self.rect.h/10))
        pygame.draw.rect(screen,self.accentColor,self.rect,2, border_radius = round(self.rect.h/10))
        super().render(screen)

    def resetPopUps(self):
        """
        PopUp.resetPopUps() --> None
        Gère la suppression du popup et le retour à l'écran principal si le joueur s'est connecté.
        """
        self.master.popup = None
        if self.app.playerUsername :
            self.master.resetTexts()
            self.app.mainMenu.setButtons()
            self.app.mainMenu.setActive()

class InputField(object):
    """Champ d'entrée de texte"""
    def __init__(self, master, indice, x, y, w, h, colors, maxLength, emptyText="", text="", censored=0):
        # Attributs d'instance:
        self.master = master
        self.i = indice
        self.time = 0
        self.active = False
        self.maxLength = maxLength
        self.censored = censored
        #Police d'écriture:
        self.fontSize = round(h/5*4)
        self.font = pygame.font.Font("freesansbold.ttf",self.fontSize)

        #Couleurs:
        self.passiveColor = colors[0]
        self.activeColor = colors[1]
        self.color = self.passiveColor

        #Elements visibles:
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.emptyText = emptyText # texte à afficher quand la case est vide
        if self.censored:
            self.censoredText = ""
        self.textSurface = self.font.render(self.text, True, self.color)
        self.textRect = self.textSurface.get_rect()
        self.emptyTextSurface = self.font.render(self.emptyText, False, self.activeColor)
        self.emptyTextSurface.set_alpha(65) # rend le texte informatif transparent
    
    def handleEvent(self,event):
        """
        InputField.handleEvent(pygame.Event event) --> None
        Prise en charge des différents événements transmis par l'application
        """
        # Clics de souris:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False

        # Touches du clavier:
        if self.active :
            self.color = self.activeColor
            if event.type == pygame.KEYDOWN:
                # Touches spéciales:
                if event.key == pygame.K_TAB:
                    self.active = False
                    try:
                        nextField = self.master.inputFields[self.i+1]
                        nextField.active = True
                    except:
                        pass
                elif event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE or event.key == pygame.K_KP_ENTER:
                    self.active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                    if self.censored:
                        self.censoredText = self.censoredText[:-1]
                #Texte normal:
                else:
                    if len(self.text)<self.maxLength :
                        self.text += event.unicode
                        if self.censored:
                            self.censoredText = (len(self.text)-1)*"*"+event.unicode
                    else:
                        self.master.popup = PopUp(self.master,round(self.master.app.screenh/2),round(self.master.app.screenh/3),"Vous avez atteint la taille maximale!")
            
            if self.censored:
                self.textSurface = self.font.render(self.censoredText, True, self.color)
            else:
                self.textSurface = self.font.render(self.text, True, self.color)

        else :
            self.color = self.passiveColor
            if self.censored :
                self.censoredText = len(self.text)*"*"
                self.textSurface = self.font.render(self.censoredText, True, self.color)
      
    def render(self, screen):
        """
        InputField.render(pygame.Surface screen) --> None
        Affiche sur l'écran screen la zone d'entrée de texte ainsi que le texte
        """
        pygame.draw.rect(screen, self.color, self.rect, round(self.rect.height/20),border_radius = round(self.rect.h/2))
        screen.blit(self.textSurface, (round(self.rect.x+self.rect.width/20), round(self.rect.y+self.rect.height/2-self.fontSize/2)))
        self.renderCursor(screen)
        if self.text == "" and not self.active :
            screen.blit(self.emptyTextSurface, (round(self.rect.x+self.rect.width/20), round(self.rect.y+self.rect.height/2-self.fontSize/2)))
    
    def renderCursor(self,screen):
        """
        InputField.renderCursor(pygame.Surface screen) --> None
        Affiche le curseur de texte sur l'écran
        """
        if self.active:
            self.textRect = self.textSurface.get_rect()
            if self.time%self.master.app.fps<self.master.app.fps/2:
                pygame.draw.line(screen, self.activeColor,(round(self.rect.x+self.rect.width/20+self.textRect.width),round(self.rect.y+self.rect.height/2-self.fontSize/2)),(round(self.rect.x+self.rect.width/20+self.textRect.width),round(self.rect.y+self.rect.height/2+self.fontSize/2)),round(self.rect.width/200))
        self.time+=1

class Button(object):
    """Bouton basique affiché par une image"""
    def __init__(self,master,x,y,h,images, func):
        self.master = master
        self.app = self.master.app
        passive, active, self.function = images["passive"],images["active"], func  

        #création des images passives et actives : images lorsque le curseur est en dehors du bouton ou sur le bouton respectivement
        self.passiveImage = Image(passive, h)
        self.activeImage = Image(active, h)
        #création du bouton actuellement à l'écran:
        self.image = self.passiveImage
        self.imageRect = self.image.get_rect()
        self.imageRect.center = x,y

        #création du son du bouton:
        self.sound = pygame.mixer.Sound("./sounds/ButtonPress.wav")
        self.sound.set_volume(self.app.get_volume())

    def changeImage(self,image):
        """
        Button.changeImage(image) --> None
        Change l'image à l'écran du bouton
        """
        if self.image!= image:
            self.image = image

    def detectCursor(self,cursorPos):
        """
        Button.detectCursor(tuple cursorPos) --> None
        Détecte si le curseur est sur le bouton, et change l'image affichée en conséquence
        """
        if self.imageRect.x <= cursorPos[0] <= self.imageRect.x+self.imageRect.width : # Test horizontal
            if self.imageRect.y <= cursorPos[1] <= self.imageRect.y+self.imageRect.height : # Test vertical
                self.changeImage(self.activeImage)

            else :
                self.changeImage(self.passiveImage)

        else :
            self.changeImage(self.passiveImage)
    
    def handleEvent(self, event):
        """
        Button.handleEvent(pygame.Event event) --> None
        Gestion d'événement du bouton
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.image == self.activeImage:
            self.function()
            self.sound.play()
        
    def render(self,screen):
        """
        Button.render(pygame.Surface screen) --> None
        Affiche le bouton à l'écran
        """
        self.image.render(screen,self.imageRect)

class AudioButton(Button):
    "Bouton gérant le son du jeu"
    def __init__(self, master, x, y, h, images, func):
        super().__init__(master,x,y,h,images,func)
        self.unmutedImage, self.mutedImage = self.passiveImage, self.activeImage
        if self.master.get_volume() == 1:
            self.image = self.unmutedImage
        else:
            self.image = self.mutedImage
        self.cursorOnButton = 0
    
    def detectCursor(self, cursorPos):
        """
        AudioButton.detectCursor(tuple cursorPos) --> None
        Détecte si le curseur est sur le bouton
        """
        if self.imageRect.x <= cursorPos[0] <= self.imageRect.x+self.imageRect.width : # Test horizontal
            if self.imageRect.y <= cursorPos[1] <= self.imageRect.y+self.imageRect.height : # Test vertical
                self.cursorOnButton = 1

            else :
                self.cursorOnButton = 0

        else :
            self.cursorOnButton = 0

    def handleEvent(self,event):
        """
        AudioButton.handleEvent(pygame.Event event) --> None
        Gestion d'événement du bouton
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.cursorOnButton:
            self.action()
            self.sound.play()
    
    def action(self):
        """
        AudioButton.action() --> None
        Change l'image du bouton et effectue la fonction du bouton
        """
        if self.image == self.mutedImage:
            self.function(1)
        else:
            self.function(0)
        self.changeImage()

    def changeImage(self):
        """
        AudioButton.changeImage() --> None
        Change l'image du bouton lorsqu'il est cliqué
        """
        if self.image == self.mutedImage:
            self.image = self.unmutedImage
        else:
            self.image = self.mutedImage

class ArrowButton(Button):
    "Bouton flèche augmentant ou diminuant un nombre"
    def __init__(self,master,x,y,h,images, func, enabled):
        super().__init__(master,x,y,h,images,func)
        self.disabledImage = Image(images["disabled"],h)
        self.enabled = enabled # Flag indiquant si le bouton est activé, c-à-d s'il peut être utilisé
        if self.enabled:
            self.image = self.passiveImage
        else:
            self.image = self.disabledImage
    
    def detectCursor(self, cursorPos):
        """
        ArrowButton.detectCursor(tuple cursorPos) --> None
        Gère la détection du curseur si le bouton est activé
        """
        if self.enabled:
            super().detectCursor(cursorPos)
        else:
            self.changeImage(self.disabledImage)

class Image:
    """Objet image"""
    def __init__(self,image,h):
        # Attributs d'instance:
        self.image = self.imagify(image, h)
    
    def imagify(self, image, h):
        """
        Image.imagify(str image, int h) --> pygame.Surface
        Crée une image à partir du fichier indiqué par <image>
        """
        image = pygame.image.load(image).convert_alpha()
        imageRect = image.get_rect()
        image = pygame.transform.scale(image,(round(h*imageRect.width/imageRect.height),round(h)))

        return image
    
    def get_rect(self):
        """
        Image.get_rect() --> pygame.Rect
        Retourne les coordonnées du coin supérieur gauche de l'image
        """
        return self.image.get_rect()

    def render(self,screen, rect):
        """
        Image.render(pygame.Surface screen, pygame.Rect rect) --> None
        Affiche l'image sur l'écran <screen> à la place indiquée par <rect>
        """
        screen.blit(self.image,rect)

class Paragraph:
    " Un paragraphe de texte"
    def __init__(self, x, y ,text, font, fontSize, color, width):
        self.texts = []
        self.textRects = []
        self.paragraphize(x,y,text,font,fontSize,color,width)

    def paragraphize(self, x , y, text, font, fontSize, color, width):
        """
        Paragraph.paragraphize(int x, int y, str text, str font, int fontSize, tuple color, int width) --> None
        Crée un paragraphe de texte tenant dans la zone de largeur width, centré horizontalement en x et commençant à la hauteur y
        """
        font = pygame.font.Font(font,fontSize)

        words = text.split(" ")
        lines = []
        line = ""
        newline = ""
        # Création de lignes (composées de mots entiers) rentrant dans la largeur width
        for word,i in zip(words,range(0,len(words))):
            newline+=word+" "
            newlineWidth = font.render(newline,True,color).get_rect().width
            if newlineWidth > width: # La nouvelle ligne est trop grande --> on prend la ligne gardée en mémoire
                lines.append(line)
                newline = word+" " # redéfinition de newLine
                line = ""
            else :
                line = newline
        
        lines.append(newline) # Ajout des mots restants présents dans newLine
        
        # Création des textes
        for i,line in zip(range(0,len(lines)),lines):
            text = font.render(line, True, color)
            textRect = text.get_rect()
            textRect.center = x,y+i*(fontSize*4/3)
            self.texts.append(text)
            self.textRects.append(textRect)
    
    def render(self, screen):
        """
        Paragraph.render(pygame.Surface screen) --> None
        Affiche le paragraphe à l'écran
        """
        for text, textRect in zip(self.texts, self.textRects):
            screen.blit(text,textRect)
        
    