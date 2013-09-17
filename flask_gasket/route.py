# this controls all routing information to and from application

import json, copy
import control
import uuid
import data
from flask import Flask, request

DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)

def setConfig(config,viewMod):

	allModels = readModels(config)
	# print allModels['user']['_recv']
	# allModels
	
	rootUrls = config['_route']['api']
	assumed = config['_route']['_assume']
	allCommands = config['_route']['_funcs']
	setMethods('/api',rootUrls,viewMod,allModels,assumed,allCommands)
	
def moveUpKey(globalAssume,set,key):
	
	if key in set:
		return set[key]
	
	elif key in globalAssume:
		return globalAssume[key]
	
	return control.NotPresent

def sharedVals(vals,defaultInfo,statusInfo,uniqueInfo):

	# default
	if defaultInfo != control.NotPresent:
		vals['_default'] = defaultInfo
	
	# optional
	if statusInfo != control.NotPresent:
		vals['_optional'] = statusInfo
		
	# unique
	if uniqueInfo != control.NotPresent:
		vals['_unique'] = uniqueInfo

def searchListSizeID(config,otherModelKey,otherKey):
	
	ret = []
	models = config['_model']
	
	for modelKey in models:
		modelVal = models[modelKey]
		
		for key in modelVal:
			set = modelVal[key]
			
			if '_counter_list' in set:
				counterSet = set['_counter_list']
				
				if counterSet['other_model'] == otherModelKey and \
					counterSet['other_id'] == otherKey:
				
					counterModel = modelKey
					counterName = key
					
					ret = (counterModel,counterName)
	
	return ret

def readModels(config):
	
	allModels = {}
	
	models = config['_model']
	globalAssume = models.get('_assume',{})
	
	for modelKey in models:
		modelVal = models[modelKey]
		
		newModelRecv = {}
		newModelSend = {}
		
		newModelServer = {}
		newModelServerInd = {}
		newModelServerVal = {}
		
		primaryKey = None
		
		for key in modelVal:
			set = modelVal[key]
			
			clientInfo = moveUpKey(globalAssume,set,'_client')
			serverInfo = moveUpKey(globalAssume,set,'_server')
			typeInfo = moveUpKey(globalAssume,set,'_type')
			
			defaultInfo = moveUpKey(globalAssume,set,'_default')
			statusInfo = moveUpKey(globalAssume,set,'_optional')
			uniqueInfo = moveUpKey(globalAssume,set,'_unique')
			
			if '_recv' in clientInfo:
				recvVals = {}
				recvVals['_type'] = typeInfo
				sharedVals(recvVals,defaultInfo,statusInfo,uniqueInfo)
				
				newModelRecv[key] = recvVals
				
			if '_send' in clientInfo:
			
				sendVals = {}
				sendVals['_type'] = typeInfo
				sharedVals(sendVals,defaultInfo,statusInfo,uniqueInfo)
				
				newModelSend[key] = sendVals
			
			# is in server
			if len(serverInfo) > 0:
				
				# make sure user input in relation to
				# server is valid configuration
				
				serverVals = {}
				serverVals['_type'] = typeInfo
				
				if '_value' in serverInfo:
					serverVals['_server'] = '_value'
				
				if '_index' in serverInfo:
					serverVals['_server'] = '_index'
					
					# if it is an index, it might have a list size counter 
					# associated with it, search through config to find this
					ret = searchListSizeID(config,modelKey,key)
					
					if ret != []:
						serverVals['_counter_model_name'] = ret
				
				if '_index_multi' in serverInfo:
					serverVals['_server'] = '_index_multi'
				
				if typeInfo == '_primary':
					serverVals['_server'] = '_primary'
					primaryKey = key
				
				sharedVals(serverVals,defaultInfo,statusInfo,uniqueInfo)
				
				newModelServer[key] = serverVals
		
		newModelServer = {
			'_container': modelKey,
			'_primaryKey': primaryKey,
			'_data': newModelServer
		}
		
		newModel = { 	'_recv':newModelRecv,
						'_send':newModelSend,
						'_server':newModelServer	}
		
		allModels[modelKey] = newModel
		
	return allModels
	
