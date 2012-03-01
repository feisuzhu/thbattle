# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from client.ui.base import *
from client.ui.base import message as ui_message
from client.ui.controls import *
from client.ui import ui_utils
import  client.ui.resource as common_res
from client.core import Executive
from pyglet.text import Label
from utils import Rect, rect_to_dict as r2d

import logging
log = logging.getLogger('UI_Screens')

class _NotImplControl(Control):
    def draw(self):
        glColor3f(1, 1, 1)
        ui_utils.border(
            0, 0, self.width, self.height
        )

class LoadingScreen(Overlay):

    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)

        self.label = Label(text='Loading',
                    font_size=60,color=(255,255,255,255),
                    x=self.width//2, y=self.height//2,
                    anchor_x='center', anchor_y='center')

    def draw(self):
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
            ConfirmBox(u'服务器连接失败！', parent=self)
        else:
            Overlay.on_message(self, _type, *args)

    def draw(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.draw_subcontrols()

class LoginScreen(Overlay):
    class LoginDialog(Dialog):
        def __init__(self, *a, **k):
            Dialog.__init__(
                self, u'登陆', x=350, y=165,
                width=325, height=184,
                bot_reserve=50, *a, **k
            )
            self.batch = pyglet.graphics.Batch()
            Label(
                text=u'用户名：', font_size=9,color=(0,0,0,255),
                font_name='AncientPix', bold=True,
                x=368-350, y=286-165,
                anchor_x='left', anchor_y='bottom',
                batch=self.batch
            )
            Label(
                text=u'密码：', font_size=9,color=(0,0,0,255),
                font_name='AncientPix', bold=True,
                x=368-350, y=250-165,
                anchor_x='left', anchor_y='bottom',
                batch=self.batch
            )
            self.txt_username = TextBox(
                parent=self, x=438-350, y=282-165, width=220, height=20,
                text=u'魂魄妖梦'
            )
            self.txt_pwd = TextBox(
                parent=self, x=438-350, y=246-165, width=220, height=20,
                text='password'
            )
            self.btn_login = Button(
                parent=self, caption=u'进入幻想乡',
                x=50, y=10, width=100, height=30
            )
            self.btn_exit = Button(
                parent=self, caption=u'回到现世',
                x=175, y=10, width=100, height=30
            )

            @self.btn_login.event
            def on_click():
                u, pwd = self.txt_username.text, self.txt_pwd.text
                Executive.call('auth', ui_message, [u, pwd])

            @self.btn_exit.event
            def on_click():
                ui_message('app_exit')

        def draw(self):
            Dialog.draw(self)
            self.batch.draw()


    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        self.bg = common_res.bg_login
        self.bg_alpha = LinearInterp(0, 1.0, 1.5)
        self.dialog = LoginScreen.LoginDialog(parent=self)
        self.dialog.btn_close.state = Button.DISABLED

    def on_message(self, _type, *args):
        if _type == 'auth_success':
            GameHallScreen().switch()
        elif _type == 'auth_failure':
            log.error('Auth failure')
            ConfirmBox(u'认证失败！', parent=self)
        else:
            Overlay.on_message(self, _type, *args)

    def draw(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glColor4f(1, 1, 1, self.bg_alpha.value)
        self.bg.blit(0, 0)
        self.draw_subcontrols()

class GameHallScreen(Overlay):
    class GameList(Dialog):
        def __init__(self, p):
            Dialog.__init__(
                self, parent=p, caption=u'当前大厅内的游戏',
                x=35, y=220, width=700, height=420,
                bot_reserve=30, bg=common_res.bg_gamelist,
            )
            self.btn_close.state = Button.DISABLED

            gl = self.gamelist = ListView(parent=self, x=2, y=30, width=696, height=420-30-25)
            gl.set_columns([
                (u'No.', 100),
                (u'游戏名称', 200),
                (u'游戏类型', 200),
                (u'人数', 50),
                (u'当前状态', 80),
            ])


            self.btn_create = Button(parent=self, caption=u'创建游戏', x=690-270, y=6, width=70, height=20)
            self.btn_quickstart = Button(parent=self, caption=u'快速加入', x=690-180, y=6, width=70, height=20)
            self.btn_refresh = Button(parent=self, caption=u'刷新列表', x=690-90, y=6, width=70, height=20)


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


        def on_message(self, _type, *args):
            if _type == 'current_games':
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
                        [u'等待中', u'游戏中'][gi['started']]
                    ])
                    li.game_id = gi['id']

    class ChatBox(Dialog):
        def __init__(self, parent):
            Dialog.__init__(
                self, parent=parent,
                caption=u'系统/聊天信息',
                x=35, y=20, width=700, height=180,
                bot_reserve=33,
            )
            self.btn_close.state = Button.DISABLED
            self.box = TextArea(
                parent=self, x=2, y=33+2, width=700, height=180-24-2-33
            )
            self.inputbox = TextBox(
                parent=self, x=6, y=6, width=688, height=22,
            )

            @self.inputbox.event
            def on_enter():
                text = unicode(self.inputbox.text)
                self.inputbox.text = u''
                if text:
                    Executive.call('chat', ui_message, text)

        def append(self, v):
            self.box.append(v)

    def __init__(self, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)
        self.bg = common_res.bg_gamehall

        self.gamelist = self.GameList(self)

        chat = self.chat_box = GameHallScreen.ChatBox(parent=self)
        chat.text = u'您现在处于游戏大厅！\n'
        self.playerlist = Dialog(caption=u'当前在线玩家', parent=self, x=750, y=220, width=240, height=420)
        self.userinfo_box = Dialog(caption=u'你的战绩', parent=self, x=750, y=20, width=240, height=180)

        Executive.call('get_hallinfo', ui_message, None)

    def on_message(self, _type, *args):
        if _type == 'game_joined':
            GameScreen(args[0]).switch()
        elif _type in ('chat_msg', 'speaker_msg'):
            uname, msg = args[0]
            uname = uname.replace('|', '||')
            self.chat_box.append(u'|cff0000ff%s|r： %s\n' % (uname, msg))
        elif _type == 'gamehall_error':
            log.error('GameHall Error: %s' % args[0]) # TODO
            ConfirmBox(args[0], parent=self)
        else:
            Overlay.on_message(self, _type, *args)

    def draw(self):
        #glColor3f(.9, .9, .9)
        glColor3f(1,1,1)
        self.bg.blit(0, 0)
        self.draw_subcontrols()

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

        def draw(self):
            self.draw_subcontrols()

        def on_message(self, _type, *args):
            if _type == 'player_change':
                self.update_portrait(args[0])

        def update_portrait(self, pl):
            for i, p in enumerate(pl):
                name = p.get('nickname')
                name = 'EMPTY SLOT' if not name else name
                self.portraits[i].player_name = name
                self.portraits[i].refresh()

    class EventsBox(Dialog):
        def __init__(self, parent):
            Dialog.__init__(
                self, parent=parent,
                caption=u'游戏信息',
                x=820, y=350, width=204, height=370,
                bot_reserve=0, bg=common_res.bg_eventsbox,
            )
            self.no_move = True
            self.btn_close.state = Button.DISABLED
            self.box = TextArea(
                parent=self, x=2, y=2, width=200, height=370-24-2
            )

        def append(self, v):
            self.box.append(v)

    class ChatBox(Dialog):
        def __init__(self, parent):
            Dialog.__init__(
                self, parent=parent,
                caption=u'系统/聊天信息',
                x=820, y=0, width=204, height=352,
                bot_reserve=33, bg=common_res.bg_chatbox,
            )
            self.no_move = True
            self.btn_close.state = Button.DISABLED
            self.box = TextArea(
                parent=self, x=2, y=33+2, width=200, height=352-24-2-33
            )
            self.inputbox = TextBox(
                parent=self, x=6, y=6, width=192, height=22,
            )

            @self.inputbox.event
            def on_enter():
                text = unicode(self.inputbox.text)
                self.inputbox.text = u''
                if text:
                    Executive.call('chat', ui_message, text)

        def append(self, v):
            self.box.append(v)

    def __init__(self, game, *args, **kwargs):
        Overlay.__init__(self, *args, **kwargs)

        self.bg = common_res.bg_ingame

        self.game = game
        self.ui_class = game.ui_class
        self.gameui = game.ui_class(
            parent=False, game=game,
            **r2d((0, 0, 820, 720))
        ) # add when game starts

        self.events_box = GameScreen.EventsBox(parent=self)
        self.chat_box = GameScreen.ChatBox(parent=self)
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
        elif _type == 'end_game':
            self.remove_control(self.gameui)
            self.add_control(self.panel)
        elif _type in ('chat_msg', 'speaker_msg'):
            uname, msg = args[0]
            uname = uname.replace('|', '||')
            self.chat_box.append(u'|cff0000ff%s|r： %s\n' % (uname, msg))
        elif _type in ('game_left', 'fleed'):
            GameHallScreen().switch()
        elif _type == 'game_joined':
            # last game ended, this is the auto
            # created game
            GameScreen(args[0]).switch()
        else:
            Overlay.on_message(self, _type, *args)

    def draw(self):
        glColor3f(1,1,1)
        self.bg.blit(0, 0)
        self.draw_subcontrols()
