import tundra
from urlparse import urlsplit
import copy

import gevent
from gevent import Greenlet
from gevent import socket
from gevent.coros import Semaphore
from gevent.queue import Queue

import ws4py.client.geventclient
from ws4py.exc import HandshakeError, StreamClosed

def handle_clients(ws):
    def incoming():
        while True:
            m = ws.receive()
            if m is not None:
                print m, len(str(m))
                #if len(str(m)) == 35:
                    #ws.close()
                    #break
            else:
                break
        print "Connection closed!"
    
    def outgoing():
        for i in range(0, 40, 5):
            ws.send("*" * i)
        
        # We won't get this back
        ws.send("Foobar")
    print "handling client"
    greenlets = [
        gevent.spawn(incoming),
        gevent.spawn(outgoing),
    ]
    #gevent.joinall(greenlets)


    
def update(t):
    if client is not None:
        #server.next()
        #client._stopped_event.wait(timeout=0.001)
        print '.'
        wait


if tundra.Server().IsAboutToStart():
    client = ws4py.client.geventclient.WebSocketClient('http://echo.websocket.org/')
    client.connect()
    print "websocket client connected."
    handle_clients(client)
    tundra.Frame().connect("Updated(float)", update)
    sceneapi = tundra.Scene()


