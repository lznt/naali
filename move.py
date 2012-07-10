import tundra


def __init__(self):
	print 'Something'

def move2(i):
	avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName("Bot").get()#Change this to Bot + something when testing on phone
	#if i == True:
	avatarEntity.animationcontroller.EnableAnimation('Walk', True, 0.25, False)
	#	walkAnimName = 'Walk'
	#	avatarEntity.animationcontroller.animationState = walkAnimName
	#	avatarEntity.animationcontroller.SetAnimationSpeed(walkAnimName, 0.60)
	#	avatarEntity.animationcontroller.EnableAnimation(walkAnimName , True, 0.25, False)
	#	print 'run'
	#else: 
	#	avatarEntity.animationcontroller.DisableAllAnimations()
print 'hello'