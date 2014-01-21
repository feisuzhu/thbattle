# -*- coding: utf-8 -*-

# -- stdlib --
import logging
log = logging.getLogger('UI_Screens')
from collections import deque
import shlex
import re

# -- third party --
import pyglet
from pyglet.gl import glClear, glClearColor, glColor3f, glColor4f, GL_COLOR_BUFFER_BIT, glRectf
from pyglet.text import Label

# -- own --
from client.ui.base import WINDOW_WIDTH, WINDOW_HEIGHT, Control, Overlay, ui_message
from client.ui.base.interp import CosineInterp, InterpDesc, LinearInterp
from client.ui.controls import BalloonPromptMixin, Button, Colors, ConfirmBox, Frame, VolumeTuner
from client.ui.controls import ImageSelector, ListView, Panel
from client.ui.controls import PasswordTextBox, PlayerPortrait
from client.ui.controls import TextArea, TextBox, SensorLayer
from client.ui.resource import resource as common_res
from client.ui.soundmgr import SoundManager

from client.core import Executive
from utils import rect_to_dict as r2d, textsnap, inpoly, openurl
from user_settings import UserSettings
from account import Account
from settings import ServerNames

RE_AT = re.compile(ur'@([^@ ]+)')

def handle_chat(_type, args):
    if _type in ('chat_msg', 'ob_msg'):
        uname, msg = args[0]
        uname = uname.replace('|', '||')
        
        if Executive.gamemgr.account.username in RE_AT.findall(msg):
            from utils.notify import notify, AT

            notify(u'东方符斗祭 - 有人@您哦',
                   u'%s: %s' % (uname, msg), level = AT)

        style = '|cff0000ff' if _type == 'chat_msg' else '|c9f5f9fff'
        return u'%s%s|r：%s\n' % (style, uname, msg)

    elif _type == 'speaker_msg':
        node, uname, msg = args[0]
        from utils.notify import notify, SPEAKER
        notify(u'东方符斗祭 - 『文々。新闻』',
               u'%s: %s' % (uname, msg), level=SPEAKER)
        node = node and '|G%s' % ServerNames.get(node, node)
        uname = uname.replace('|', '||')
        return u'%s|ccc3299ff『文々。新闻』|cff0000ff%s|r： %s\n' % (node, uname, msg)

    elif _type == 'system_msg':
        _, msg = args[0]
        return u'|B|R%s|r\n' % msg

    else:
        return None


class ChatBoxFrame(Frame):
    history_limit = 1000
    history = deque([None] * history_limit)

    def __init__(self, **k):
        Frame.__init__(
            self,
            caption=u'系统/聊天信息',
            bot_reserve=33, **k
        )
        self.box = TextArea(
            parent=self, x=2, y=33+2, width=self.width, height=self.height-24-2-33
        )
        self.inputbox = TextBox(
            parent=self, x=6, y=6, width=self.width-12, height=22,
        )
        self.history_cursor = -1
        self.last_input = u''
        self.box.text = u'|R输入/?可以查看可用命令|r\n'

        @self.inputbox.event
        def on_text_motion(motion):
            hist = self.history
            cursor = self.history_cursor
            box = self.inputbox
            from pyglet.window import key
            if motion == key.MOTION_UP:
                cursor += 1
                if not cursor:
                    self.last_input = box.text

                text = hist[cursor]
                if text:
                    self.history_cursor = cursor
                    box.text = text
                    box.caret.position = len(text)

            if motion == key.MOTION_DOWN:
                if cursor < 0: return
                cursor -= 1

                if cursor < 0:
                    self.history_cursor = -1
                    box.text = self.last_input

                    return

                text = hist[cursor]
                if text:
                    box.text = text
                    box.caret.position = len(text)
                    self.history_cursor = cursor
                else:
                    self.history_cursor = -1

        @self.inputbox.event
        def on_enter():
            text = unicode(self.inputbox.text)
            self.inputbox.text = u''
            if not text: return

            self.add_history(text)
            if text.startswith(u'`') and len(text) > 1:
                text = text[1:]
                if not text: return
                Executive.call('speaker', ui_message, text)
            elif text.startswith(u'/'):
                from . import commands
                cmdline = shlex.split(text[1:])
                msg = commands.process_command(cmdline)
                msg and self.append(msg)
            else:
                Executive.call('chat', ui_message, text)

    def append(self, v):
        self.box.append(v)

    def add_history(self, text):
        self.history_cursor = -1
        hist = self.__class__.history
        hist.rotate(1)
        hist[0] = text
        hist[-1] = None

    def set_color(self, color):
        Frame.set_color(self, color)
        self.inputbox.color = color