# for required send and recv to and from client
def setVals(toSet,getFrom,allModels,attributes):
			
	vals = {}
	modelKey = None
	
	if isinstance(toSet,str) or isinstance(toSet,unicode):
		
		# get model values
		if toSet.startswith('_model_'):
			modelKey = toSet[len('_model_'):]
			vals = allModels[modelKey][getFrom]
			
		elif toSet.startswith('_optional_model_'):
			modelKey = toSet[len('_optional_model_'):]
			vals = allModels[modelKey][getFrom]
		
			vals = copy.deepcopy(vals)
			for key in vals:
				val = vals[key]
				val['_optional'] = True
		
		elif toSet.startswith('_list_model_'):
			modelKey = toSet[len('_list_model_'):]
			modelVals = allModels[modelKey][getFrom]
			
			attributes['isList'] = True
			vals = { 'list':modelVals }
			
		else:
			print toSet
			assert(False)
	else:
		keys = toSet.keys()
		vals = copy.deepcopy(toSet)
		
		# don't include if value is optional
		# for key in keys:
		#	if '_optional' in vals[key]:
		#		del vals[key]
	
	return vals

# urlSet is commands within the baseUrl
# viewMod is the view module
def createCommands(baseUrl,urlSet,viewMod,allModels,assumed,allCommands):
	
	funcs = urlSet['_']
	commands = {}
	
	# set commands
	for funcDict in funcs:
		
		commandName = funcDict['_command']
		
		# if not present, go up
		if '_recv' not in funcDict:
			funcDict['_recv'] = assumed['_recv']
		
		if '_send' not in funcDict:
			funcDict['_send'] = assumed['_send']
		
		attrRec = {}
		attrSend = {}
		
		toRecv = funcDict['_recv']
		valsToRec = setVals(toRecv,'_recv',allModels,attrRec)
		
		toSend = funcDict['_send']
		valsToSend = setVals(toSend,'_send',allModels,attrSend)
		
		# fill in assumed vals
		if '_recv' in assumed:
			assumeRecv = assumed['_recv']
			for key in assumeRecv:
				valsToRec[key] = assumeRecv[key]
		
		if '_send' in assumed:
			assumeSend = assumed['_send']
			for key in assumeSend:
				valsToSend[key] = assumeSend[key]
		
		def getFuncList(name,curAllCommands):
		
			if name in funcDict:
				val = funcDict[name]
				if isinstance(val,str):
					curAllCommands += [val]
				elif isinstance(val,list):
					curAllCommands += val
				else:
					assert(False)
		
		curAllCommands = []
		getFuncList('_pre',curAllCommands)
		getFuncList('_func',curAllCommands)
		getFuncList('_post',curAllCommands)
		
		funcOut = []
		
		# add to _recv_def based on pre
		# add function
		for allComInfoKey in curAllCommands:
			
			if allComInfoKey in allCommands:
				
				allComInfo = allCommands[allComInfoKey]
				
				if '_recv' in allComInfo:
					toAdd = setVals(allComInfo['_recv'],'_recv',allModels,attrRec)
					valsToRec = dict(valsToRec.items() + toAdd.items())
				
				if '_send' in allComInfo:
					toAdd = setVals(allComInfo['_send'],'_send',allModels,attrSend)
					valsToSend = dict(valsToSend.items() + toAdd.items())
			
			allComFunc = getattr(viewMod, allComInfoKey)
			funcOut.append((allComInfoKey,allComFunc))
		
		# methodName = funcDict['_func']
		# methodToCall = getattr(viewMod, methodName)
		# funcOut.append((methodName,methodToCall))
		
		# for paging
		if 'list' in valsToSend:
			valsToRec['page'] = { '_type': '_string', '_optional': True }
		
		valsToRec = { '_data':valsToRec }
		for attrKey in attrRec:
			valsToRec[attrKey] = attrRec[attrKey]
		
		valsToSend = { '_data':valsToSend }
		for attrKey in attrSend:
			valsToSend[attrKey] = attrSend[attrKey]
		
		commands[commandName] = {
			
			# these are definitions, don't contain values
			'_recv_def': valsToRec,
			'_send_def': valsToSend,
			'_funcs': funcOut,
			'_http':'POST'
		}
		
		if '_http' in funcDict:
			commands[commandName]['_http'] = funcDict['_http']
	
	return commands

