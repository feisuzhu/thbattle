# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from client.ui.base import Overlay, TextBox, Button, Dialog
from client.ui.base import message as ui_message
from client.core import Executive
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

class ServerSelectScreen(Overlay):
    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        self.btn = Button(caption=u'连接服务器', x=480, y=400,
                          width=64, height=32, parent=self)
        self.btn.set_handler('on_click', self.do_connect)

    def do_connect(self):
        Executive.message('connect_server', ui_message, ('127.0.0.1', 9999), ui_message)

    def on_message(self, _type, *args):
        if _type == 'server_connected':
            login = LoginScreen()
            login.switch()
        elif _type == 'server_connect_failed':
            print 'FAILED!'
        else:
            Overlay.on_message(self, _type, *args)

class LoginScreen(Overlay):

    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        self.batch = pyglet.graphics.Batch()
        self.title = Label(text='GENSOUKILL',
                    font_size=60,color=(0,0,0,255),
                    x=272, y=475,
                    batch=self.batch)
        x, y, w, h = 350, 165, 325, 160
        x1, y1 = x + w, y + h
        self.batch.add(5, GL_LINE_STRIP, None,
                       ('v2i', [
                        x, y, x1, y,
                        x1, y1, x, y1,
                        x, y]),
                       ('c3f', [0.0, 0.0, 0.0] * 5))
        Label(text=u'用户名：', font_size=12,color=(0,0,0,255),
                            x=368, y=284,
                            anchor_x='left', anchor_y='bottom',
                            batch=self.batch)
        Label(text=u'密码：', font_size=12,color=(0,0,0,255),
                            x=368, y=246,
                            anchor_x='left', anchor_y='bottom',
                            batch=self.batch)
        self.txt_username = TextBox(parent=self, x=438, y=282, width=220, text='youmu')
        self.txt_pwd = TextBox(parent=self, x=438, y=246, width=220, text='password')
        self.btn_login = Button(parent=self, caption=u'进入幻想乡', x=378, y=182, width=127, height=48)
        self.btn_exit = Button(parent=self, caption=u'回到现世', x=520, y=182, width=127, height=48)

        @self.btn_login.event
        def on_click():
            u, pwd = self.txt_username.text, self.txt_pwd.text
            Executive.message('auth', ui_message, u, pwd)

        @self.btn_exit.event
        def on_click():
            ui_message('app_exit')

    def on_message(self, _type, *args):
        if _type == 'auth_success':
            GameHallScreen().switch()
        elif _type == 'auth_failure':
            print 'FAILED'
        else:
            Overlay.on_message(self, _type, *args)


    def draw(self, dt):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.batch.draw()
        self.draw_subcontrols(dt)


class GameHallScreen(Overlay):
    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        self.btn_create = Button(parent=self, caption=u'创建游戏', x=378, y=182, width=117, height=48)
        self.btn_quickstart = Button(parent=self, caption=u'快速加入', x=510, y=182, width=117, height=48)
