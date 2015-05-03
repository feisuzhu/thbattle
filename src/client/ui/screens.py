# -*- coding: utf-8 -*-

# -- stdlib --
from collections import deque
import logging
import os
import re
import shlex
import sys

# -- third party --
from gevent.event import Event
from pyglet.gl import GL_COLOR_BUFFER_BIT, glClear, glClearColor, glColor3f, glColor4f, glRectf
from pyglet.text import Label
import gevent
import pyglet
import requests

# -- own --
from account import Account
from client.core.executive import Executive
from client.core.replay import Replay
from client.ui.base import Control, Overlay, WINDOW_HEIGHT, WINDOW_WIDTH, ui_message
from client.ui.base.interp import CosineInterp, InterpDesc, LinearInterp
from client.ui.controls import BalloonPrompt, Button, CheckBox, Colors, ConfirmBox, Frame
from client.ui.controls import ImageButton, ImageSelector, ListView, LoadingWindow, NoInviteButton
from client.ui.controls import OptionButtonGroup, Panel, PasswordTextBox, PlayerPortrait
from client.ui.controls import SensorLayer, TextArea, TextBox, VolumeTuner
from client.ui.resloader import L
from client.ui.soundmgr import SoundManager
from game.autoenv import EventHandler
from options import options
from settings import ServerNames
from user_settings import UserSettings
from utils import inpoly, openurl, rect_to_dict as r2d, textsnap
from utils.crypto import simple_decrypt, simple_encrypt
from utils.filedlg import get_open_file_name, get_save_file_name
from utils.misc import BatchList

# -- code --
# -- code --
RE_AT = re.compile(ur'@([^@ ]+)')
log = logging.getLogger('UI_Screens')


def handle_chat(_type, args):
    if _type in ('chat_msg', 'ob_msg'):
        uname, msg = args[0]
        uname = uname.replace('|', '||')
        if uname in UserSettings.blocked_users:
            msg = u'***此人消息已屏蔽***'

        if Executive.gamemgr.account.username in RE_AT.findall(msg):
            from utils.notify import notify, AT

            notify(u'东方符斗祭 - 有人@您哦', u'%s: %s' % (uname, msg), level=AT)

        style = '|cff0000ff' if _type == 'chat_msg' else '|c9f5f9fff'
        return u'%s%s|r：%s\n' % (style, uname, msg)

    elif _type == 'speaker_msg':
        node, uname, msg = args[0]
        if uname in UserSettings.blocked_users:
            msg = u'***此人消息已屏蔽***'

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


def confirm(text, title, buttons):
    from gevent.event import AsyncResult
    rst = AsyncResult()
    box = ConfirmBox(text, title, buttons, parent=Overlay.cur_overlay)

    @box.event
    def on_confirm(val):
        rst.set(val)
    return rst.get()


class ChatBox(Frame):
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

        self.set_capture('on_text')

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
                Executive.speaker(text)
            elif text.startswith(u'/'):
                from . import commands
                cmdline = shlex.split(text[1:])
                msg = commands.process_command(cmdline)
                msg and self.append(msg)
            else:
                Executive.chat(text)

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

    def on_text(self, text):
        if text == '\r' and self.overlay.current_focus is not self.inputbox:
            self.inputbox.text = u''
            self.inputbox.set_focus()


class Screen(Overlay):
    def on_message(self, _type, *args):
        if _type == 'server_dropped':
            c = ConfirmBox(u'已经与服务器断开链接，请重新启动游戏！', parent=Screen.cur_overlay)

            @c.event
            def on_confirm(v):
                Executive.disconnect()
                ServerSelectScreen().switch()

        elif _type == 'invite_request':
            uid, uname, gid, gtype = args[0]
            from user_settings import UserSettings as us
            if us.no_invite:
                Executive.invite_grant(gid, False)
                return

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
                Executive.invite_grant(gid, val)

        else:
            Overlay.on_message(self, _type, *args)


