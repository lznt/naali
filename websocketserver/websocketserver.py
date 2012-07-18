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
import AssignMatrix
#import move

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
		server._stopped_event.wait(timeout=0.0001)
		#print '.',
		#def on_exit(self):
		# Need to figure something out what to do and how
		#if walk == True:
			#moveUpdate(t)

			
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


class GraffitiWebSocket(WebSocket):

	walk = False
	avatarEntity = None
	relativeLat = 0
	relativeLon = 0
	totalLat = 0
	totalLon = 0
	latitudeInMeters = 0
	longitudeInMeters = 0
	distanceInMeters = 0
	ratioLat = 0
	ratioLon = 0
	angle = 0
	PoliceId = 1
	
	def opened(self):
		print "Websocket client connected"
		self.send('Websocket client connected')

	def received_message(self, message):
		"""
		Automatically sends back the provided ``message`` to
		its originating endpoint.
		"""

		lat1 = 65.012124
		lon1 = 25.473395
		#lat1 = 65.058325
		#lon1 = 25.468476
		
		def add():
			#In final version visible after the first move.
			print "Player Added"
			avatarEntity =  tundra.Scene().MainCameraScene().CreateEntity(scene.NextFreeId(), ["EC_Placeable","EC_DynamicComponent", "EC_AnimationController", "EC_Mesh", "EC_RigidBody", "EC_Avatar", "EC_Script"]).get()
			avatarEntity.SetTemporary(True)
			avatarEntity.placeable.visible = True
			avatarEntity.SetName("Bot" + str(msg['data']['user']))
			avatarEntity.rigidbody.mass = 0
			avatarEntity.placeable.SetPosition(0, -4, 0)
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'ratios')
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'toMoves')
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'angleOfOrientation')
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'ifToWalk')
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'busted')
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'totals')
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'reset')
			#avatarEntity.avatar.appearanceRef.setRef("default_avatar.avatar")
			avatarEntity.script.className = "BotScriptApp.BotScript"
			#C2.className = "BotAndPoliceApp.BotAndPolice"
			
			#Approx 0 on oulu3d
			#long = 25.473395
			#lat = 65.012124
			
		def addPolice():
			#Some sort of counter to determine how many polices are added (if not static)
			policeEntity = tundra.Scene().MainCameraScene().CreateEntity(scene.NextFreeId(),["EC_Placeable", "EC_DynamicComponent", "EC_AnimationController", "EC_Mesh", "EC_RigidBody", "EC_Avatar", "EC_Script"]).get()
			policeEntity.SetTemporary(True)
			policeEntity.placeable.visible = False
			policeEntity.SetName("Bot_Police")
			#GraffitiWebSocket.PoliceId + 1
			policeEntity.rigidbody.mass = 0
			#policeEntity.placeable.SetPosition(0, -4, 0)
			policeEntity.script.className = "PoliceScriptApp.PoliceScript"

			
		def move():
			
			avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName("Bot" + str(msg['data']['_id'])).get()
			length = len(msg['data']['localizations'])
			lat =  msg['data']['localizations'][length-1]['lat']
			lon =  msg['data']['localizations'][length-1]['lon']
			#print lat, lon
			#print lat1, lon1
			#lat = msg['data']['lat']
			#lon = msg['data']['lon']
			lat2 = lat
			lon2 = lon
			speed = 1.6
			##Call haversine to calculate lat, lon and distance##
			latitudeInMeters = haversine.calcLat(lat1, lat2)
			longitudeInMeters = haversine.calcLong(lon1, lon2, lat1, lat2)
			GraffitiWebSocket.distanceInMeters = haversine.distance(lat1, lat2, lon1, lon2)
			
			dlon = lon2 - lon1
			dlat = lat2 - lat1
			
			if dlon < 0: 
				longitudeInMeters = -longitudeInMeters
			if dlat > 0:
				latitudeInMeters = -latitudeInMeters

			relativeLon = longitudeInMeters - avatarEntity.placeable.Position().x()
			relativeLat = latitudeInMeters - avatarEntity.placeable.Position().z()
		
			
			if math.fabs(relativeLat) >= math.fabs(relativeLon):
				ratioLon = math.fabs(relativeLon / relativeLat)
				ratioLat = 1
		
			else: #relativeLon > relativeLat:
				ratioLat = math.fabs(relativeLat / relativeLon)
				ratioLon = 1
				
			##Send relatives and angle to dynamiccomponent
			toMoves = avatarEntity.dynamiccomponent.GetAttribute('toMoves')
			toMoves.setx(relativeLon)
			toMoves.sety(relativeLat)
			avatarEntity.dynamiccomponent.SetAttribute('toMoves', toMoves)
			
			angleOfOrientation = avatarEntity.dynamiccomponent.GetAttribute('angleOfOrientation')
			angleOfOrientation.sety(math.atan2(relativeLat, relativeLon))
			avatarEntity.dynamiccomponent.SetAttribute('angleOfOrientation', angleOfOrientation)

			##Send ratios to dynamiccomponents	
			ratios = avatarEntity.dynamiccomponent.GetAttribute('ratios')
			ratios.setx(ratioLon)
			ratios.sety(ratioLat)
			avatarEntity.dynamiccomponent.SetAttribute('ratios', ratios)

			
			##In case that move() is called before the movement ends, set total's to 0
			totals = avatarEntity.dynamiccomponent.GetAttribute('totals')
			totals.setx(0)
			totals.sety(0)
			avatarEntity.dynamiccomponent.SetAttribute('totals', totals)
			
			reset = avatarEntity.dynamiccomponent.GetAttribute('reset')
			reset = True
			avatarEntity.dynamiccomponent.SetAttribute('reset', reset)
			
			##Send walk
			toWalk = avatarEntity.dynamiccomponent.GetAttribute('ifToWalk')
			toWalk = True
			avatarEntity.dynamiccomponent.SetAttribute('ifToWalk', toWalk)
			avatarEntity.SetAttribute('busted', False)
			##sent
			
		
		def spray():
			#Need to add some id for screens, to identify at this stage that which screen is being used.
			#Currently manipulating always 'screen', in future we can change all this by some identification.
			avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName("Bot" + str(msg['data']['_id'])).get()
			name = msg['data']['_id']
			#The lousy variable to decide the destiny of our screen. Currently can only use 1 screen, since we insert stuff to screen by name
			
			if name == 'str':
				screen = tundra.Scene().MainCameraScene().GetEntityByName("Galleria_Screen").get()
				screenvalues = screen.dynamiccomponent.GetAttribute('screenvalues')
				screenvalues.setx(1)
				screenvalues.sety(0)
				screenvalues.setz(0)
				screen.dynamiccomponent.SetAttribute('screenvalues', screenvalues)
			elif name == 'st':
				screen = tundra.Scene().MainCameraScene().GetEntityByName("Puistola_Screen").get()
				screenvalues = screen.dynamiccomponent.GetAttribute('screenvalues')
				screenvalues.setx(0)
				screenvalues.sety(1)
				screenvalues.setz(0)
				screen.dynamiccomponent.SetAttribute('screenvalues', screenvalues)
			else:
				screen = tundra.Scene().MainCameraScene().GetEntityByName("Galleria_Screen").get()
				screenvalues = screen.dynamiccomponent.GetAttribute('screenvalues')
				screenvalues.setx(0)
				screenvalues.sety(0)
				screenvalues.setz(1)
				screen.dynamiccomponent.SetAttribute('screenvalues', screenvalues)
			
			particle = tundra.Scene().MainCameraScene().GetEntityByName('Puistola_Spray').get()
			ifToSprayPar = particle.dynamiccomponent.GetAttribute('ifSprayedPar')
			ifToSprayPar = True
			particle.dynamiccomponent.SetAttribute('ifSprayedPar', ifToSprayPar)
			
			ifToSpray = screen.dynamiccomponent.GetAttribute('ifSprayed')
			ifToSprayed = True
			screen.dynamiccomponent.SetAttribute('ifSprayed', ifToSprayed)
		
			#In here we get the msg from server, that tells which team has painted, and sends the variable to
			#dynamiccomponent where its fetched by TeamMaterials.js and then used.
		
		
	
		#print "Websocket message received:"
		
		#print message.data.decode("utf-8")
			
		msg = json.loads(message.data.decode("utf-8"))    
		self.send(message.data, message.is_binary)
	

			
			
		actions = { "addMobileUser" : add, "movedUser" : move, "sprayGraffiti" : spray, "addPolice" : addPolice}

		actions[msg['action']]()      

			

if tundra.Server().IsAboutToStart():
	server = ws4py.server.geventserver.WebSocketServer(('0.0.0.0', 9999), websocket_class=GraffitiWebSocket)
	server.start()
	print "websocket server started."
	assert tundra.Frame().connect("Updated(float)", update)

	                             
	sceneapi = tundra.Scene()
	
	print "Websocket Server connecting to OnSceneAdded:", sceneapi.connect("SceneAdded(QString)", on_sceneadded)
	#on_sceneadded("TundraServer")