class Screen(Overlay):
    def on_message(self, _type, *args):
        if _type == 'server_dropped':
            ConfirmBox(u'已经与服务器断开链接，请重新启动游戏！', parent=Screen.cur_overlay)

        elif _type == 'invite_request':
            from user_settings import UserSettings as us
            if us.no_invite: return

            uid, uname, gid, gtype = args[0]
            from gamepack import gamemodes as modes

            gtype = modes.get(gtype, None)
            gtype = gtype and gtype.ui_meta.name

            invite_text = u'%s 邀请你一起玩 %s 模式' % (uname, gtype)

            from utils import notify
            notify(u'东方符斗祭 - 邀请提醒', invite_text)

            box = ConfirmBox(
                invite_text, timeout=20,
                parent=self, buttons=((u'确定', True), (u'取消', False)), default=False
            )

            @box.event
            def on_confirm(val, uid=uid):
                Executive.call('invite_grant', ui_message, [gid, val])

        else:
            Overlay.on_message(self, _type, *args)


class UpdateScreen(Screen):
    trans = dict(
        update_begin=lambda: u'|W开始更新……|r',
        up2date=lambda: u'|W已经是最新版本了|r',
        delete_file=lambda fn: u'|W删除：|LB%s|r' % fn,
        download_file=lambda fn: u'|W下载：|LB%s|r' % fn,
        download_complete=lambda fn: u'|W下载完成：|LB%s|r' % fn,
        write_failed=lambda fn: u'|R无法写入：|LB%s|r' % fn,
        update_finished=lambda: u'|W更新完成|r',
        http_error=lambda code, url: u'|RHTTP错误： %d %s|r' % (code, url),
        network_error=lambda: u'|R网络错误|r',
        io_error=lambda: u'|R系统错误|r',  # WHATEVER
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
        self.worldmap = common_res.worldmap.get()

        from settings import ServerList, NOTICE

        class NoticePanel(Panel):
            fill_color = (1.0, 1.0, 0.9, 0.5)

            def __init__(self, text, *a, **k):
                Panel.__init__(self, *a, **k)
                self.zindex = 100
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

        screen = self

        class HighlightLayer(SensorLayer, BalloonPromptMixin):
            zindex = 0
            hl_alpha = InterpDesc('_hl_alpha')

            def __init__(self, *a, **k):
                SensorLayer.__init__(self, *a, **k)
                BalloonPromptMixin.__init__(self)
                from base.baseclasses import main_window
                self.window = main_window
                self.hand_cursor = self.window.get_system_mouse_cursor('hand')
                self.worldmap_shadow = common_res.worldmap_shadow.get()
                self.disable_click = False
                self.highlight = None
                self.hldraw = None
                self.hl_alpha = 0
                self.hlhit = False

            def on_mouse_motion(self, x, y, dx, dy):
                for s in ServerList.values():
                    if inpoly(x, y, s['polygon']):
                        self.hl_alpha = 1
                        if self.highlight is not s:
                            self.highlight = s
                            self.init_balloon(s['description'], polygon=s['polygon'])
                            x, y, w, h = s['box']
                            tex = self.worldmap_shadow.get_region(x, y, w, h)
                            self.hldraw = (x, y, tex)
                            self.window.set_mouse_cursor(self.hand_cursor)

                        break
                else:
                    if self.highlight:
                        self.highlight = None
                        self.hl_alpha = LinearInterp(1.0, 0, 0.3)
                        self.window.set_mouse_cursor(None)

                    self.init_balloon('', (0, 0, 0, 0))

            def on_mouse_release(self, x, y, button, modifiers):
                if self.highlight and not self.disable_click:
                    self.disable_click = True
                    screen.do_connect(self.highlight['address'])

            def enable_click(self):
                self.disable_click = False

            def draw(self):
                hla = self.hl_alpha
                if hla and not self.disable_click:
                    x, y, tex = self.hldraw
                    glColor4f(1, 1, 1, hla)
                    tex.blit(x, y)

        NoticePanel(
            NOTICE,
            parent=self,
            width=800, height=600,
            x=(self.width-800)//2, y=(self.height-600)//2
        )

        self.highlight_layer = HighlightLayer(parent=self)

        VolumeTuner(parent=self, x=self.width - 90, y=60)

    def do_connect(self, addr):
        Executive.call('connect_server', ui_message, addr, ui_message)

    def on_message(self, _type, *args):
        if _type == 'server_connected':
            login = LoginScreen()
            login.switch()
        elif _type == 'server_connect_failed':
            self.highlight_layer.enable_click()
            log.error('Server connect failed.')
            ConfirmBox(u'服务器连接失败！', parent=self)
        elif _type == 'version_mismatch':
            self.highlight_layer.enable_click()
            log.error('Version mismatch')
            ConfirmBox(u'您的版本与服务器版本不符，无法进行游戏！', parent=self)
        else:
            Screen.on_message(self, _type, *args)

    def draw(self):
        #glColor3f(0.9, 0.9, 0.9)
        glColor3f(1, 1, 1)
        self.worldmap.blit(0, 0)
        self.draw_subcontrols()

    def on_switch(self):
        SoundManager.switch_bgm(common_res.bgm_hall)
        from options import options

        options.testing and ConfirmBox(
            u'测试模式开启，现在可以登陆测试服务器。\n'
            u'测试模式下可能无法登陆正常服务器，\n'
            u'测试服务器也会随时重新启动。',
            parent=self, zindex=99999,
        )


class LoginScreen(Screen):
    class LoginDialog(Frame):
        def __init__(self, *a, **k):
            Frame.__init__(
                self, u'登陆', x=350, y=165,
                width=325, height=184,
                bot_reserve=50, *a, **k
            )

            def L(text, x, y, *a, **k):
                self.add_label(
                    text, x=x, y=y,
                    font_size=9, color=(0, 0, 0, 255),
                    bold=True, anchor_x='left', anchor_y='bottom',
                    *a, **k
                )

            L(u'用户名：', 368 - 350, 286 - 165)
            L(u'密码：', 368 - 350, 250 - 165)

            self.txt_username = TextBox(
                parent=self, x=438-350, y=282-165, width=220, height=20,
                text=UserSettings.last_id,
            )
            self.txt_pwd = PasswordTextBox(
                parent=self, x=438-350, y=246-165, width=220, height=20,
                text='',
            )
            self.btn_login = Button(
                parent=self, caption=u'进入幻想乡',
                x=50, y=10, width=100, height=30
            )
            self.btn_reg = Button(
                parent=self, caption=u'乡民登记',
                color=Colors.orange,
                x=175, y=10, width=100, height=30
            )

            @self.btn_login.event
            def on_click():
                self.do_login()

            @self.txt_pwd.event
            def on_enter():
                self.do_login()

            @self.btn_reg.event  # noqa
            def on_click():
                openurl('http://www.thbattle.net')

        def do_login(self):
            u, pwd = self.txt_username.text, self.txt_pwd.text
            Executive.call('auth', ui_message, [u, pwd])

    def __init__(self, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)
        self.bg = common_res.bg_login.get()
        self.bg_alpha = LinearInterp(0, 1.0, 1.5)
        self.dialog = LoginScreen.LoginDialog(parent=self)
        try_game = Button(
            parent=self, caption=u'试玩',
            x=750, y=50, width=100, height=30, color=Colors.orange,
        )

        @try_game.event
        def on_click():
            text = (
                u'试玩的玩家有以下限制：\n'
                u'\n'
                u'随机的id，不记录游戏数和节操\n'
                u'固定的头像、自定义签名\n'
                u'无法使用文文新闻和邀请功能\n'
                u'无法断线重连'
            )

            confirm = ConfirmBox(text, buttons=ConfirmBox.Presets.OKCancel, parent=self)

            @confirm.event
            def on_confirm(val):
                val and Executive.call('auth', ui_message, ['-1', 'guest'])

    def on_message(self, _type, *args):
        if _type == 'auth_success':
            UserSettings.last_id = self.dialog.txt_username.text
            GameHallScreen().switch()

        elif _type == 'auth_failure':
            log.error('Auth failure')
            status = args[0]
            tbl = dict(
                not_available=u'您的帐号目前不可用，请联系管理员询问！',
                already_logged_in=u'请不要重复登录！',
                invalid_credential=u'认证失败！',
            )
            ConfirmBox(tbl.get(status, status), parent=self)
        else:
            Screen.on_message(self, _type, *args)

    def draw(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        glColor4f(1, 1, 1, self.bg_alpha.value)
        self.bg.blit(0, 0)
        self.draw_subcontrols()

    def on_switch(self):
        SoundManager.switch_bgm(common_res.bgm_hall)


class GameHallScreen(Screen):
    class GameList(Frame):
        class CreateGamePanel(Panel):
            def __init__(self, *a, **k):
                w, h = 550, 485
                Panel.__init__(
                    self, width=w, height=h,
                    zindex=1000,
                    *a, **k
                )
                self.x = (self.overlay.width - w) // 2
                self.y = (self.overlay.height - h) // 2

                self.btncreate = btncreate = Button(
                    u'创建游戏', parent=self, x=440, y=75, width=90, height=40
                )
                self.btncancel = btncancel = Button(
                    u'取消', parent=self, x=440, y=25, width=90, height=40
                )
                btncreate.state = Button.DISABLED

                txtbox = self.txtgamename = TextBox(
                    parent=self, x=95, y=395, width=420, height=22,
                )
                uname = Executive.gamemgr.account.username

                f = pyglet.font.load('AncientPix', 9)

                un1 = textsnap(uname, f, 140)

                if un1 != uname:
                    uname = textsnap(uname, f, 120) + u'…'
                txtbox.text = uname + u'的游戏'

                self.labels = batch = pyglet.graphics.Batch()
                Label(
                    u'创建游戏房间', font_size=12, x=275, y=431,
                    anchor_x='center', anchor_y='bottom',
                    color=Colors.green.heavy + (255, ),
                    shadow=(1, 207, 240, 156, 204),
                    batch=batch,
                ),
                Label(
                    u'房间名称：', font_size=9, x=30, y=400,
                    anchor_x='left', anchor_y='bottom',
                    color=Colors.green.heavy + (255, ),
                    shadow=(1, 207, 240, 156, 204),
                    batch=batch,
                )

                from gamepack import gamemodes as modes

                self.selectors = selectors = []

                def on_select():
                    btncreate.state = Button.NORMAL

                for i, (gname, gcls) in enumerate(modes.items()):
                    y, x = divmod(i, 3)
                    x, y = 30 + 170*x, 275 - 125*y
                    s = ImageSelector(
                        gcls.ui_meta.logo, selectors,
                        parent=self, x=x, y=y
                    )
                    intro = getattr(gcls.ui_meta, 'description', None)
                    intro and s.init_balloon(intro, width=480)
                    s.gametype = gname
                    s.event(on_select)
                    selectors.append(s)

                @btncreate.event
                def on_click():
                    gtype = ImageSelector.get_selected(selectors).gametype
                    f = pyglet.font.load('AncientPix', 9)
                    roomname = textsnap(txtbox.text, f, 200)
                    Executive.call('create_game', ui_message, [gtype, roomname])

                @btncancel.event  # noqa
                def on_click():
                    self.delete()

            def draw(self):
                Panel.draw(self)
                self.labels.draw()

        class ObserveGamePanel(Panel):
            def __init__(self, game_id, *a, **k):
                Panel.__init__(
                    self, width=550, height=340,
                    zindex=10000,
                    *a, **k
                )
                self.game_id = game_id
                self.x = (self.overlay.width - 550) // 2
                self.y = (self.overlay.height - 340) // 2

                self.btncancel = btncancel = Button(
                    u'取消', parent=self, x=440, y=25, width=90, height=40
                )

                self.labels = pyglet.graphics.Batch()

                Label(
                    u'旁观游戏', font_size=12, x=275, y=306,
                    anchor_x='center', anchor_y='bottom',
                    color=Colors.green.heavy + (255, ),
                    shadow=(2, 207, 240, 156, 204),
                    batch=self.labels,
                )

                @btncancel.event
                def on_click():
                    self.delete()

                Executive.call('query_gameinfo', ui_message, game_id)

            def draw(self):
                Panel.draw(self)
                self.labels.draw()

            def on_message(self, _type, *args):
                if _type == 'gameinfo':
                    gid, ul = args[0]
                    if gid != self.game_id: return

                    ul = [i for i in ul if i['state'] not in ('dropped', 'fleed')]

                    for i, p in enumerate(ul):
                        y, x = divmod(i, 5)
                        x, y = 30 + 100*x, 250 - 60*y
                        acc = Account.parse(p['account'])
                        s = Button(
                            acc.username,
                            color=Colors.orange,
                            parent=self, x=x, y=y,
                            width=95, height=30,
                        )
                        s.userid = acc.userid

                        @s.event
                        def on_click(uid=acc.userid, un=acc.username):
                            Executive.call('observe_user', ui_message, uid)
                            self.overlay.chat_box.append(u'|R已经向%s发送了旁观请求，请等待回应……|r\n' % un)
                            self.delete()

        def __init__(self, p):
            Frame.__init__(
                self, parent=p, caption=u'当前大厅内的游戏',
                x=35, y=220, width=700, height=420,
                bot_reserve=30, bg=common_res.bg_gamelist.get(),
            )

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
                self.CreateGamePanel(parent=self.overlay)

            @self.btn_quickstart.event  # noqa
            def on_click():
                Executive.call('quick_start_game', ui_message, 'THBattle')

            @self.btn_refresh.event  # noqa
            def on_click():
                Executive.call('get_hallinfo', ui_message, None)

            @self.gamelist.event
            def on_item_dblclick(li):
                # TODO:
                if li.started:
                    #Executive.call('observe_user', ui_message, li.game_id)
                    self.ObserveGamePanel(li.game_id, parent=self.overlay)
                else:
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
                        gname = gcls.ui_meta.name
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
                    ], color=(0, 0, 0, 255) if gi['started'] else (0xef, 0x75, 0x45, 0xff))
                    li.game_id = gi['id']
                    li.started = gi['started']

    class ChatBox(ChatBoxFrame):
        def __init__(self, parent):
            ChatBoxFrame.__init__(
                self, parent=parent,
                #x=35, y=20, width=700, height=180,
                x=35+255, y=20, width=700-255, height=180,
            )

    class OnlineUsers(Frame):
        def __init__(self, parent):
            Frame.__init__(
                self, parent=parent,
                caption=u'当前在线玩家',
                x=750, y=220, width=240, height=420,
                bot_reserve=10,
            )
            self.box = TextArea(
                parent=self, x=2, y=12, width=240-4, height=420-24-2-10
            )

        def on_message(self, _type, *args):
            lookup = {
                'hang': u'|c0000ffff游戏大厅|r',
                'ingame': u'|G游戏中|r',
                'inroomwait': u'|R在房间中|r',
                'ready': u'|c9f5f9fff准备状态|r',
                'observing': u'|LB观战中|r',
            }
            if _type == 'current_users':
                users = args[0]
                box = self.box
                box.text = u'\u200b'
                self.caption = u'当前在线玩家：%d' % len(users)
                self.update()
                t = u'\n'.join(
                    u'%s([|c9100ffff%s|r], %s)' % (username.replace('|', '||'), uid, lookup.get(state, state))
                    for uid, username, state in users
                )
                box.append(t)

    class NoticeBox(Frame):
        def __init__(self, parent):
            Frame.__init__(
                self, x=750, y=20, width=240, height=180,
                caption=u'花果子念报', parent=parent,
            )
            ta = self.textarea = TextArea(
                parent=self, x=2, y=10+2, width=240-4, height=180-24-2-10
            )
            ta.text = u'正在获取最新新闻……'

            def update(rst):
                if rst:
                    _, content = rst
                    try:
                        ta.text = content.decode('utf-8')
                        return
                    except Exception as e:
                        import traceback
                        traceback.print_exc(e)

                ta.text = u'|R无法显示新闻！|r'

            from settings import HALL_NOTICE_URL
            Executive.call('fetch_resource', update, HALL_NOTICE_URL)

    class StatusBox(Frame):
        def __init__(self, parent):
            Frame.__init__(
                self, x=35, y=20, width=240, height=180,
                caption=u'帐号信息', parent=parent,
            )
            self.textarea = TextArea(
                parent=self, x=2, y=10+2, width=240-4, height=180-24-2-10
            )

        def on_message(self, _type, *args):
            if _type == 'your_account':
                acc = Executive.gamemgr.account
                ta = self.textarea
                ta.text = u'\u200b'
                f = u'|c0000ffff%s：|r %s\n'
                ta.append(f % (u'UID', acc.userid))
                ta.append(f % (u'用户名', acc.username))
                ta.append(f % (u'节操', acc.other['credits']))
                ta.append(f % (u'游戏数', acc.other['games']))
                ta.append(f % (u'逃跑数', acc.other['drops']))
                ta.append(f % (u'称号', acc.other['title']))

    def __init__(self, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)
        self.bg = common_res.bg_gamehall.get()

        self.gamelist = self.GameList(self)

        chat = self.chat_box = GameHallScreen.ChatBox(parent=self)
        chat.text = u'您现在处于游戏大厅！\n'
        self.playerlist = GameHallScreen.OnlineUsers(parent=self)
        self.noticebox = GameHallScreen.NoticeBox(parent=self)
        self.statusbox = GameHallScreen.StatusBox(parent=self)

        VolumeTuner(parent=self, x=850, y=660)

        b = Button(parent=self,
            x=750, y=660, width=80, height=35,
            color=Colors.orange, caption=u'卡牌查看器',
        )

        @b.event
        def on_click():
            openurl('http://thb.io')

        Executive.call('get_hallinfo', ui_message, None)

    def on_message(self, _type, *args):
        rst = handle_chat(_type, args)
        if rst:
            self.chat_box.append(rst)
            return

        elif _type == 'game_joined':
            GameScreen(args[0]).switch()

        elif _type == 'gamehall_error':
            log.error('GameHall Error: %s' % args[0])  # TODO
            mapping = {
                'cant_join_game': u'无法加入游戏！'
            }
            ConfirmBox(mapping.get(args[0], args[0]), parent=self)

        elif _type == 'observe_refused':
            uname = args[0]
            self.chat_box.append(u'|R%s 回绝了你的旁观请求|r\n' % uname)

        else:
            Screen.on_message(self, _type, *args)

    def draw(self):
        #glColor3f(.9, .9, .9)
        glColor3f(1, 1, 1)
        self.bg.blit(0, 0)
        self.draw_subcontrols()

    def on_switch(self):
        SoundManager.switch_bgm(common_res.bgm_hall)