class UpdateScreen(Screen):
    def __init__(self, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)
        ta = TextArea(
            parent=self, width=600, height=450,
            x=(self.width-600)//2, y=(self.height-450)//2
        )
        self.textarea = ta
        self.update_gr = None

    def update_message(self, msg, arg):
        ta = self.textarea
        if msg == 'error':
            ta.append(u'|W更新出错：\n|R%s|r\n' % str(arg))
            return

        progress = self.format_progress(arg)
        if not progress:
            return

        if msg == 'logic_progress':
            ta.append(u'|W游戏更新：|LB%s|r\n' % progress)
        elif msg == 'interpreter_progress':
            ta.append(u'|W解释器更新：|LB%s|r\n' % progress)

    def format_progress(self, stat):
        if not stat.total_objects:
            return ''

        if stat.indexed_deltas:
            return ''

        return u'{}% ({}/{}), {:.2f} KiB'.format(
            int(100.0 * stat.received_objects / stat.total_objects),
            stat.received_objects,
            stat.total_objects,
            stat.received_bytes / 1024.0,
        )

    def draw(self):
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT)
        self.draw_subcontrols()

    def on_switch(self):
        self.textarea.append(u'|W正在更新……|r\n')

        def do_update():
            rst = Executive.update(self.update_message)
            box = None
            if rst == 'update_disabled':
                box = ConfirmBox(u'自动更新已经禁用', parent=self)
            elif rst == 'error':
                box = ConfirmBox(u'更新过程出现错误，你可能不能正常游戏！', parent=self)

            if box:
                @box.event
                def on_confirm(v):
                    ServerSelectScreen().switch()
            else:
                ServerSelectScreen().switch()

        self.update_gr = gevent.spawn(do_update)


class ReplayButton(ImageButton):
    def __init__(self, **k):
        ImageButton.__init__(self, L('c-buttons-replay'), 1, **k)

    def on_click(self):
        self.state = ImageButton.DISABLED

        @gevent.spawn
        def replay():
            from base.baseclasses import main_window
            filename = get_open_file_name(main_window, u'打开Replay', [(u'THB Replay 文件', u'*.thbrep')])
            if not filename:
                self.state = ImageButton.NORMAL
                return

            try:
                rep = Replay.loads(open(filename, 'rb').read())
            except Exception as e:
                log.exception(e)
                ConfirmBox(u'打开Replay失败！', u'Replay', parent=Overlay.cur_overlay)
                self.state = ImageButton.NORMAL
                return

            if not Executive.is_version_present(rep.client_version):
                ConfirmBox(
                    u'Replay中的客户端版本在本地没有找到，请确认是否更新到最新的客户端！', u'Replay',
                    parent=Overlay.cur_overlay,
                )
                self.state = ImageButton.NORMAL
                return

            if not Executive.is_version_match(rep.client_version):
                if confirm(u'你的游戏没有切换到相应的版本上，要切换吗？', u'Replay', ConfirmBox.Presets.OKCancel):
                    Executive.switch_version(rep.client_version)
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                    assert False, 'WTF'
                else:
                    self.state = ImageButton.NORMAL
                    return

            g = Executive.start_replay(rep, ui_message)
            ReplayScreen(g, rep).switch()


class ServerSelectScreen(Screen):

    def __init__(self, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)
        self.worldmap = L('c-bg_worldmap')

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

        class HighlightLayer(SensorLayer):
            zindex = 0
            hl_alpha = InterpDesc('_hl_alpha')

            def __init__(self, *a, **k):
                SensorLayer.__init__(self, *a, **k)
                self.balloon = BalloonPrompt(self)
                from base.baseclasses import main_window
                self.window = main_window
                self.hand_cursor = self.window.get_system_mouse_cursor('hand')
                self.worldmap_shadow = L('c-bg_worldmap_shadow')
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
                            self.balloon.set_balloon(s['description'], polygon=s['polygon'])
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

                    self.balloon.set_balloon('', (0, 0, 0, 0))

            def on_mouse_release(self, x, y, button, modifiers):
                if self.highlight and not self.disable_click:
                    self.disable_click = True
                    self.select_server(self.highlight)

            def select_server(self, server):
                @gevent.spawn
                def work():
                    if not options.no_update and not Executive.is_version_match(server['branch']):
                        if confirm(u'你的游戏没有切换到最新版上，要切换吗？', u'自动更新', ConfirmBox.Presets.OKCancel):
                            Executive.switch_version(server['branch'])
                            import os
                            import sys
                            os.execv(sys.executable, [sys.executable] + sys.argv)
                            assert False, 'WTF'

                    lw2 = LoadingWindow(u'正在连接服务器', parent=self.parent)
                    ui_message(Executive.connect_server(
                        server['address'], ui_message
                    ))
                    lw2.done()

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
        ReplayButton(parent=self, x=self.width - 220, y=60, zindex=1)

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
        # glColor3f(0.9, 0.9, 0.9)
        glColor3f(1, 1, 1)
        self.worldmap.blit(0, 0)
        self.draw_subcontrols()

    def on_switch(self):
        SoundManager.switch_bgm('c-bgm_hall')


