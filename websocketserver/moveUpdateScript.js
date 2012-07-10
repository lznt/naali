function BotScript (entity, comp)
{
	this.me = entity;
	frame.Updated.connect(this, this.Update);
	
}

function BotScript.prototype.Update(t)
{
		
}

function BotScript.prototype.getAvatar()
{
	var speed = 1.6;
	var time = t;
	var avatarEntity = tundra.Scene().MainCameraScene().GetEntityByName("Bot" + str(msg['data']['_id'])).get();
	var yNow = avatarEntity.placeable.Position().y();
	var xNow = avatarEntity.placeable.Position().x();
	var zNow = avatarEntity.placeable.Position().z();
	var orientation = avatarEntity.placeable.Orientation()
	var angleOfOrientation = orientation.FromEulerZYX(0,angle,0);
	
	avatarEntity.placeable.SetOrientation(angle);
	
	
	
	

}