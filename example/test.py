from flask_gasket.testutil import *

def testUser():

	# malformed signup
	urlRec = '/user'
	sendJson = {
		'command':'signup', 
		'username':'guy1', 
		'password':'password1234', 
		'name':'User One',
		'bio':'test bio'
	}
	
	expectGet = {
		'status': 'error',
		'code': 410,
		'message':'invalid json, missing key: email'
	}
	
	res = runCommand(urlRec,sendJson)
	checkVals(expectGet,res,'malformed signup')
	
	# Sign Up
	urlRec = '/user'
	sendJson = {
		'command':'signup', 
		'username':'guy1', 
		'password':'password1234', 
		'name':'User One',
		'email':'guy1@example.com',
		'bio':'test bio'
	}
	
	expectGet = {
		'status': 'success',
		'code': 200,
		'userID': '<any>',
		'token': '<any>',
		'username': 'guy1', 
		'name': 'User One',
		'email': 'guy1@example.com',
		'bio': 'test bio', 
		'numPosts': 0,
		'createdAt': '<any>'
	}
	
	res = runCommand(urlRec,sendJson)
	checkVals(expectGet,res,'signup')
	
	# session token
	token = res['token']
	
	expect = {
		'status': 'error', 
		'message': 'username taken', 
		'code': 411
	}
	
	res = runCommand(urlRec,sendJson)
	checkVals(expect,res,'username taken')
	
	# Get User By username
	urlRec = '/user'
	sendJson = {
		'command':'get',
		'username':'guy1'
	}
	
	# don't need session token to just get a user's basic information
	del expectGet['token']
	
	res = runCommand(urlRec,sendJson)
	checkVals(expectGet,res,'get user by username')
	
	userID_1 = res['userID']
	
	# Get User By userID
	urlRec = '/user/' + userID_1
	sendJson = {'command':'get'}
	
	res = runCommand(urlRec,sendJson)
	checkVals(expectGet,res,'get user by userID')
	
	# Logout
	urlRec = '/user/' + userID_1
	sendJson = {
		'command':'logout',
		'token':token
	}
	expect = {'status':'success', 'code':200}
	
	res = runCommand(urlRec,sendJson)
	checkVals(expect,res,'logout')
	
	# Logout again
	expect = {'status':'error', 'code':414, 'message':'unauthorized'}
	
	res = runCommand(urlRec,sendJson)
	checkVals(expect,res,'multiple logout')

if __name__ == "__main__":

	# clear database before testing
	delAll()
	
	print 'Start Tests'
	testUser()
	