class LoginScreen(Screen):
    class LoginDialog(Frame):
        def __init__(self, *a, **k):
            Frame.__init__(
                self, u'登陆', x=350, y=165,
                width=325, height=184,
                bot_reserve=50, *a, **k
            )

            def Lbl(text, x, y, *a, **k):
                self.add_label(
                    text, x=x, y=y,
                    font_size=9, color=(0, 0, 0, 255),
                    bold=True, anchor_x='left', anchor_y='bottom',
                    *a, **k
                )

            Lbl(u'用户名：', 368 - 350, 286 - 165)
            Lbl(u'密码：', 368 - 350, 250 - 165)

            self.txt_username = TextBox(
                parent=self, x=438-350, y=282-165, width=220, height=20,
                text=UserSettings.last_id,
            )
            self.txt_pwd = PasswordTextBox(
                parent=self, x=438-350, y=246-165, width=220, height=20,
                text=simple_decrypt(UserSettings.saved_passwd),
            )
            self.chk_savepwd = CheckBox(
                parent=self, x=438-350, y=56, caption=u'记住密码',
                value=bool(self.txt_pwd.text),
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
            self.parent.start_login()
            Executive.auth(u, pwd)

        def disable(self):
            self.btn_login.state = Button.DISABLED

        def enable(self):
            self.btn_login.state = Button.NORMAL

    def __init__(self, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)
        self.bg = L('c-bg_login')
        self.bg_alpha = LinearInterp(0, 1.0, 1.5)
        self.dialog = LoginScreen.LoginDialog(parent=self)
        self.btn_try = try_game = Button(
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
                self.start_login()
                val and Executive.auth('-1', 'guest')

    def on_message(self, _type, *args):
        if _type == 'auth_success':
            dlg = self.dialog
            UserSettings.last_id = dlg.txt_username.text
            UserSettings.saved_passwd = simple_encrypt(
                dlg.txt_pwd.text if dlg.chk_savepwd.value else ''
            )
            GameHallScreen().switch()

        elif _type == 'auth_failure':
            log.error('Auth failure')
            self.done_login()
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

    def start_login(self):
        self.loading = LoadingWindow(u'正在验证用户', parent=self)
        self.btn_try.state = Button.DISABLED
        self.dialog.disable()

    def done_login(self):
        self.loading.done()
        self.btn_try.state = Button.NORMAL
        self.dialog.enable()

    def on_switch(self):
        SoundManager.switch_bgm('c-bgm_hall')


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
                    parent=self, x=95, y=395, width=320, height=22,
                )
                uname = Executive.gamemgr.account.username

                self.chk_invite_only = CheckBox(
                    parent=self, x=423, y=397, caption=u'邀请制房间', value=False,
                )

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

                n_hidden = 0

                from options import options

                for i, (gname, gcls) in enumerate(modes.items()):
                    if not options.show_hidden_modes:
                        if getattr(gcls.ui_meta, 'hidden', False):
                            n_hidden += 1
                            continue

                    y, x = divmod(i - n_hidden, 3)
                    x, y = 30 + 170*x, 275 - 125*y
                    s = ImageSelector(
                        L(gcls.ui_meta.logo), selectors,
                        parent=self, x=x, y=y
                    )
                    intro = getattr(gcls.ui_meta, 'description', None)
                    intro and s.balloon.set_balloon(intro, width=480)
                    s.gametype = gname
                    s.event(on_select)
                    selectors.append(s)

                @btncreate.event
                def on_click():
                    gtype = ImageSelector.get_selected(selectors).gametype
                    f = pyglet.font.load('AncientPix', 9)
                    roomname = textsnap(txtbox.text, f, 200)
                    Executive.create_game(gtype, roomname, self.chk_invite_only.value)
                    self.delete()

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

                Executive.query_gameinfo(game_id)

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
                            Executive.observe_user(uid)
                            self.overlay.chat_box.append(u'|R已经向%s发送了旁观请求，请等待回应……|r\n' % un)
                            self.delete()

        def __init__(self, p):
            Frame.__init__(
                self, parent=p, caption=u'当前大厅内的游戏',
                x=35, y=220, width=700, height=420,
                bot_reserve=30, bg=L('c-bg_gamelist'),
            )

            gl = self.gamelist = ListView(parent=self, x=2, y=30, width=696, height=420-30-25)
            gl.set_columns([
                (u'No.',      100),
                (u'游戏名称', 200),
                (u'游戏类型', 200),
                (u'人数',     50),
                (u'当前状态', 80),
            ])

            self.btn_create     = Button(parent=self, caption=u'创建游戏', x=690-270, y=6, width=70, height=20)
            self.btn_quickstart = Button(parent=self, caption=u'快速加入', x=690-180, y=6, width=70, height=20)
            self.btn_refresh    = Button(parent=self, caption=u'刷新列表', x=690-90,  y=6, width=70, height=20)

            @self.btn_create.event
            def on_click():
                self.CreateGamePanel(parent=self.overlay)

            @self.btn_quickstart.event  # noqa
            def on_click():
                Executive.quick_start_game()

            @self.btn_refresh.event  # noqa
            def on_click():
                Executive.get_lobbyinfo()

            @self.gamelist.event
            def on_item_dblclick(li):
                if li.started:
                    self.ObserveGamePanel(li.game_id, parent=self.overlay)
                else:
                    Executive.join_game(li.game_id)

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
                        '%d/%d' % (gi['nplayers'], n_persons),
                        [u'等待中', u'游戏中'][gi['started']],
                    ], color=(0, 0, 0, 255) if gi['started'] else (0xef, 0x75, 0x45, 0xff))
                    li.game_id = gi['id']
                    li.started = gi['started']

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
                'hang':       u'|c0000ffff游戏大厅|r',
                'ingame':     u'|G游戏中|r',
                'inroomwait': u'|R在房间中|r',
                'ready':      u'|c9f5f9fff准备状态|r',
                'observing':  u'|LB观战中|r',
            }
            if _type == 'current_users':
                users = args[0]
                box = self.box
                box.text = u'\u200b'
                self.caption = u'当前在线玩家：%d' % len(users)
                self.update()
                rst = []
                for u in users:
                    acc = Account.parse(u['account'])
                    username = acc.username.replace('|', '||')
                    rst.append(u'%s([|c9100ffff%s|r], %s)' % (
                        username.replace('|', '||'),
                        acc.userid,
                        lookup.get(u['state'], u['state']),
                    ))

                box.append('\n'.join(rst))

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

            @gevent.spawn
            def update():
                from settings import HALL_NOTICE_URL
                resp = requests.get(HALL_NOTICE_URL)
                if resp.ok:
                    ta.text = resp.content.decode('utf-8')
                else:
                    ta.text = u'|R无法显示新闻！|r'

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
        self.bg = L('c-bg_gamehall')

        self.gamelist = self.GameList(self)

        chat = self.chat_box = ChatBox(parent=self, x=35+255, y=20, width=700-255, height=180)
        chat.text = u'您现在处于游戏大厅！\n'
        self.playerlist = GameHallScreen.OnlineUsers(parent=self)
        self.noticebox = GameHallScreen.NoticeBox(parent=self)
        self.statusbox = GameHallScreen.StatusBox(parent=self)

        VolumeTuner(parent=self, x=850, y=650)
        NoInviteButton(parent=self, x=654, y=650, width=80, height=35)

        b = Button(
            parent=self, x=564, y=650, width=80, height=35,
            color=Colors.orange, caption=u'加入QQ群',
        )

        @b.event
        def on_click():
            openurl('http://shang.qq.com/wpa/qunwpa?idkey=e25b8a940bf6e5409c48d7dac3681257c47b341c97b0d1d9c3b278d650aa8b0b')

        b = Button(
            parent=self, x=750, y=650, width=80, height=35,
            color=Colors.orange, caption=u'卡牌查看器',
        )
        del on_click

        @b.event
        def on_click():
            openurl('http://thb.io')

        del on_click

        b = Button(
            parent=self, x=35, y=650, width=80, height=35,
            color=Colors.orange, caption=u'切换服务器',
        )

        @b.event
        def on_click():
            Executive.disconnect()
            ServerSelectScreen().switch()

        Executive.get_lobbyinfo()

    def on_message(self, _type, *args):
        rst = handle_chat(_type, args)
        if rst:
            self.chat_box.append(rst)
            return

        elif _type == 'game_joined':
            GameScreen(args[0]).switch()

        elif _type == 'lobby_error':
            log.error('Lobby error: %s' % args[0])  # TODO
            mapping = {
                'cant_join_game': u'无法加入游戏',
                'no_such_user': u'没有这个玩家',
                'maoyu_limitation': u'您现在是毛玉（试玩玩家），不能这样做。\n毛玉只能玩练习模式和KOF模式。',
                'not_invited': u'这是个邀请制房间，只能通过邀请进入。',
                'banned': u'你已经被强制请离，不能重复进入',
            }
            ConfirmBox(mapping.get(args[0], args[0]), parent=self)

        elif _type == 'observe_refused':
            uname = args[0]
            self.chat_box.append(u'|R%s 回绝了你的旁观请求|r\n' % uname)

        else:
            Screen.on_message(self, _type, *args)

    def draw(self):
        # glColor3f(.9, .9, .9)
        glColor3f(1, 1, 1)
        self.bg.blit(0, 0)
        self.draw_subcontrols()

    def on_switch(self):
        SoundManager.switch_bgm('c-bgm_hall')


