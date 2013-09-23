# API with users and posts

import hashlib, uuid
import flask_gasket.control

# uses userID as additional salt
# uuid.uuid4().hex
salt = 'df67a20945b34119a39f7bbe37a3697f'

# len(uuid.uuid4().hex)
SIZE_ID = 32

def authorize(args):

	serverDef = args['_all_models']['user']['_server']
	
	recv = args['_recv']
	conn = args['_conn']
	
	fullToken = recv['token']
	
	token = fullToken[:SIZE_ID]
	userID = fullToken[SIZE_ID:]
	
	user = conn.getPrimary(userID,serverDef)
	if user == None:
		return (False,flask_gasket.control.errorNotFound)
	
	if 'serverToken' not in user or token != user['serverToken']:
		return (False,flask_gasket.control.errorUnauthorized)
	
	if user['userID'] != userID:
		return (False,flask_gasket.control.errorUnauthorized)
	
	ret = { 'user': user }
	
	return (True,ret)
	
def userSend(args):
	fromServer = args['_last']
	return (True,fromServer)

def postSend(args):
	fromServer = args['_last']
	return (True,fromServer)

def postSendList(args):
	fromServer = args['_last']
	return (True,fromServer)

def signup(args):

	serverDef = args['_all_models']['user']['_server']
	
	recv = args['_recv']
	conn = args['_conn']
	
	userID = uuid.uuid4().hex
	
	# password
	password = recv['password']
	hashpass = hashlib.sha256(password + userID + salt).hexdigest()
	token = uuid.uuid4().hex
	
	# recv is added to toServer to complete serverDef
	toServer = {}
	toServer['hashpass'] = hashpass
	toServer['serverToken'] = token
	
	toClient = conn.create(userID,recv,toServer,serverDef)
	
	isSuccess = False
	if 'code' not in toClient:
		toClient['token'] = token + userID
		isSuccess = True
	
	return (isSuccess,toClient)
	
def login(args):

	serverDef = args['_all_models']['user']['_server']
	
	recv = args['_recv']
	conn = args['_conn']
	
	# if don't have user, get by userID
	if 'userID' not in recv:
	
		ret = conn.getSecondary('username',recv['username'],serverDef)
		if len(ret) == 0:
			return (False,flask_gasket.control.errorNotFound)
		user = ret[0]
		userID = user['userID']
	
	else:
		userID = recv['userID']
		
		# get raw
		user = conn.getPrimary(userID,serverDef)
		if user == None:
			return (False,flask_gasket.control.errorNotFound)
	
	# check hashpass
	password = recv['password']
	hashpass = hashlib.sha256(password + userID + salt).hexdigest()
	
	if hashpass != user['hashpass']:
		return (False,flask_gasket.control.errorUnauthorized)
	
	token = uuid.uuid4().hex
	user['serverToken'] = token
	
	toClient = conn.update(userID,{},user,serverDef,user)
	
	if 'code' not in toClient:
		toClient['token'] = token + userID
	
	return (True,toClient)

def logout(args):

	serverDef = args['_all_models']['user']['_server']
	
	recv = args['_recv']
	conn = args['_conn']
	
	user = args['_funcs']['authorize']['user']
	
	# remove token
	del user['serverToken']
	
	# conn.update
	conn.update(user['userID'],{},user,serverDef,user)
	
	# return success
	return (True,{})
	
def getUserByName(args):

	serverDef = args['_all_models']['user']['_server']
	
	recv = args['_recv']
	conn = args['_conn']
	
	ret = conn.getSecondary('username',recv['username'],serverDef)
	if len(ret) == 0:
		return (False,flask_gasket.control.errorNotFound)
	toClient = ret[0]
	
	return (True,toClient)

def getUserByID(args):

	serverDef = args['_all_models']['user']['_server']
	
	recv = args['_recv']
	conn = args['_conn']
	
	ret = conn.getPrimary(recv['userID'],serverDef)
	if ret == None:
		return (False,flask_gasket.control.errorNotFound)
	toClient = ret
	
	return (True,toClient)

def getUserPosts(args):

	serverDef = args['_all_models']['post']['_server']
	
	recv = args['_recv']
	conn = args['_conn']
	
	ret = conn.getSecondary('userID',recv['userID'],serverDef)
	ret = sortVals(ret)
	
	toClient = { 'list':ret }
	return (True,toClient)

def createPost(args):
	
	serverUserDef = args['_all_models']['user']['_server']
	serverDef = args['_all_models']['post']['_server']
	
	recv = args['_recv']
	conn = args['_conn']
	
	user = args['_funcs']['authorize']['user']
	
	toServer = {
		'username':user['username'],
		'name':user['name'],
		'userID':user['userID']
	}
	
	postID = uuid.uuid4().hex
	
	toClient = conn.create(postID,recv,toServer,serverDef)
	isSuccess = ('code' not in toClient)
	
	return (isSuccess,toClient)

def getPost(args):

	serverDef = args['_all_models']['post']['_server']
	
	recv = args['_recv']
	conn = args['_conn']
	
	ret = conn.getPrimary(recv['postID'],serverDef)
	if ret == None:
		return (False,flask_gasket.control.errorNotFound)
	toClient = ret
	
	return (True,toClient)
	