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

    #assert scene.connect("AttributeChanged(IComponent*, IAttribute*, AttributeChange::Type)", onAttributeChanged)
    #assert scene.connect("EntityCreated(Entity*, AttributeChange::Type)", onNewEntity)

    #assert scene.connect("ComponentAdded(Entity*, IComponent*, AttributeChange::Type)", onComponentAdded)

    #assert scene.connect("EntityRemoved(Entity*, AttributeChange::Type)", onEntityRemoved)

    
def update(t):
	if server is not None:
		#server.next()
		server._stopped_event.wait(timeout=0.0001)
		#print 'smth'
		#This functionality makes sure that we send msg's only when a player has been busted. Sends the players name to server.
		#Server then messages the player for being busted.
		if GraffitiWebSocket.Ready == True:
			Logic = tundra.Scene().MainCameraScene().GetEntityByName("Logic").get()
			if Logic.dynamiccomponent.GetAttribute('Busted') == True:
				player = Logic.dynamiccomponent.GetAttribute('PlayerName')
				sendAll({"action" : "busted" , "data":{"user": {"name" : player}}})
		#Here attanch someday the messagesender to phone.
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


class GraffitiWebSocket(WebSocket):
	
	walk = False
	avatarEntity = None
	police = None
	policeId = 0
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
	Ready = False
	Logic = None
	Busted = False
	
	def opened(self):
		print "Websocket client connected"
		#self.send('Websocket client connected')
		clients.add(self)
		
	def received_message(self, message):
		"""
		Automatically sends back the provided ``message`` to
		its originating endpoint.
		"""
		print(message)
		lat1 = 65.012124
		lon1 = 25.473395
		#lat1 = 65.058325
		#lon1 = 25.468476
		
		def add():
			#In final version visible after the first move.
			print "Player Added"
			avatarEntity =  tundra.Scene().MainCameraScene().CreateEntity(scene.NextFreeId(), ["EC_Placeable","EC_DynamicComponent", "EC_AnimationController", "EC_Mesh", "EC_RigidBody", "EC_Avatar"]).get()
			avatarEntity.SetTemporary(True)
			avatarEntity.GetOrCreateComponent("EC_Script", 'Player')
			avatarEntity.placeable.visible = True
			avatarEntity.SetName(str(msg['data']['user']['name']))
			avatarEntity.rigidbody.mass = 0
			avatarEntity.placeable.SetPosition(0, -4, 0)
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'ratios')
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'toMoves')
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'angleOfOrientation')
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'ifToWalk')
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'Busted')
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'totals')
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'reset')
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'Spraying')
			avatarEntity.dynamiccomponent.SetAttribute('Spraying', False)
			#Need to add some value to check players team and set it after that.
			avatarEntity.dynamiccomponent.CreateAttribute('string', 'Team')
			avatarEntity.dynamiccomponent.CreateAttribute('string', 'Role')
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'rdyToSpray')
			avatarEntity.dynamiccomponent.SetAttribute('Role', 'Player')
			#avatarEntity.avatar.appearanceRef.setRef("default_avatar.avatar")
			avatarEntity.script.className = "BotScriptApp.BotScript"
			#C2.className = "BotAndPoliceApp.BotAndPolice"
			avatarEntity.dynamiccomponent.SetAttribute('Team', str(msg['data']['user']['team']))
			GraffitiWebSocket.Ready = True
			#Approx 0 on oulu3d
			#long = 25.473395
			#lat = 65.012124
			
		def addPolice():
			#Some sort of counter to determine how many polices are added (if not static)
			policeEntity = tundra.Scene().MainCameraScene().CreateEntity(scene.NextFreeId(),["EC_Placeable", "EC_DynamicComponent", "EC_AnimationController", "EC_Mesh", "EC_RigidBody", "EC_Avatar", "EC_Script"]).get()
			policeEntity.SetTemporary(True)
			policeEntity.placeable.visible = False
			policeEntity.SetName("Police")
			#GraffitiWebSocket.PoliceId + 1
			policeEntity.rigidbody.mass = 0
			#policeEntity.placeable.SetPosition(0, -4, 0)
			policeEntity.dynamiccomponent.CreateAttribute('bool', 'Spraying')
			Logic = tundra.Scene().MainCameraScene().GetEntityByName('Logic')
			policeEntity.script.className = "PoliceScriptApp.PoliceScript"

			
		def move():
			
			avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName(str(msg['data']['user']['name'])).get()
			lat =  msg['data']['localization']['lat']
			lon =  msg['data']['localization']['lon']
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
			##sent
			
		
		def spray():
			#Get spraying player, sprayed venue and particleEffect for that venue.
			avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName(str(msg['data']['user']['name'])).get()
			screen = tundra.Scene().MainCameraScene().GetEntityByName(str(msg['data']['venue']['name'])).get()
			particle = tundra.Scene().MainCameraScene().GetEntityByName(str(msg['data']['venue']['name']) + "spray").get()
			Logic = tundra.Scene().MainCameraScene().GetEntityByName('Logic').get()
			id = Logic.dynamiccomponent.GetAttribute('id')
			
			particleName = (str(msg['data']['venue']['name']) + "spray")
			screenName = str(msg['data']['venue']['name'])
			team = avatarEntity.dynamiccomponent.GetAttribute('Team')
			playerPos = screen.dynamiccomponent.GetAttribute('playerPos')
			particlePos = avatarEntity.dynamiccomponent.GetAttribute('particlePos')
			#Set player current position, to use them to calculate distance from area.
			curPosx = avatarEntity.placeable.Position().x()
			curPosz = avatarEntity.placeable.Position().z()
			playerPos.setx(curPosx)
			playerPos.setz(curPosz)
			#Position of screen, to move player to spray if spraying in that area.
			particlePosx = particle.placeable.Position().x()
			particlePosz = particle.placeable.Position().z()
			particlePos.setx(particlePosx)
			particlePos.setz(particlePosz)
			#Set all needed information for dynamiccomponents, so that scripts can use them.
			screen.dynamiccomponent.SetAttribute('screenName', str(msg['data']['venue']['name']))
			screen.dynamiccomponent.SetAttribute('playerPos', playerPos)
			screen.dynamiccomponent.SetAttribute('PlayerId', str(msg['data']['user']['name']))
			screen.dynamiccomponent.SetAttribute('PlayerTeam' , team)
			screen.dynamiccomponent.SetAttribute('PlayerName', str(msg['data']['user']['name']))
			screen.dynamiccomponent.SetAttribute('Spraying', True)
			particle.dynamiccomponent.SetAttribute('particleName', str(msg['data']['venue']['name']) + "spray")
			particle.dynamiccomponent.SetAttribute('PlayerName', str(msg['data']['user']['name']))
			particle.dynamiccomponent.SetAttribute('Spraying', True)
			avatarEntity.dynamiccomponent.SetAttribute('particlePos', particlePos)
			avatarEntity.dynamiccomponent.SetAttribute('Spraying', True)
			avatarEntity.dynamiccomponent.SetAttribute('screenName', str(msg['data']['venue']['name']))
			
			
	
		#print "Websocket message received:"
		
		#print message.data.decode("utf-8")
			
		msg = json.loads(message.data.decode("utf-8"))    
		#self.send(message.data, message.is_binary)
		

			
			
		actions = { "add" : add, "move" : move, "spray" : spray, "addPolice" : addPolice}

		actions[msg['action']]()      

	
if tundra.Server().IsAboutToStart():
	server = ws4py.server.geventserver.WebSocketServer(('0.0.0.0', 9999), websocket_class=GraffitiWebSocket)
	server.start()
	print "websocket server started."
	assert tundra.Frame().connect("Updated(float)", update)

	                            
	sceneapi = tundra.Scene()
	
	print "Websocket Server connecting to OnSceneAdded:", sceneapi.connect("SceneAdded(QString)", on_sceneadded)
	#on_sceneadded("TundraServer")
