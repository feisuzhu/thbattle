import gevent
from gevent.server import StreamServer
from server.core import User, Receptionist, GameHall

Receptionist.spawn()
GameHall.spawn()

def new_client(sock, addr):
    u = User(sock, addr)
    # TODO: Notifies [Receptionist] that a new user is coming
    Receptionist.instance.recept(u)
    u._greenlet_waitdata()

server = StreamServer(('0.0.0.0', 9999), new_client)
server.serve_forever()

