# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from client.ui.base import *
from client.ui.base import message as ui_message
from client.ui.controls import *
import  client.ui.resource as common_res
from client.core import Executive
from pyglet.text import Label
from utils import Rect, rect_to_dict as r2d

import logging
log = logging.getLogger('UI_Screens')

class Screen(Overlay):
    def on_message(self, _type, *args):
        if _type == 'server_dropped':
            ConfirmBox(u'已经与服务器断开链接，请重新启动游戏！', parent=Screen.cur_overlay)
        else:
            Overlay.on_message(self, _type, *args)

class UpdateScreen(Screen):
    trans = dict(
        update_begin = lambda: u'|W开始更新……|r',
        up2date = lambda: u'|W已经是最新版本了|r',
        delete_file = lambda fn: u'|W删除：|LB%s|r' % fn,
        download_file = lambda fn: u'|W下载：|LB%s|r' % fn,
        download_complete= lambda fn: u'|W下载完成：|LB%s|r' % fn,
        write_failed = lambda fn: u'|R无法写入：|LB%s|r' % fn,
        update_finished = lambda: u'|W更新完成|r',
        http_error = lambda code, url: u'|RHTTP错误： %d %s|r' % (code, url),
        network_error = lambda: u'|R网络错误|r',
        io_error = lambda: u'|R系统错误|r', # WHATEVER
    )

    def __init__(self, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)
        ta = TextArea(
            parent=self, width=600, height=450,
            x=(self.width-600)//2, y=(self.height-450)//2
        )
        self.textarea = ta

    def update_message(self, msg, *args):
        msg = self.trans[msg](*args)
        self.textarea.append(msg + '\n')

    def draw(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.draw_subcontrols()

class ServerSelectScreen(Screen):
    def __init__(self, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)
        self.buttons  = buttons = []
        from settings import ServerList as sl, NOTICE

        class BalloonImageButton(ImageButton, BalloonPrompt):
            pass

        class NoticePanel(Panel):
            fill_color = (1.0, 1.0, 0.9, 0.5)
            def __init__(self, text, *a, **k):
                Panel.__init__(self, *a, **k)
                w, h = self.width, self.height
                ta = TextArea(
                    parent=self,
                    font_size=12,
                    x=2, y=60,
                    width=w-4, height=h-4-60
                )
                ta.append(text)
                btn = Button(
                    u'关闭',
                    parent=self,
                    x=(w-120)//2, y=20,
                    width=120, height=40,
                )
                @btn.event
                def on_click():
                    self.delete()

        for s in sl.values():
            btn = BalloonImageButton(
                common_res.buttons.serverbtn,
                parent=self, x=s['x'], y=s['y'],
            )
            btn.init_balloon(s['description'])
            btn.set_handler('on_click', lambda s=s: self.do_connect(s['address']))
            buttons.append(btn)

        NoticePanel(
            NOTICE,
            parent=self,
            width=800, height=600,
            x=(self.width-800)//2, y=(self.height-600)//2
        )

    def do_connect(self, addr):
        for b in self.buttons:
            b.state = Button.DISABLED
        Executive.call('connect_server', ui_message, addr, ui_message)

    def on_message(self, _type, *args):
        if _type == 'server_connected':
            login = LoginScreen()
            login.switch()
        elif _type == 'server_connect_failed':
            for b in self.buttons:
                b.state = Button.NORMAL
            log.error('Server connect failed.')
            ConfirmBox(u'服务器连接失败！', parent=self)
        elif _type == 'version_mismatch':
            for b in self.buttons:
                b.state = Button.NORMAL
            log.error('Version mismatch')
            ConfirmBox(u'您的版本与服务器版本不符，无法进行游戏！', parent=self)
        else:
            Screen.on_message(self, _type, *args)

    def draw(self):
        glColor3f(0.9, 0.9, 0.9)
        common_res.worldmap.blit(0, 0)
        self.draw_subcontrols()

class LoginScreen(Screen):
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
                text=u'另一只罪袋'
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
                pyglet.app.exit()

        def draw(self):
            Dialog.draw(self)
            self.batch.draw()

    def __init__(self, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)
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
            Screen.on_message(self, _type, *args)

    def draw(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glColor4f(1, 1, 1, self.bg_alpha.value)
        self.bg.blit(0, 0)
        self.draw_subcontrols()

class GameHallScreen(Screen):
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
                Executive.call('create_game', ui_message, ['THBattle', u'我的游戏'])

            @self.btn_quickstart.event
            def on_click():
                Executive.call('quick_start_game', ui_message, 'THBattle')

            @self.btn_refresh.event
            def on_click():
                Executive.call('get_hallinfo', ui_message, None)

            @self.gamelist.event
            def on_item_dblclick(li):
                Executive.call('join_game', ui_message, li.game_id)

        def on_message(self, _type, *args):
            if _type == 'current_games':
                from gamepack import gamemodes as modes
                current_games = args[0]
                glist = self.gamelist
                glist.clear()
                for gi in current_games:
                    gcls = modes.get(gi['type'], None)
                    if gcls:
                        gname = gcls.name
                        n_persons = gcls.n_persons
                    else:
                        gname = u'未知游戏类型'
                        n_persons = 0

                    li = glist.append([
                        gi['id'],
                        gi['name'],
                        gname,
                        '%d/%d' % (
                            gi['nplayers'],
                            n_persons,
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

    class OnlineUsers(Dialog):
        def __init__(self, parent):
            Dialog.__init__(
                self, parent=parent,
                caption=u'当前在线玩家',
                x=750, y=220, width=240, height=420,
                bot_reserve=10,
            )
            self.btn_close.state = Button.DISABLED
            self.box = TextArea(
                parent=self, x=2, y=12, width=240-4, height=420-24-2-10
            )

        def on_message(self, _type, *args):
            lookup = {
                'hang': u'|c0000ffff游戏大厅|r',
                'ingame': u'|G游戏中|r',
                'inroomwait': u'|R在房间中|r',
                'ready': u'|c9f5f9fff准备状态|r',
            }
            if _type == 'current_users':
                users = args[0]
                box = self.box
                box.text = u'\u200b'
                self.caption = u'当前在线玩家：%d' % len(users)
                self.update()
                t = u'\n'.join(
                    u'%s(%s)' % (username, lookup.get(state, state))
                    for uid, username, state in users
                )
                box.append(t)

    def __init__(self, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)
        self.bg = common_res.bg_gamehall

        self.gamelist = self.GameList(self)

        chat = self.chat_box = GameHallScreen.ChatBox(parent=self)
        chat.text = u'您现在处于游戏大厅！\n'
        self.playerlist = GameHallScreen.OnlineUsers(parent=self)
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
            mapping = {
                'cant_join_game': u'无法加入游戏！'
            }
            ConfirmBox(mapping.get(args[0], args[0]), parent=self)
        else:
            Screen.on_message(self, _type, *args)

    def draw(self):
        #glColor3f(.9, .9, .9)
        glColor3f(1,1,1)
        self.bg.blit(0, 0)
        self.draw_subcontrols()

class GameScreen(Screen):
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
            for x, y, color in parent.ui_class.portrait_location:
                l.append(PlayerPortrait('NONAME', parent=self, x=x, y=y, color=color))
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
                name = p.get('username', 'EMPTY SLOT')
                if p.get('state', False) == 'ready': name = u'(准备)' + name
                self.portraits[i].player_name = name
                self.portraits[i].update()

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
        Screen.__init__(self, *args, **kwargs)

        self.bg = common_res.bg_ingame

        self.game = game
        self.ui_class = game.get_ui_class()
        self.gameui = self.ui_class(
            parent=False, game=game,
            **r2d((0, 0, 820, 720))
        ) # add when game starts

        self.events_box = GameScreen.EventsBox(parent=self)
        self.chat_box = GameScreen.ChatBox(parent=self)
        self.panel = GameScreen.RoomControlPanel(parent=self)
        self.btn_exit = Button(
            parent=self, caption=u'退出房间', zindex=1,
            **r2d((730, 670, 75, 25))
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
        elif _type == 'game_crashed':
            ConfirmBox(u'游戏逻辑已经崩溃，请退出房间！\n这是不正常的状态，你可以报告bug。', parent=self)
        else:
            Screen.on_message(self, _type, *args)

    def draw(self):
        glColor3f(1,1,1)
        self.bg.blit(0, 0)
        self.draw_subcontrols()
