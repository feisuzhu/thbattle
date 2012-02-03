# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from client.ui.base import *
from client.ui.base import message as ui_message
from client.ui.controls_extra import *
from client.core import Executive
from pyglet.text import Label
from utils import Rect, rect_to_dict as r2d

import logging
log = logging.getLogger('UI_Screens')

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
        Executive.call('connect_server', ui_message, ('127.0.0.1', 9999), ui_message)

    def on_message(self, _type, *args):
        if _type == 'server_connected':
            login = LoginScreen()
            login.switch()
        elif _type == 'server_connect_failed':
            log.error('Server connect failed.')
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
            Executive.call('auth', ui_message, [u, pwd])

        @self.btn_exit.event
        def on_click():
            ui_message('app_exit')

    def on_message(self, _type, *args):
        if _type == 'auth_success':
            GameHallScreen().switch()
        elif _type == 'auth_failure':
            log.error('Auth failure')
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
        gl = self.gamelist = ListView(parent=self, x=35, y=220, width=700, height=420)
        gl.set_columns([
            ('game_no', 80),
            ('game_name', 300),
            ('game_type', 180),
            ('game_players', 50),
            ('game_status', 80),
        ])
        chat = self.chatbox = TextArea(parent=self, x=35, y=20, width=680, height=180)
        chat.text = 'Welcome to |cff0000ffGENSOUKILL|r!!!!!'
        ctl = self.control_panel = Control(parent=self, x=750, y=220, width=240, height=420)
        userinfo = self.userinfobox = Control(parent=self, x=750, y=20, width=240, height=180)

        self.btn_create = Button(parent=ctl, caption=u'创建游戏', x=0, y=0, width=117, height=48)
        self.btn_quickstart = Button(parent=ctl, caption=u'快速加入', x=0, y=50, width=117, height=48)
        self.btn_refresh = Button(parent=ctl, caption=u'刷新列表', x=0, y=100, width=117, height=48)

        @self.btn_create.event
        def on_click():
            Executive.call('create_game', ui_message, ['SimpleGame', 'Default Game'])

        @self.btn_quickstart.event
        def on_click():
            Executive.call('quick_start_game', ui_message, 'SimpleGame')

        @self.btn_refresh.event
        def on_click():
            Executive.call('get_hallinfo', ui_message, None)

        @self.gamelist.event
        def on_item_dblclick(li):
            Executive.call('join_game', ui_message, li.game_id)

        Executive.call('get_hallinfo', ui_message, None)

    def on_message(self, _type, *args):
        if _type == 'game_joined':
            GameScreen(args[0]).switch()
        elif _type == 'current_games':
            current_games = args[0]
            glist = self.gamelist
            glist.clear()
            for gi in current_games:
                li = glist.append([
                    gi['id'],
                    gi['name'],
                    gi['type'],
                    '%d/%d' % (
                        len([i for i in gi['slots'] if i['id']]),
                        len(gi['slots']),
                    ),
                    [u'等待中', u'进行中'][gi['started']]
                ])
                li.game_id = gi['id']

        elif _type == 'gamehall_error':
            log.error('GameHall Error: %s' % args[0]) # TODO
        else:
            Overlay.on_message(self, _type, *args)

class GameScreen(Overlay):
    class RoomControlPanel(Control):
        def __init__(self, parent=None):
            Control.__init__(self, parent=parent, **r2d((0, 0, 820, 720)))
            self.btn_getready = Button(
                parent=self, caption=u'准备', **r2d((360, 80, 100, 35))
            )

            self.box = pyglet.graphics.Batch()
            self.box.add(
                5, GL_LINE_STRIP, None,
                ('v2i', Rect(0, 0, 820, 140).glLineStripVertices()),
                ('c3f', [0.0, 0.0, 0.0] * 5)
            )
            l = []
            for (x, y), color in parent.ui_class.portrait_location:
                l.append(PlayerPortrait('NONAME', parent=self, x=x, y=y))
            self.portraits = l

            @self.btn_getready.event
            def on_click():
                Executive.call('get_ready', ui_message, [])
                self.btn_getready.state = Button.DISABLED

        def draw(self, dt):
            self.box.draw()
            self.draw_subcontrols(dt)

        def on_message(self, _type, *args):
            if _type == 'player_change':
                self.update_portrait(args[0])
            elif _type == 'game_left':
                GameHallScreen().switch()
            elif _type == 'game_joined':
                # last game ended, this is the auto
                # created game
                GameScreen(args[0]).switch()

        def update_portrait(self, pl):
            for i, p in enumerate(pl):
                name = p.get('nickname')
                name = 'EMPTY SLOT' if not name else name
                self.portraits[i].player_name = name
                self.portraits[i].refresh()

    def __init__(self, game, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)

        self.game = game
        self.ui_class = game.ui_class
        self.gameui = game.ui_class(
            parent=False, game=game,
            **r2d((0, 0, 820, 720))
        ) # add when game starts

        event_rect = (820, 350, 204, 370)
        chat_rect = (820, 0, 204, 350)
        self.events_box = TextArea(parent=self, **r2d(event_rect))
        self.chat_box = TextArea(parent=self, **r2d(chat_rect))
        self.panel = GameScreen.RoomControlPanel(parent=self)
        self.btn_exit = Button(
            parent=self, caption=u'退出房间', zindex=1,
            **r2d((730, 20, 75, 25))
        )

        @self.btn_exit.event
        def on_click():
            Executive.call('exit_game', ui_message, [])

    def on_message(self, _type, *args):
        if _type == 'game_started':
            self.remove_control(self.panel)
            self.gameui.init()
            self.add_control(self.gameui)
        if _type == 'end_game':
            self.remove_control(self.gameui)
            self.add_control(self.panel)
        else:
            Overlay.on_message(self, _type, *args)
