import pyglet
from pyglet.gl import *

w = pyglet.window.Window(width=1024, height=720)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
glViewport(0, 0, 1024, 720)
glOrtho(0, 1024, 0, 720, -1000, 1000)
glMatrixMode(GL_MODELVIEW)
glClearColor(1, 1, 1, 1)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
glPolygonMode(GL_BACK, GL_LINE)
img = pyglet.image.load('../src/client/ui/res/worldmap.png')
tex = img.get_texture()

coords = []


@w.event
def on_draw():
    glColor3f(1, 1, 1)
    glPolygonMode(GL_FRONT, GL_FILL)
    tex.blit(0, 0)
    glPolygonMode(GL_FRONT, GL_LINE)
    glBegin(GL_POLYGON)
    for x, y in coords:
        glVertex2f(x, y)
    glEnd()


@w.event
def on_mouse_press(x, y, button, modifiers):
    coords.append((x, y))


pyglet.app.run()
print coords