class GameScreen(Screen):
    flash_alpha = InterpDesc('_flash_alpha')

    class InvitePanel(Panel):
        def __init__(self, game_id, *a, **k):
            Panel.__init__(
                self, width=550, height=340,
                zindex=10000,
                *a, **k
            )
            self.game_id = game_id
            self.x = (self.overlay.width - 550) // 2
            self.y = (self.overlay.height - 340) // 2

            self.btncancel = btncancel = Button(
                u'关闭', parent=self, x=440, y=25, width=90, height=40
            )

            self.labels = pyglet.graphics.Batch()

            Label(
                u'邀请游戏', font_size=12, x=275, y=306,
                anchor_x='center', anchor_y='bottom',
                color=Colors.green.heavy + (255, ),
                shadow=(2, 207, 240, 156, 204),
                batch=self.labels,
            )

            @btncancel.event
            def on_click():
                self.delete()

            Executive.call('get_hallinfo', ui_message, None)

        def draw(self):
            Panel.draw(self)
            self.labels.draw()

        def on_message(self, _type, *args):
            if _type == 'current_users':
                ul = args[0]
                ul = [(uid, uname) for uid, uname, state in ul if state in ('hang', 'observing')]

                for i, (uid, uname) in enumerate(ul):
                    y, x = divmod(i, 5)
                    x, y = 30 + 100*x, 250 - 60*y
                    s = Button(
                        uname,
                        color=Colors.orange,
                        parent=self, x=x, y=y,
                        width=95, height=30,
                    )

                    @s.event
                    def on_click(s=s, uid=uid, un=uname):
                        Executive.call('invite_user', ui_message, uid)
                        self.overlay.chat_box.append(u'|R已经邀请了%s，请等待回应……|r\n' % un)
                        s.state = Button.DISABLED

    class RoomControlPanel(Control):
        def __init__(self, parent=None):
            Control.__init__(self, parent=parent, **r2d((0, 0, 820, 720)))
            self.btn_getready = Button(
                parent=self, caption=u'准备', **r2d((360, 80, 100, 35))
            )

            self.btn_invite = Button(
                parent=self, caption=u'邀请', **r2d((360, 40, 100, 35))
            )

            self.ready = False

            l = []

            class MyPP(PlayerPortrait):
                # this class is INTENTIONALLY put here
                # to make cached avatars get gc'd
                cached_avatar = {}

            for x, y, color in parent.ui_class.portrait_location:
                l.append(MyPP('NONAME', parent=self, x=x, y=y, color=color))
            self.portraits = l

            @self.btn_getready.event
            def on_click():
                if self.ready:
                    Executive.call('cancel_ready', ui_message, [])
                    self.ready = False
                    self.btn_getready.caption = u'准备'
                    self.btn_getready.update()
                else:
                    Executive.call('get_ready', ui_message, [])
                    #self.btn_getready.state = Button.DISABLED
                    self.ready = True
                    self.btn_getready.caption = u'取消准备'
                    self.btn_getready.update()

            @self.btn_invite.event  # noqa
            def on_click():
                GameScreen.InvitePanel(self.parent.game.gameid, parent=self)

        def draw(self):
            self.draw_subcontrols()

        def on_message(self, _type, *args):
            if _type == 'player_change':
                self.update_portrait(args[0])
            elif _type == 'kick_request':
                u1, u2, count = args[0]
                self.parent.chat_box.append(
                    u'|B|R>> |c0000ffff%s|r希望|c0000ffff|B%s|r离开游戏，已有%d人请求\n' % (
                        u1[1], u2[1], count
                    )
                )
            elif _type == 'game_joined':
                self.ready = False
                self.btn_getready.caption = u'准备'
                self.btn_getready.state = Button.NORMAL

                for p in self.portraits:
                    p.account = None

        def update_portrait(self, pl):
            def players():
                return {
                    p.account.username
                    for p in self.portraits
                    if p.account
                }

            orig_players = players()
            full = True

            for i, p in enumerate(pl):
                accdata = p['account']
                acc = Account.parse(accdata) if accdata else None
                if not accdata: full = False

                port = self.portraits[i]
                port.account = acc
                port.ready = (p['state'] == 'ready')

                port.update()

            curr_players = players()

            for player in (orig_players - curr_players):
                self.parent.chat_box.append(
                    u'|B|R>> |r玩家|c0000ffff|B%s|r已离开游戏\n' % player
                )

            for player in (curr_players - orig_players):
                self.parent.chat_box.append(
                    u'|B|R>> |r玩家|c0000ffff|B%s|r已进入游戏\n' % player
                )

            if not self.ready and full and orig_players != curr_players:
                if Executive.gamemgr.account.username in curr_players:
                    from utils import notify
                    notify(u'东方符斗祭 - 满员提醒', u'房间已满员，请准备。')

    class EventsBox(Frame):
        def __init__(self, parent):
            Frame.__init__(
                self, parent=parent,
                caption=u'游戏信息',
                x=820, y=350, width=204, height=370,
                bot_reserve=0, bg=common_res.bg_eventsbox.get(),
            )
            self.box = TextArea(
                parent=self, x=2, y=2, width=200, height=370-24-2
            )

        def append(self, v):
            self.box.append(v)

        def clear(self):
            self.box.text = u'\u200b'

    class ChatBox(ChatBoxFrame):
        def __init__(self, parent):
            ChatBoxFrame.__init__(
                self, parent=parent,
                x=820, y=0, width=204, height=352,
                bg=common_res.bg_chatbox.get(),
            )

    def __init__(self, game, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)

        self.backdrop = common_res.bg_ingame.get()
        self.flash_alpha = 0.0

        self.game = game
        self.ui_class = game.ui_meta.ui_class
        self.gameui = self.ui_class(
            parent=False, game=game,
            **r2d((0, 0, 820, 720))
        )  # add when game starts

        self.events_box = GameScreen.EventsBox(parent=self)
        self.chat_box = GameScreen.ChatBox(parent=self)
        self.panel = GameScreen.RoomControlPanel(parent=self)
        self.btn_exit = Button(
            parent=self, caption=u'退出房间', zindex=1,
            **r2d((730, 670, 75, 25))
        )

        VolumeTuner(parent=self, x=690, y=665)

        @self.btn_exit.event
        def on_click():
            box = ConfirmBox(u'真的要离开吗？', buttons=ConfirmBox.Presets.OKCancel, parent=self)

            @box.event
            def on_confirm(val):
                if val:
                    Executive.call('exit_game', ui_message, [])

    def on_message(self, _type, *args):
        rst = handle_chat(_type, args)
        if rst:
            self.chat_box.append(rst)
            return

        elif _type == 'game_started':
            from utils import notify
            notify(u'东方符斗祭 - 游戏提醒', u'游戏已开始，请注意。')
            self.remove_control(self.panel)
            self.add_control(self.gameui)
            self.gameui.init()
            self.game.start()

        elif _type == 'end_game':
            self.remove_control(self.gameui)
            self.add_control(self.panel)
            g = args[0]

        elif _type == 'client_game_finished':
            g = args[0]
            g.ui_meta.ui_class.show_result(g)

        elif _type in ('game_left', 'fleed'):
            GameHallScreen().switch()

        elif _type == 'game_joined':
            # last game ended, this is the auto
            # created game
            self.game = args[0]
            self.panel.btn_getready.state = Button.NORMAL
            self.gameui = self.ui_class(
                parent=False, game=self.game,
                **r2d((0, 0, 820, 720))
            )
            SoundManager.switch_bgm(common_res.bgm_hall)
            self.backdrop = common_res.bg_ingame.get()
            self.set_color(Colors.green)
            self.events_box.clear()

        elif _type == 'game_crashed':
            ConfirmBox(
                u'游戏逻辑已经崩溃，请退出房间！\n'
                u'这是不正常的状态，你可以报告bug。\n'
                u'游戏ID：%d' % self.game.gameid,
                parent=self
            )
            from __main__ import do_crashreport
            do_crashreport()

        elif _type == 'observe_request':
            uid, uname = args[0]
            box = ConfirmBox(
                u'玩家 %s 希望旁观你的游戏，是否允许？\n'
                u'旁观玩家可以看到你的手牌。' % uname, timeout=20,
                parent=self, buttons=((u'允许', True), (u'不允许', False)), default=False
            )

            @box.event
            def on_confirm(val, uid=uid):
                Executive.call('observe_grant', ui_message, [uid, val])

        elif _type == 'observer_enter':
            obuid, obname, uname = args[0]
            self.chat_box.append(
                u'|B|R>> |r|c0000ffff%s|r[|c9100ffff%d|r]|r趴在了|c0000ffff%s|r身后\n' % (obname, obuid, uname)
            )

        elif _type == 'observer_leave':
            obuid, obname, uname = args[0]
            self.chat_box.append(
                u'|B|R>> |r|c0000ffff%s|r飘走了\n' % obname
            )

        else:
            Screen.on_message(self, _type, *args)

    def draw(self):
        glColor3f(1, 1, 1)
        self.backdrop.blit(0, 0)
        glColor4f(0, 0, 0, .5)
        glRectf(0, 0, 1000, 138)
        glColor3f(0.1922, 0.2706, 0.3882)
        glRectf(0, 138, 1000, 140)
        glColor3f(1, 1, 1)
        self.draw_subcontrols()
        fa = self.flash_alpha
        if fa:
            glColor4f(1, 1, 1, fa)
            glRectf(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    def set_flash(self, duration):
        self.flash_alpha = CosineInterp(1.0, 0.0, duration)

    def set_color(self, color):
        self.events_box.set_color(color)
        self.chat_box.set_color(color)

    def on_switch(self):
        SoundManager.switch_bgm(common_res.bgm_hall)