class GameEventsBox(Frame):
    def __init__(self, parent, width, height, **k):
        Frame.__init__(self, parent=parent, caption=u'游戏信息', bot_reserve=0, width=width, height=height, **k)
        self.box = TextArea(
            parent=self, x=2, y=2,
            width=width - 4, height=height - 24 - 2,
        )

    def append(self, v):
        self.box.append(v)

    def clear(self):
        self.box.text = u'\u200b'


class UIEventHook(EventHandler):
    def __init__(self, gameui):
        EventHandler.__init__(self)
        self.gameui = gameui
        self.live = False

    def evt_user_input(self, evt, arg):
        trans, ilet = arg
        evt = Event()
        ilet.event = evt
        self.gameui.process_game_event('user_input', arg)
        evt.wait()
        return ilet

    def handle(self, evt, data):
        if not self.live and evt not in ('game_begin', 'switch_character', 'reseat'):
            return data

        return getattr(self, 'evt_' + evt, self.gameui.process_game_event)(evt, data)

    def set_live(self):
        self.live = True


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

            Executive.get_lobbyinfo()

        def draw(self):
            Panel.draw(self)
            self.labels.draw()

        def on_message(self, _type, *args):
            if _type == 'current_users':
                ul = args[0]
                ul = [Account.parse(u['account']) for u in ul if u['state'] in ('hang', 'observing')]

                for i, u in enumerate(ul):
                    y, x = divmod(i, 5)
                    x, y = 30 + 100 * x, 250 - 35 * y
                    s = Button(
                        u.username,
                        color=Colors.orange,
                        parent=self, x=x, y=y,
                        width=95, height=30,
                    )

                    @s.event
                    def on_click(s=s, uid=u.userid, un=u.username):
                        Executive.invite_user(uid)
                        self.overlay.chat_box.append(u'|R已经邀请了%s，请等待回应……|r\n' % un)
                        s.state = Button.DISABLED

    class RoomControlPanel(Control):
        class GameParamsPanel(Control):
            def __init__(self, params_disp, parent=None):
                Control.__init__(self, parent=parent, **r2d((5, 34, 350, 120)))
                self.labels = lbls = BatchList()
                self.param_btns = btns = {}

                for i, (k, d) in enumerate(params_disp.items()):
                    lbls.append(Label(
                        d['desc'], x=0, y=(2 - i) * 30 + 5, font_size=9,
                        color=Colors.get4i(Colors.blue.caption),
                        shadow=(2, 255, 255, 255, 255)
                    ))

                    og = OptionButtonGroup(
                        parent=self, x=98, y=(2 - i) * 30, buttons=d['options'],
                    )

                    @og.event
                    def on_option(v, k=k):
                        Executive.set_game_param(k, v)
                        return True

                    btns[k] = og

            def draw(self):
                glColor3f(1, 1, 1)
                Control.draw(self)
                self.labels.draw()

            def on_message(self, _type, *args):
                if _type == 'game_params':
                    for k, v in args[0].items():
                        self.param_btns[k].set_value(v)

        def __init__(self, parent=None):
            Control.__init__(self, parent=parent, **r2d((0, 0, 820, 700)))
            self.btn_getready = Button(
                parent=self, caption=u'准备', **r2d((360, 80, 100, 35))
            )

            self.btn_invite = Button(
                parent=self, caption=u'邀请', **r2d((360, 40, 100, 35))
            )

            self.game_params_panel = self.GameParamsPanel(self.parent.game.ui_meta.params_disp, parent=self)

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
                self.btn_getready.state = Button.DISABLED
                if self.ready:
                    Executive.cancel_ready()
                else:
                    Executive.get_ready()

            @self.btn_invite.event  # noqa
            def on_click():
                GameScreen.InvitePanel(self.parent.game.gameid, parent=self)

        def draw(self):
            self.draw_subcontrols()

        def update_ready_btn(self):
            if self.ready:
                self.ready = True
                self.btn_getready.caption = u'取消准备'
            else:
                self.ready = False
                self.btn_getready.caption = u'准备'

            self.btn_getready.state = Button.NORMAL
            self.btn_getready.update()

        def on_message(self, _type, *args):
            if _type == 'player_change':
                self.update_portrait(args[0])
            elif _type == 'kick_request':
                u1, u2, count = args[0]
                u1 = Account.parse(u1['account'])
                u2 = Account.parse(u2['account'])
                self.parent.chat_box.append(
                    u'|B|R>> |c0000ffff%s|r希望|c0000ffff|B%s|r离开游戏，已有%d人请求\n' % (
                        u1.username, u2.username, count
                    )
                )
            elif _type == 'game_joined':
                self.ready = False
                self.update_ready_btn()

                for p in self.portraits:
                    p.account = None

            elif _type == 'set_game_param':
                u, k, v = args[0]
                u = Account.parse(u['account'])
                disp = self.parent.game.ui_meta.params_disp[k]
                lookup = {v: s for s, v in disp['options']}
                self.parent.chat_box.append(
                    u'|B|R>> |c0000ffff%s|r已经将|c0000ffff%s|r设定为|c0000ffff%s|r，请重新准备。\n' % (
                        u.username, disp['desc'], lookup[v],
                    )
                )

        def update_portrait(self, pl):
            def players():
                return {
                    p.account.username
                    for p in self.portraits
                    if p.account
                }

            orig_players = players()
            full = True
            my_uid = Executive.gamemgr.account.userid

            for i, p in enumerate(pl):
                accdata = p['account']
                acc = Account.parse(accdata) if accdata else None
                if not accdata: full = False

                if acc and acc.userid == my_uid:
                    self.ready = p['state'] == 'ready'
                    self.update_ready_btn()

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

    def __init__(self, game, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)

        self.backdrop = L('c-bg_ingame')
        self.flash_alpha = 0.0

        self.game = game
        self.ui_class = game.ui_meta.ui_class()
        self.gameui = self.ui_class(
            parent=False, game=game,
            **r2d((0, 0, 820, 700))
        )  # add when game starts
        game.event_observer = UIEventHook(self.gameui)

        self.events_box = GameEventsBox(
            parent=self, x=820, y=340, width=204, height=360,
            bg=L('c-bg_eventsbox'),
        )
        self.chat_box = ChatBox(
            parent=self, x=820, y=0, width=204, height=342,
            bg=L('c-bg_chatbox'),
        )
        self.panel = GameScreen.RoomControlPanel(parent=self)
        self.btn_exit = Button(
            parent=self, caption=u'退出房间', zindex=1,
            **r2d((730, 660, 75, 25))
        )
        self.btn_no_invite = NoInviteButton(
            parent=self, zindex=1, **r2d((730, 630, 75, 25))
        )

        VolumeTuner(parent=self, x=690, y=660)

        @self.btn_exit.event
        def on_click():
            box = ConfirmBox(u'真的要离开吗？', buttons=ConfirmBox.Presets.OKCancel, parent=self)

            @box.event
            def on_confirm(val):
                val and Executive.exit_game()

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
            g = self.game
            g.event_observer = UIEventHook(self.gameui)

            @gevent.spawn
            def start():
                gevent.sleep(0.3)
                svr = g.me.server
                if svr.gamedata_piled():
                    g.start()
                    svr.wait_till_live()
                    gevent.sleep(0.1)
                    svr.wait_till_live()
                    self.gameui.set_live()
                    g.event_observer.set_live()
                else:
                    self.gameui.set_live()
                    g.event_observer.set_live()
                    g.start()

        elif _type == 'ob_kick_request':
            u1, u2, count = args[0]
            u1 = Account.parse(u1['account'])
            u2 = Account.parse(u2['account'])
            self.chat_box.append(
                u'|B|R>> |c0000ffff%s|r希望|c0000ffff|B%s|r[|c9100ffff%d|r]离开游戏，已有%d人请求\n' % (
                    u1.username, u2.username, u2.userid, count
                )
            )

        elif _type == 'end_game':
            self.remove_control(self.gameui)
            self.add_control(self.panel)
            g = args[0]

            box = ConfirmBox(u'要保存这场游戏的Replay吗？', buttons=ConfirmBox.Presets.OKCancel, parent=self)

            @box.event
            def on_confirm(v):
                if not v:
                    return

                @gevent.spawn
                def save():
                    filename = get_save_file_name(None, u'保存Replay', [(u'THB Replay 文件', u'*.thbrep')])
                    if not filename.endswith('.thbrep'):
                        filename += '.thbrep'

                    Executive.save_replay(filename)

        elif _type == 'client_game_finished':
            g = args[0]
            g.ui_meta.ui_class().show_result(g)

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
            SoundManager.switch_bgm('c-bgm_hall')
            self.backdrop = L('c-bg_ingame')
            self.set_color(Colors.green)
            self.events_box.clear()

        elif _type == 'game_crashed':
            ConfirmBox(
                u'游戏逻辑已经崩溃，请退出房间！\n'
                u'这是不正常的状态，你可以报告bug。\n'
                u'游戏ID：%d' % self.game.gameid,
                parent=self
            )
            from crashreport import do_crashreport
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
                Executive.observe_grant(uid, val)

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
        SoundManager.switch_bgm('c-bgm_hall')


