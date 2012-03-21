#!/bin/false

# ------------ code used to generate thb.resource.tag_sealarray -------

star = pyglet.image.load('/dev/shm/dfdf.png').get_texture(rectangle=True)
frame = pyglet.image.load('/dev/shm/frame.png').get_texture(rectangle=True)

n = 36
fbo = Framebuffer(pyglet.image.Texture.create_for_size(
    GL_TEXTURE_RECTANGLE_ARB, 25*n, 25, GL_RGBA
))

from colorsys import hsv_to_rgb as hsv
with fbo:
    glClearColor(0, 0, 0, 0)
    glClear(GL_COLOR_BUFFER_BIT)
    n1 = float(n)
    for i in range(n):
        glLoadIdentity()
        glColor3f(1, 1, 1)
        frame.blit(i*25, 0)
        glTranslatef(12.5 + i*25, 12.5, 0)
        glRotatef(-120/n1*i, 0, 0, 1)
        glTranslatef(-12.5, -12.5, 0)
        glColor3f(*hsv(i/n1, .6, 1.))
        star.blit(0, 0)

fbo.texture.save('/dev/shm/rst.png')
# ----------------------------------------------
