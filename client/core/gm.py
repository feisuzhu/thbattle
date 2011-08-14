from utils import AsyncService, PlayerList
from server_endpoint import Server
import sys
import gevent
from gevent import socket

class DataHolder(object): pass

class GameManager(AsyncService):

    def __init__(self):
        AsyncService.__init__(self)
        self.state = 'initial'

    def service_auth(self, user, pwd):
        assert self.state == 'connected', 'connect first!'
        self.server.write(['auth', [user, pwd]])
        rst, data = self.server.ctlexpect(['greeting', 'auth_err'])
        if rst == 'greeting':
            self.server_id = data
            self.state = 'hang'
            return True
        else:
            return False

    def service_heartbeat(self):
        assert self.state != 'initial', 'connect first!'
        while True:
            gevent.sleep(30)
            self.server.write(['heartbeat', None])

    def service_failure_handler(self):
        self.server.ctlexpect(['timeout'])
        print 'Timed out. Exit.'
        sys.exit()

    def service_connect(self, addr):
        assert self.state == 'initial', 'what else can it be??'
        s = socket.socket()
        s.connect(addr)
        svr = Server.spawn(s, 'SERVER')
        self.server = svr
        self.state = 'connected'
        return svr

    def service_inroom_handler(self):
        from client.core import PeerPlayer
        from gamepack import gamemodes
        while True:
            cmd, data = self.server.ctlexpect(['player_change', 'game_started', 'game_joined', 'fleed', 'game_left', 'end_game'])
            if cmd == 'player_change':
                assert self.state in ('inroom', 'ingame')
                if self.state == 'inroom':
                    players = data
                else:
                    for i, p in enumerate(data):
                        if p.get('dropped'):
                            game.players[i].dropped = True

            elif cmd == 'game_started':
                assert self.state == 'inroom'
                self.state = 'ingame'
                pid = [i['id'] for i in players]
                pl = [PeerPlayer(i) for i in players]
                pl[pid.index(self.server_id)] = self.server
                game.me = self.server
                game.players = PlayerList(pl)
                self.server.gamedata = DataHolder()
                game.start()

            elif cmd == 'game_joined':
                assert self.state == 'hang'
                self.state = 'inroom'
                game = gamemodes[data['type']]()

            elif cmd == 'fleed':
                assert self.state == 'ingame'
                self.state = 'hang'
                game.kill()
                game = None

            elif cmd == 'game_left':
                assert self.state == 'inroom'
                self.state = 'hang'
                game = None
            
            elif cmd == 'end_game':
                assert self.state == 'ingame'
                self.state = 'hang'
                game = None
                