class ReplayScreen(Screen):
    flash_alpha = InterpDesc('_flash_alpha')

    class ReplayPanel(Frame):
        def __init__(self, **k):
            Frame.__init__(self, caption=u'Replay控制', **k)

            self.btn_start = Button(u'开始', parent=self, color=Colors.orange, x=15, y=65, width=80, height=24)
            self.btn_pause = Button(u'暂停', parent=self, color=Colors.blue, x=15 + 80 + 15, y=65, width=80, height=24)
            self.btn_brake = Button(u'减速', parent=self, x=15, y=25, width=80, height=24)
            self.btn_accel = Button(u'加速', parent=self, x=15 + 80 + 15, y=25, width=80, height=24)

            self.delay = 2.0
            self.paused = False
            self.running = Event()
            self.running.set()

            self.delay_lbl = self.add_label(
                u'当前延迟：%s秒' % self.delay,
                x=15, y=105, font_size=9, color=(0, 0, 0, 255),
                anchor_x='left', anchor_y='bottom',
            )

            self.btn_start.event('on_click')(self.start)
            self.btn_pause.event('on_click')(self.pause)
            self.btn_brake.event('on_click')(self.brake)
            self.btn_accel.event('on_click')(self.accel)

        def start(self):
            self.parent.start_replay()
            self.btn_start.state = Button.DISABLED

        def pause(self):
            if self.paused:
                self.running.set()
                self.btn_pause.caption = u'暂停'
                self.paused = False
            else:
                self.running.clear()
                self.btn_pause.caption = u'恢复'
                self.paused = True

            self.btn_pause.update()

        def brake(self):
            self.delay += 0.1
            self.delay_lbl.text = u'当前延迟：%s秒' % self.delay

        def accel(self):
            self.delay = max(self.delay - 0.1, 0.2)
            self.delay_lbl.text = u'当前延迟：%s秒' % self.delay

        def handle_delay(self, evt, _):
            gevent.sleep(self.delay)
            self.running.wait()

    class Portraits(Control):

        def __init__(self, parent=None):
            Control.__init__(self, parent=parent, **r2d((0, 0, 820, 700)))
            l = []

            class MyPP(PlayerPortrait):
                # this class is INTENTIONALLY put here
                # to make cached avatars get gc'd
                cached_avatar = {}

            for x, y, color in parent.ui_class.portrait_location:
                l.append(MyPP('NONAME', parent=self, x=x, y=y, color=color))

            self.portraits = l

        def draw(self):
            self.draw_subcontrols()

        def update_portrait(self, pl):
            for i, p in enumerate(pl):
                accdata = p['account']
                acc = Account.parse(accdata) if accdata else None
                port = self.portraits[i]
                port.account = acc
                port.ready = True
                port.update()

    def __init__(self, game, replay, *args, **kwargs):
        Screen.__init__(self, *args, **kwargs)

        self.backdrop = L('c-bg_ingame')
        self.flash_alpha = 0.0

        self.game = game
        self.ui_class = game.ui_meta.ui_class()
        self.gameui = self.ui_class(
            parent=False, game=game,
            **r2d((0, 0, 820, 700))
        )  # add when game starts

        Button(
            parent=self, caption=u'结束Replay', zindex=1,
            **r2d((730, 660, 75, 25))
        ).event('on_click')(self.end_replay)

        self.events_box = GameEventsBox(
            parent=self, x=820, y=150, width=204, height=550,
            bg=L('c-bg_eventsbox'),
        )
        self.replay_panel = ReplayScreen.ReplayPanel(
            parent=self, x=820, y=0, width=204, height=152,
        )

        self.portraits = ReplayScreen.Portraits(parent=self)
        self.portraits.update_portrait(replay.users[len(game.npc_players):])

        VolumeTuner(parent=self, x=690, y=660)

    def start_replay(self):
        self.portraits.delete()
        self.add_control(self.gameui)
        self.gameui.init()
        g = self.game
        g.event_observer = UIEventHook(self.gameui)
        g.event_observer.evt_user_input_begin_wait_resp = self.replay_panel.handle_delay
        g.event_observer.set_live()
        g.start()

    def end_replay(self):
        Executive.end_replay()
        ServerSelectScreen().switch()

    def on_message(self, _type, *args):
        if _type in ('client_game_finished', 'end_game'):
            g = args[0]
            ServerSelectScreen().switch()
            if _type == 'client_game_finished':
                g.ui_meta.ui_class().show_result(g)
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
        self.replay_panel.set_color(color)

    def on_switch(self):
        SoundManager.switch_bgm('c-bgm_hall')
