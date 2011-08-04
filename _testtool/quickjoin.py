from socket import *
import simplejson as json
import sys

so = socket()
so.connect(('127.0.0.1', 9999))
so.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
f = so.makefile()

def write(p):
    '''
    Send json encoded packet
    '''
    d = encode(p)
    sys.stdout.write(">> %s" % d)
    so.send(d)


def close():
    so.shutdown(SHUT_RDWR)

def encode(p):
    def default(o):
        return o.__data__() if hasattr(o, '__data__') else repr(o)
    return json.dumps(p, default=default) + "\n"

def read():
    try:
        s = f.readline(1000)
        sys.stdout.write("<< " + s)
        if s == '':
            so.close()
            return
        d = json.loads(s)
        return d
    except IOError as e:
        so.close()
        return

write(['auth',['feisuzhu', 'Proton']])
read()
write(['quick_start_game', None])
read()
read()
write(['get_ready', None])
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()
read()