# creates splitter closure which
# splits commands to the functions that will run from view
def createSplitter(baseUrl,commands,allModels):
	
	methods = ['POST','GET']
	
	# have to create splitter for each method
	for method in methods:
		
		# determine if any of this method type present
		createMethod = False
		for command in commands:
			if commands[command]['_http'] == method:
				createMethod = True
			
		if not createMethod:
			continue
		
		otherRecv = None
		if method == 'GET':
			otherRecv = { 'command':'get' }
		
		# define closure for each which will check all the
		# right values are received from and returned to client
		def splitter(**kwargs):
			
			if otherRecv != None:
				recv = otherRecv
			else:
				try:
					recv = json.loads(request.data)
				except ValueError:
					ret = control.errorInvalidJson
					return json.dumps(ret)
		
			if 'command' not in recv:
				ret = control.invalidJsonCommand(commands.keys())
				return json.dumps(ret)
		
			commandName = recv['command']
		
			if commandName not in commands:
				ret = control.invalidJsonCommand(commands.keys())
				return json.dumps(ret)
		
			command = commands[commandName]
			recSet = command['_recv_def']
			sendSet = command['_send_def']
		
			# url and json arguments are treated the same
			for getKey in kwargs:
				getVal = kwargs[getKey]
			
				# must be the same if key is present in both url and json
				if otherRecv == None and getKey in recv and getVal != recv[getKey]:
					ret = control.invalidNoMatch(getKey)
					return json.dumps(ret)
			
				recv[getKey] = getVal
			
			# check received against what is expected
			(isValid,ret) = data.matchRecv(recv,recSet,kwargs)
			if not isValid:
				return json.dumps(ret)
			validRecv = ret
		
			conn = data.RiakConn(allModels)
		
			newArgs = {
				'_recv_def':recSet,
				'_send_def':sendSet,
			
				'_all_models':allModels,
				'_conn':conn,
				'_recv':validRecv,
			
				'_funcs':{}
			}
		
			# run pre commands
			if '_funcs' in command and len(command['_funcs']) > 0:
				allCommands = command['_funcs']
				for allCommandKey, allCommand in allCommands:
				
					got = allCommand(newArgs)
					(isSuccess,res) = got
					if not isSuccess:
						return json.dumps(res)
			
					newArgs['_funcs'][allCommandKey] = res
					newArgs['_last'] = res
		
			# the very last value is treated as what is sent to client
			send = newArgs['_last']
		
			# only add code if not added already
			# or not an error
			if 'code' not in send:
			
				# check for send
				send = data.matchSend(send,sendSet)
			
				send['code'] = 200
				send['status'] = 'success'
			
			# errors always only return: code (not 200), status ('error'), and message
			
			ret = send
			return json.dumps(ret)
			
		if DEBUG:
		
			oldSplitter = splitter
		
			def splitter(**kwargs):
		
				print '---------------------------------'
				print 'req:'
				print request.data
				print ''
				
				ret = oldSplitter(**kwargs)
		
				print 'send:'
				print ret
				print ''
				
				return ret
		
		# add splitter to app
		splitter.methods = [method]
		app.add_url_rule(baseUrl,baseUrl,splitter)

# recurse through URLs
def setMethods(baseUrl,urlSet,viewMod,allModels,assumed,allCommands):
	
	if '_' in urlSet:
		
		commands = createCommands(baseUrl,urlSet,viewMod,allModels,assumed,allCommands)
		createSplitter(baseUrl,commands,allModels)
		
	for key in urlSet:
		
		if key != '_':
			newUrlSet = urlSet[key]
			newBaseUrl = baseUrl + '/' + key
			
			setMethods(newBaseUrl,newUrlSet,viewMod,allModels,assumed,allCommands)

def getApp():
	return app

def startApp(config,viewMod):
	
	setConfig(config,viewMod)
	
	# debug=True
	app.run(host='0.0.0.0',port=5600,debug=True)
	