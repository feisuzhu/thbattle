import pyglet
from pyglet.gl import *
from client.ui.base import Overlay
from pyglet.text import Label

class LoadingScreen(Overlay):
    
    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        
        self.label = Label(text='Loading',
                    font_size=60,color=(255,255,255,255),
                    x=self.width//2, y=self.height//2,
                    anchor_x='center', anchor_y='center')
    
    def draw(self, dt):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.label.draw()

class LoginScreen(Overlay):
    
    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        self.batch = xxx#
        self.title = Label(text='LoginSCREEN!',
                    font_size=60,color=(0,0,0,255),
                    x=self.width//2, y=self.height//2,
                    anchor_x='center', anchor_y='center')
    
    def draw(self, dt):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.label.draw()
        