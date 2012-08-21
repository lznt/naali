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
counter = 1

scene = None

def log(s):
    print "WebsocketServer:", s

def newclient(connectionid):
    if scene is not None:
        tundra.Server().UserConnected(connectionid, 0, 0)
        avent = scene.CreateEntity("EC_Avatar", 'EC_DynamicComponent')
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
	
	#server.UserDisconnected().connect(this.ServerHandleUserDisconnected)
	
    #assert scene.connect("AttributeChanged(IComponent*, IAttribute*, AttributeChange::Type)", onAttributeChanged)
    #assert scene.connect("EntityCreated(Entity*, AttributeChange::Type)", onNewEntity)

    #assert scene.connect("ComponentAdded(Entity*, IComponent*, AttributeChange::Type)", onComponentAdded)

    #assert scene.connect("EntityRemoved(Entity*, AttributeChange::Type)", onEntityRemoved)

#This is the update function that runs on every frametime on realXtend side.
def update(t):
	if server is not None:
		#server.next()
		server._stopped_event.wait(timeout=0.0001)
		if GraffitiWebSocket.ReadyWatcher == False:
			setScriptOnLoad()
		
		#This functionality makes sure that we send msg's only when a player has been busted. Sends the players name to server.
		#Server then messages the player for being busted.
		if GraffitiWebSocket.Ready == True:
			Logic = tundra.Scene().MainCameraScene().GetEntityByName("Logic").get()
			if Logic.dynamiccomponent.GetAttribute('Busted') == True:
				player = Logic.dynamiccomponent.GetAttribute('PlayerName')
				sendAll({"action" : "busted" , "data":{"user": {"name" : player}}})
			if Logic.dynamiccomponent.GetAttribute('newMsg') == True:
				#Add send to server here
				#sendAll(Logic.dynamiccomponent.GetAttribute('msg'))
				Logic.dynamiccomponent.SetAttribute('newMsg', False)

#Currently an empty function, made for checking that if entities are yet created
def setScriptOnLoad():
	logic = tundra.Scene().MainCameraScene().GetEntityByName("Logic").get()
	while(logic == None):
		print 'none'
	
	GraffitiWebSocket.ReadyWatcher = True
	

#Function that sends the server an msg
def sendAll(data):
	for client in clients:
		try:
			client.send(json.dumps(data))

		except socket.error:
			pass #client has been disconnected, will be noted later & disconnected by another part


