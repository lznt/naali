import math
import random
import json
import socket #just for exception handling for restarts here
import time

import ws4py.server.geventserver
from ws4py.websocket import WebSocket


from PythonQt.QtGui import QVector3D as Vec3
from PythonQt.QtGui import QQuaternion as Quat

import haversine
import tundra
import move

clients = set()
connections = dict()


scene = None

def log(s):
    print "WebsocketServer:", s

def newclient(connectionid):
    if scene is not None:
        tundra.Server().UserConnected(connectionid, 0, 0)
        avent = scene.GetEntityByNameRaw("Avatar" + str(connectionid))
        return avent.id

    else:
        tundra.LogWarning("Websocket server got a client connection, but has no scene - what to do?")

def removeclient(connectionid):
    tundra.Server().UserDisconnected(connectionid, 0)

def on_sceneadded(name):
    '''Connects to various signal when scene is added'''
    global scene
    sceneapi = tundra.Scene()
    scene = sceneapi.GetScene(name).get() #*Raw
    print "Using scene:", scene.name, scene

    assert scene.connect("AttributeChanged(IComponent*, IAttribute*, AttributeChange::Type)", onAttributeChanged)
    assert scene.connect("EntityCreated(Entity*, AttributeChange::Type)", onNewEntity)

    assert scene.connect("ComponentAdded(Entity*, IComponent*, AttributeChange::Type)", onComponentAdded)

    assert scene.connect("EntityRemoved(Entity*, AttributeChange::Type)", onEntityRemoved)

    
def update(t):
	
	
	if server is not None:
		#server.next()
		server._stopped_event.wait(timeout=2.0001)
		#print '.',
		#def on_exit(self):
		# Need to figure something out what to do and how
		if GraffitiWebSocket.walk == True:
			moveUpdate(t)

			
def sendAll(data):
	for client in clients:
		try:
			client.send(json.dumps(data))
		except socket.error:
			pass #client has been disconnected, will be noted later & disconnected by another part

def onAttributeChanged(component, attribute, changeType):
    #FIXME Only syncs hard coded ec_placeable
    #Maybe get attribute or something
    
    #FIXME Find a better way to get component name
    component_name = str(component).split()[0]

    #Let's only sync EC_Placeable
    if component_name != "EC_Placeable":
        return

    entity = component.ParentEntity()
    
    # Don't sync local stuff
    if entity.IsLocal():
        return

    ent_id = entity.id

    data = component.GetAttributeQVariant('Transform')
    transform = list()

    transform.extend([data.position().x(), data.position().y(), data.position().z()])
    transform.extend([data.rotation().x(), data.rotation().y(), data.rotation().z()])
    transform.extend([data.scale().x(), data.scale().y(), data.scale().z()])

    sendAll(['setAttr', {'id': ent_id, 
                         'component': component_name,
                         'Transform': transform}])

def onNewEntity(entity, changeType):
    sendAll(['addEntity', {'id': entity.id}])
    print entity

def onComponentAdded(entity, component, changeType):
    #FIXME Find a better way to get component name
    component_name = str(component).split()[0]

    # Just sync EC_Placeable and EC_Mesh since they are currently the
    # only ones that are used in the client
    if component_name not in ["EC_Placeable", "EC_Mesh"]:
        return

    if component_name == "EC_Mesh":
        sendAll(['addComponent', {'id': entity.id, 'component': component_name, 'url': 'ankka.dae'}])

    else: #must be pleaceable
        data = component.transform
        transform = list()

        transform.extend([data.position().x(), data.position().y(), data.position().z()])
        transform.extend([data.rotation().x(), data.rotation().y(), data.rotation().z()])
        transform.extend([data.scale().x(), data.scale().y(), data.scale().z()])

        sendAll(['addComponent', {'id': entity.id, 
                             'component': component_name,
                             'Transform': transform}])

    print entity.id, component

def onEntityRemoved(entity, changeType):
    print "Removing", entity
    sendAll(['removeEntity', {'id': entity.id}])

