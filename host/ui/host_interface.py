# Main UI logic, handles manual/auto mode toggling
import pygame,pygame.freetype
pygame.init()
pygame.freetype.init()
class interface:
    def __init__(self,w):
        self.w = w
        self.autoB = button(50,400,100,25,"Auto Control",rectcolor = (0,255,0))
        self.objectFindB = button(600,500,100,25, "Find Object")
        self.goB = button(630,550,40,40,"GO",rectcolor = (255,0,0))
        self.upB = button(75,450,50,50," ^")
        self.rightB = button(125,500,50,50," >")
        self.leftB = button(25,500,50,50," <")
        self.downB = button(75,550,50,50," v")
        self.objectName = textfield(600,450,100,25)
        self.rotateTheta = textfield(605,400,40,20)
        self.rotateBeta = textfield(655,400,40,20)
        self.auto = True
        self.messages = ""

    def event(self,action):
        self.autoB.event(action)
        self.objectFindB.event(action)
        self.objectName.event(action)
        self.rotateTheta.event(action)
        self.rotateBeta.event(action)
        self.goB.event(action)
        if not self.auto:
            self.upB.event(action)
            self.rightB.event(action)
            self.leftB.event(action)
            self.downB.event(action)
    def tick(self):
        if self.autoB.getclicked():
            if self.auto:
                self.auto = False
                self.autoB.setrectcolor((125,125,125))
            else:
                self.auto = True
                self.autoB.setrectcolor((0,255,0))
        if self.objectFindB.getclicked():
            self.objectName.setstring("")
        if self.goB.getclicked():
            self.rotateTheta.setstring("")
            self.rotateBeta.setstring("")
    def returns(self):
        return "bob"

    def draw(self):
        self.autoB.draw(self.w)
        self.objectFindB.draw(self.w)
        self.objectName.draw(self.w)
        self.rotateTheta.draw(self.w)
        self.rotateBeta.draw(self.w)
        self.goB.draw(self.w)
        if not self.auto:
            self.upB.draw(self.w)
            self.rightB.draw(self.w)
            self.leftB.draw(self.w)
            self.downB.draw(self.w)
class textfield:
    def __init__(self,x,y,w,h,textcolor = (0,0,0),edgecolor = (0,0,0),rectcolor = (200,200,200),font = None,text = ""):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.data = text
        self.tick = True
        self.time = 0
        self.stringindex = -2
        self.textcolor = textcolor
        self.edgecolor = edgecolor
        self.rectcolor = rectcolor
        self.font = font
        self.textsize = self.gettextsize()
    def setfont(self,font):
        self.font = font
    def settextcolor(self,textcolor):
        self.textcolor = textcolor
    def setedgecolor(self,edgecolor):
        self.edgecolor = edgecolor
    def setrectcolor(self,rectcolor):
        self.rectcolor = rectcolor
    def gettextsize(self):
        size = self.h-10
        font = pygame.freetype.Font(self.font, size)  # None = default font, 32 = size
        rect = font.get_rect(self.data)
        while rect.width > self.w-10:
            font = pygame.freetype.Font(self.font, size)  # None = default font, 32 = size
            rect = font.get_rect(self.data)
            size -= 1
        return size
    def getstringsize(self,chari):
        font = pygame.freetype.Font(self.font, self.textsize)  # None = default font, 32 = size
        rect = font.get_rect(chari)
        return rect.width
    def setstring(self,string):
        self.data = string
        self.textsize = self.gettextsize()
    def getstring(self):
        return self.data
    def event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            px,py = event.pos
            if (self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h):
                if self.stringindex == -2:
                    self.stringindex = len(self.data)-1
                else:
                    sx = px-self.x
                    for i in range(len(self.data)):
                        distance = self.getstringsize(self.data[:i+1])
                        if (distance > sx):
                            self.stringindex = i
                            break
                        else:
                            self.stringindex = len(self.data)-1
            else:
                self.stringindex = -2
        if event.type == pygame.KEYDOWN and self.stringindex != -2:
            if event.key == pygame.K_BACKSPACE:
                if (len(self.data) > 0 and self.stringindex >= 0):
                    part1 = self.data[:self.stringindex]
                    part2 = self.data[self.stringindex+1:]
                    self.stringindex -= 1
                    self.data = part1 + part2
                    self.textsize = self.gettextsize()
            elif event.key == pygame.K_RIGHT:
                self.stringindex += 1
            elif event.key == pygame.K_LEFT:
                self.stringindex -= 1
            else:
                part1 = self.data[:self.stringindex+1]
                part2 = self.data[self.stringindex+1:]
                self.data = part1 + event.unicode + part2
                self.stringindex += 1
                self.textsize = self.gettextsize()
    def draw(self,w):
        pygame.draw.rect(w,self.rectcolor,pygame.Rect(self.x,self.y,self.w,self.h))
        pygame.draw.rect(w,self.edgecolor,pygame.Rect(self.x,self.y,self.w,self.h),2)
        font = pygame.freetype.Font(self.font, self.textsize)
        font.render_to(w,(self.x+5,self.y+int(self.h-self.textsize)/2),self.data,self.textcolor)
        if self.tick and self.stringindex != -2:
            distance = self.getstringsize(self.data[:self.stringindex+1])
            pygame.draw.rect(w,self.textcolor,pygame.Rect(self.x+distance + 5,self.y+(self.h-self.textsize)/2,1,self.textsize))
        if self.time >= 50:
            self.tick = not self.tick
            self.time = 0
        self.time += 1
class button:
    def __init__(self,x,y,w,h,text,textcolor = (0,0,0),edgecolor = (0,0,0),rectcolor = (200,200,200),font = None):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.data = text
        self.textcolor = textcolor
        self.edgecolor = edgecolor
        self.rectcolor = rectcolor
        self.font = font
        self.textsize = self.gettextsize()
        self.clicked = False
    def setfont(self,font):
        self.font = font
    def settextcolor(self,textcolor):
        self.textcolor = textcolor
    def setedgecolor(self,edgecolor):
        self.edgecolor = edgecolor
    def setrectcolor(self,rectcolor):
        self.rectcolor = rectcolor
    def gettextsize(self):
        size = self.h - 10
        font = pygame.freetype.Font(self.font, size)  # None = default font, 32 = size
        rect = font.get_rect(self.data)
        while rect.width > self.w-10:
            font = pygame.freetype.Font(self.font, size)  # None = default font, 32 = size
            rect = font.get_rect(self.data)
            size -= 1
        return size
    def getstringsize(self,chari):
        font = pygame.freetype.Font(self.font, self.textsize)  # None = default font, 32 = size
        rect = font.get_rect(chari)
        return rect.width
    def setstring(self,string):
        self.data = string
    def getclicked(self):
        if self.clicked:
            self.clicked = False
            return True
        return False
    def event(self,event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            px,py = event.pos
            if (self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h):
                self.clicked = True
                return True
        return False
    def draw(self,w):
        pygame.draw.rect(w,self.rectcolor,pygame.Rect(self.x,self.y,self.w,self.h))
        pygame.draw.rect(w,self.edgecolor,pygame.Rect(self.x,self.y,self.w,self.h),2)
        font = pygame.freetype.Font(self.font, self.textsize)
        font.render_to(w,(self.x+5,self.y+5+((self.h-self.textsize)-10)/2),self.data,self.textcolor)
