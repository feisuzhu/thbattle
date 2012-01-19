# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from client.ui.base import Control, Overlay, TextBox, Button, Dialog
from client.ui.base import message as ui_message
from client.ui.controls_extra import TextArea, PlayerPortrait
from client.core import Executive
from pyglet.text import Label
from utils import Rect, rect_to_dict

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

    def draw(self, dt):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.draw_subcontrols(dt)

class LoginScreen(Overlay):

    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        self.batch = pyglet.graphics.Batch()
        self.title = Label(text='GENSOUKILL',
                    font_size=60,color=(0,0,0,255),
                    x=272, y=475,
                    batch=self.batch)
        r = Rect(350, 165, 325, 160)
        self.batch.add(
            5, GL_LINE_STRIP, None,
            ('v2i', r.glLineStripVertices()),
            ('c3f', [0.0, 0.0, 0.0] * 5)
        )
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
            Executive.message('auth', ui_message, [u, pwd])

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

        @self.btn_create.event
        def on_click():
            Executive.message('create_game', ui_message, 'Simple Game')

        @self.btn_quickstart.event
        def on_click():
            Executive.message('quick_start_game', ui_message, 'Simple Game')

    def on_message(self, _type, *args):
        if _type == 'game_joined':
            game = args[0]
            gs = GameScreen(game)
            self.gs = gs
            gs.switch()
        elif _type == 'gamehall_error':
            print args[0] # TODO
        elif _type == 'player_change':
            ''' HACK:
            the 'player_change' message comes right after the 'game_joined'
            message when it is received,
            GameScreen is switched to when 'game_joined' arrived, so if we
            have a good networking, GameScreen will miss the first 'player_change'
            message.'''
            if self.gs: self.gs.dispatch_message([_type]+list(args))
        else:
            Overlay.on_message(self, _type, *args)

class GameScreen(Overlay):
    class RoomControlPanel(Control):
        def __init__(self, parent=None):
            r2d = rect_to_dict
            Control.__init__(self, parent=parent, **r2d((0, 0, 820, 140)))
            self.btn_getready = Button(
                parent=self, caption=u'准备', **r2d((360, 80, 100, 35))
            )
            self.btn_exit = Button(
                parent=self, caption=u'退出房间', **r2d((730, 20, 75, 25))
            )

            @self.btn_getready.event
            def on_click():
                Executive.message('get_ready', ui_message, [])
                self.btn_getready.state = Button.DISABLED

            @self.btn_exit.event
            def on_click():
                Executive.message('exit_game', ui_message, [])

        def on_message(self, _type, *args):
            if _type == 'player_change':
                self.parent.update_portrait(args[0])
            elif _type == 'game_left':
                GameHallScreen().switch()
            else:
                Overlay.on_message(self, _type, *args)

    def __init__(self, game, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        self.ui_class = game.ui_class
        event_rect = (820, 350, 204, 370)
        chat_rect = (820, 0, 204, 350)
        self.events_box = TextArea(parent=self, **rect_to_dict(event_rect))
        self.chat_box = TextArea(parent=self, **rect_to_dict(chat_rect))
        self.panel = GameScreen.RoomControlPanel(parent=self)

        l = []
        for (x, y), color in self.ui_class.portrait_location:
            l.append(PlayerPortrait('NONAME', parent=self, x=x, y=y))
        self.portraits = l
        self.game = game

    def update_portrait(self, pl):
        for i, p in enumerate(pl):
            name = p.get('nickname')
            name = 'EMPTY SLOT' if not name else name
            self.portraits[i].player_name = name
            self.portraits[i].refresh()