def moveUpdate(t):
	if GraffitiWebSocket.relativeLat > 0:
		speed = 1.6
		time = t
		lats = speed * time * GraffitiWebSocket.ratioLat
		lons = speed * time * GraffitiWebSocket.ratioLon
		avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName("Bot").get()# + str(msg['data']['user'])).get()

		yy = avatarEntity.placeable.Position().y()
		xx = avatarEntity.placeable.Position().x()
		zz = avatarEntity.placeable.Position().z()
		
		if GraffitiWebSocket.orientation == "ne":
			summedPositionz = zz + lats
			summedPositionx = xx + lons
		elif GraffitiWebSocket.orientation == "sw":
			summedPositionz = zz - lats
			summedPositionx = xx - lons
		elif GraffitiWebSocket.orientation == "nw":
			summedPositionz = zz + lats
			summedPositionx = xx - lons
		elif GraffitiWebSocket.orientation =="se":
			summedPositionz = zz - lats
			summedPositionx = xx + lons
		
		GraffitiWebSocket.totalLat = GraffitiWebSocket.totalLat + lats
		GraffitiWebSocket.totalLon = GraffitiWebSocket.totalLon + lons	
		
		
		print GraffitiWebSocket.totalLat, GraffitiWebSocket.totalLon, GraffitiWebSocket.relativeLat, GraffitiWebSocket.relativeLon
		#avatarEntity.animationcontroller.SetAnimationSpeed(GraffitiWebSocket.walkAnimName, 0.60)
		#avatarEntity.animationcontroller.EnableAnimation(GraffitiWebSocket.walkAnimName , True, 0.25, True)
		avatarEntity.placeable.SetPosition(summedPositionx,yy,summedPositionz)

		#Muista kokeilla and ehdolla
		#
		if GraffitiWebSocket.totalLat > GraffitiWebSocket.relativeLat or GraffitiWebSocket.totalLon > GraffitiWebSocket.relativeLon:
			GraffitiWebSocket.walk = False
			GraffitiWebSocket.totalLon = 0 
			GraffitiWebSocket.totalLat = 0
			avatarEntity.animationcontroller.DisableAllAnimations()
			print 'Reached end of moveUpdate()'
		
			