class GraffitiWebSocket(WebSocket):
	#Variables:
	'''
	avatarEntity = avatarentity variable to save the avatar in.
	relativeLat, relativeLon = The actual distances to be walked. (Calculated with haversine)
	Ready = to check that a player has been added before running a if in update. Otherwise entity will be None and rex will crash
	Logic = Logic entity
	ReadyWatcher = for onScriptLoad function to know that the scene is ready and we can enter the function.
	'''
	avatarEntity = None
	relativeLat = 0
	relativeLon = 0
	Ready = False
	Logic = None
	ReadyWatcher = False
	
	def opened(self):
		print "Websocket client connected"
		#self.send('Websocket client connected')
		clients.add(self)

	#Function for received messages from server
	def received_message(self, message):
		"""
		Automatically sends back the provided ``message`` to
		its originating endpoint.
		"""
		print(message)
		##Static values for 0,0,0 in our map in real world coordinates.
		lat1 = 65.012124
		lon1 = 25.473395
		#lat1 = 65.058325
		#lon1 = 25.468476
	
		#This is the add function that adds a new player when a phone is connected to a server and sends this msg. Includes all needed attributes 
		#to run scripts and make checks, logicwise. 
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
			#For attachments in botscript
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'attachments')
			#Ratios for x and z in movement
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'ratios')
			#RelativeLat and Lon(the actual movement of z and x)
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'toMoves')
			#The angle that the player needs to turn when going somewhere
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'angleOfOrientation')
			#a dynamic value to know of the player is able to walk(is not busted or doing something else)
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'ifToWalk')
			#a dynamic value to know if the player is busted.
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'Busted')
			#totalLat and Lon for the script. These are always 0 at start
			avatarEntity.dynamiccomponent.CreateAttribute('float3', 'totals')
			#A reset value for knowing that the move() has been called
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'reset')
			#Spraying dynamiccomponent to know if a player is spraying
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'Spraying')
			avatarEntity.dynamiccomponent.SetAttribute('Spraying', False)
			#Need to add some value to check players team and set it after that.
			avatarEntity.dynamiccomponent.CreateAttribute('string', 'Team')
			#The role of the entity(NOT USED CURRENTLY)
			avatarEntity.dynamiccomponent.CreateAttribute('string', 'Role')
			#A dynamic value to know if the player is ready to spray.
			avatarEntity.dynamiccomponent.CreateAttribute('bool', 'rdyToSpray')
			avatarEntity.dynamiccomponent.SetAttribute('Role', 'Player')
			avatarEntity.script.className = "BotScriptApp.BotScript"
			avatarEntity.dynamiccomponent.SetAttribute('Team', str(msg['data']['user']['team']))
			log = tundra.Scene().MainCameraScene().GetEntityByName('Logic').get()
			log.dynamiccomponent.SetAttribute('addedPlayer', True)
			log.dynamiccomponent.SetAttribute('newSocketPlayer', True)
			log.dynamiccomponent.CreateAttribute('string', 'Player')
			log.dynamiccomponent.SetAttribute('Player', avatarEntity.name)
			log.dynamiccomponent.CreateAttribute('bool', 'newMsg')
			log.dynamiccomponent.CreateAttribute('string', 'msg')
			GraffitiWebSocket.Ready = True

			#Approx 0 on oulu3d
			#long = 25.473395
			#lat = 65.012124
		
		
		#This function adds policebots to our scene.
		def addPolice():
			#Some sort of counter to determine how many polices are added (if not static)
			policeEntity = tundra.Scene().MainCameraScene().CreateEntity(scene.NextFreeId(),["EC_Placeable", "EC_DynamicComponent", "EC_AnimationController", "EC_Mesh", "EC_RigidBody", "EC_Avatar"]).get()
			policeEntity.SetTemporary(True)
			policeEntity.GetOrCreateComponent("EC_Script", 'Police')
			policeEntity.placeable.visible = False
			policeEntity.SetName("Police")
			policeEntity.rigidbody.mass = 0
			#policeEntity.placeable.SetPosition(0, -4, 0)
			policeEntity.dynamiccomponent.CreateAttribute('bool', 'Spraying')
			#For attachments in botscript
			policeEntity.dynamiccomponent.CreateAttribute('bool', 'attachments')
			#Attachment naem to distinguish them
			policeEntity.dynamiccomponent.CreateAttribute('string', 'attachmentname');
			policeEntity.dynamiccomponent.SetAttribute('attachmentname', policeEntity.Id())
			Logic = tundra.Scene().MainCameraScene().GetEntityByName('Logic')
			policeEntity.script.className = "PoliceScriptApp.PoliceScript"

		#This is the move function, same principle is used in policemen and in spray, in this we calculate in Python, others in JS. So see
		#for different ways to do it. Haversine.py does the calculations in this one.
		def move():
			avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName(str(msg['data']['user']['name'])).get()
			lat =  msg['data']['localization']['lat']
			lon =  msg['data']['localization']['lon']
			lat2 = lat
			lon2 = lon
			speed = 1.6
			
			#Call haversine to calculate lat, lon and distance
			latitudeInMeters = haversine.calcLat(lat1, lat2)
			longitudeInMeters = haversine.calcLong(lon1, lon2, lat1, lat2)
			GraffitiWebSocket.distanceInMeters = haversine.distance(lat1, lat2, lon1, lon2)
			#to know in which quad we are in.
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
			
		
		#The spray function when a player sprays in game.
		def spray():
			#Get spraying player, sprayed venue and particleEffect for that venue.
			avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName(str(msg['data']['user']['name'])).get()
			screen = tundra.Scene().MainCameraScene().GetEntityByName(str(msg['data']['venue']['name'])).get()
			particle = tundra.Scene().MainCameraScene().GetEntityByName(str(msg['data']['venue']['name']) + "spray").get()
			Logic = tundra.Scene().MainCameraScene().GetEntityByName('Logic').get()
			id = Logic.dynamiccomponent.GetAttribute('id')
			#The particle that needs to spray.
			particleName = (str(msg['data']['venue']['name']) + "spray")
			#The screen that we are spraying(screens are spots that players spray in)
			screenName = str(msg['data']['venue']['name'])
			#Team of the player spraying.
			team = avatarEntity.dynamiccomponent.GetAttribute('Team')
			#Players current position
			playerPos = screen.dynamiccomponent.GetAttribute('playerPos')
			#Particles position, cos that is the place where the player moves when spraying.
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
		

			
		#Actions in game.
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
