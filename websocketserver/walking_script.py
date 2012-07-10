import tundra
import websocketserver

print 'Win'


if walking == True:
	avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName("Avatar1").get()
	avatarEntity.animationcontroller.EnableAnimation(u'Walk' , True, 0.25, True)
else: 
	walking = False