class GraffitiWebSocket(WebSocket):
	
	walk = False
	avatarEntity = None
	relativeLat = 0
	relativeLon = 0
	totalLat = 0
	totalLon = 0
	walkAnimName = u'Walk'
	animList = [walkAnimName]
	latitudeInMeters = 0
	longitudeInMeters = 0
	ratioLat = 0
	ratioLon = 0
	orientation = ""
	
	def opened(self):
		print "Websocket client connected"
		self.send('Websocket client connected')

	def received_message(self, message):
		"""
		Automatically sends back the provided ``message`` to
		its originating endpoint.
		"""

		lat1 = 65.012124
		lon1 = 
		#lat1 = 65.058325
		#lon1 = 25.468476
		
		def add():
			#ask about the usage of addMobileUser thru websocket echo test
			#Animation is still broken, testing testing..
			
			print "Player Added"
			avatarEntity =  tundra.Scene().MainCameraScene().CreateEntity(scene.NextFreeId(), ["EC_Placeable", "EC_AnimationController", "EC_Mesh", "EC_RigidBody", "EC_Avatar", "EC_Script"]).get()
			avatarEntity.SetTemporary(True)
			avatarEntity.placeable.visible = True
			avatarEntity.SetName("Bot") #+ str(msg['data']['user']))
			avatarEntity.rigidbody.mass = 0
			#avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName('Avatar1').get()
			#Script = avatarEntity.GetOrCreateComponent("EC_Script")
			avatarEntity.placeable.SetPosition(0, -4, 0)	
			avatarEntity.avatar.appearanceRef.setRef("default_avatar.avatar")
			#avatarEntity.appearance.appearanceRef = avatarurl
			
			#avatarEntity.script.className = "move.py"
			
			#Approx 0 on oulu3d
			#long = 25.473395
			#lat = 65.012124
			#2nd 65.012305,25.472703
			#3rd 65.012523,25.471931
			#4th 65.012976,25.471941
			
		def move():
			
			#GraffitiWebSocket.avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName("Bot").get() # + str(msg['data']['user'])).get()
			avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName("Bot").get()	
			#length = len(msg['data']['localizations'])
			#print length
			#lat =  msg['data']['localizations'][length-1]['lat']
			#lon =  msg['data']['localizations'][length-1]['lon']
			lat = msg['data']['lat']
			lon = msg['data']['lon']
			lat2 = lat
			lon2 = lon
				
			GraffitiWebSocket.latitudeInMeters = haversine.calcLat(lat1, lat2)
			GraffitiWebSocket.longitudeInMeters = haversine.calcLong(lon1, lon2, lat1, lat2)
			distanceInMeters = haversine.distance(lat1, lat2, lon1, lon2)
			
			print 'Distance in meters' , distanceInMeters
			
			#print longitudeInMeters, latitudeInMeters
			#
			#if GraffitiWebSocket.latitudeInMeters < distanceInMeters:
			#	relativeAngle = math.acos(GraffitiWebSocket.latitudeInMeters/distanceInMeters)
			#else:
			#	relativeAngle = math.acos(distanceInMeters/GraffitiWebSocket.latitudeInMeters)
			
			#relativeAngle is the angle that is made from the distance vector and the vector made by z. This way we could move
			#the right angle, if the SetRotation commands would work, which they do not. Tested via python console.
			#rotationAngle = avatarEntity.placeable.transform.SetRot(0,relativeAngle,0)
			lonOrientation = GraffitiWebSocket.longitudeInMeters - avatarEntity.placeable.Position().z()
			latOrientation = GraffitiWebSocket.latitudeInMeters - avatarEntity.placeable.Position().x()
			
			GraffitiWebSocket.relativeLon = math.fabs(lonOrientation)
			GraffitiWebSocket.relativeLat = math.fabs(latOrientation)
			
		
			
			if lonOrientation >= 0 and latOrientation >= 0:
				GraffitiWebSocket.orientation = "ne"
			elif  lonOrientation < 0 and latOrientation < 0:
				GraffitiWebSocket.orientation = "sw"
			elif lonOrientation < 0 and latOrientation >= 0:
				GraffitiWebSocket.orientation = "nw"
			elif  lonOrientation >= 0 and latOrientation < 0:
				GraffitiWebSocket.orientation = "se"
			
			print GraffitiWebSocket.orientation
			
			GraffitiWebSocket.walk = True
			walking = True

			#ac.animationState = GraffitiWebSocket.walkAnimName
			#animName = avatarEntity.animationcontroller.animationState
			#print avatarEntity.animationcontroller.IsAnimationActive(animName)
		
		
			if GraffitiWebSocket.relativeLat >= GraffitiWebSocket.relativeLon:
				GraffitiWebSocket.ratioLon = GraffitiWebSocket.relativeLon / GraffitiWebSocket.relativeLat
				GraffitiWebSocket.ratioLat = 1
				
			else: #GraffitiWebSocket.relativeLon > GraffitiWebSocket.relativeLat:
				GraffitiWebSocket.ratioLat = GraffitiWebSocket.relativeLat / GraffitiWebSocket.relativeLon
				GraffitiWebSocket.ratioLon = 1
			print GraffitiWebSocket.ratioLat , GraffitiWebSocket.ratioLon
				
			#print 'New longitude is %r' % relativeLon
			#print 'New latitude is %r' % relativeLat
			
		#print "Websocket message received:"
		
		#print message.data.decode("utf-8")
			
		msg = json.loads(message.data.decode("utf-8"))    
		self.send(message.data, message.is_binary)
	

			
			
		actions = { "addMobileUser" : add, "movedUser" : move}

		actions[msg['action']]()      

			

if tundra.Server().IsAboutToStart():
	server = ws4py.server.geventserver.WebSocketServer(('0.0.0.0', 9999), websocket_class=GraffitiWebSocket)
	server.start()
	print "websocket server started."
	

	assert tundra.Frame().connect("Updated(float)", update)
	sceneapi = tundra.Scene()
	
	print "Websocket Server connecting to OnSceneAdded:", sceneapi.connect("SceneAdded(QString)", on_sceneadded)
	#on_sceneadded("TundraServer")
