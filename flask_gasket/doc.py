# generates documentation based on configuration file

import json
import copy
import route

# information shown as:
# comment
# url
# command
# recv
# send

# dict, _model_<model>, _list_model_<model>
def concDict(d1,d2,fullDict,name):
	
	if isinstance(d2,str) or isinstance(d2,unicode):
		models = fullDict['_models']
		
		if d2[:len('_model_')] == '_model_':
		
			model = d2[len('_model_'):]
			thisGet = models[model][name]
			
			concDict(d1,thisGet,fullDict,name)
		
		elif d2[:len('_optional_model_')] == '_optional_model_':
		
			model = d2[len('_optional_model_'):]
			thisGet = models[model][name]
			
			concDict(d1,thisGet,fullDict,name)
			
		elif d2[:len('_list_model_')] == '_list_model_':
			
			model = d2[len('_list_model_'):]
			thisGet = models[model][name]
			
			myList = {}
			concDict(myList,thisGet,fullDict,name)
			
			d1['list'] = myList
			
		else:
			print d2
			assert(False)
		
		return
	
	for key in d2:
		d1[key] = copy.deepcopy(d2[key])

def getRetDict(name,com,fullDict):

	funcs = fullDict['_route']['_funcs']
	assume = fullDict['_route']['_assume'][name]
	
	retDict = {}
	concDict(retDict,assume,fullDict,name)
	
	for stageName in ['_pre','_post']:
	
		if stageName in com:
			cur = com[stageName]
			if name in funcs[cur]:
				curDict = funcs[cur][name]
				concDict(retDict,curDict,fullDict,name)
	
	if name in com:
		concDict(retDict,com[name],fullDict,name)
		
	return retDict

# combine main, _funcs, _assume
def getName(retDict):

	conv = ''
	
	for key in sorted(retDict):
		val = retDict[key]
		
		if key == 'list':
			
			conv += '\tlist:\n'
			
			for listKey in sorted(val):
				listVal = val[listKey]
				
				outVal = '<blank>'
				if isinstance(listVal,dict) and '_type' in listVal:
					# outVal = listVal['_type']
					outVal = '<string>'
					
					if '_optional' in listVal:
						outVal = '<optional>'
		
				conv += '\t\t' + str(listKey) + ': ' + outVal + '\n'
		
		else:
			
			outVal = '<blank>'
			if isinstance(val,dict) and '_type' in val:
				# outVal = val['_type']
				outVal = '<string>'
				
				if '_optional' in val:
					outVal = '<optional>'
		
			conv += '\t' + str(key) + ': ' + outVal + '\n'
	
	return conv

def createCommands(baseUrl,baseDict,toStr,fullDict):
	
	for key in sorted(baseDict):
		
		if key == '_':
		
			for com in sorted(baseDict['_']):
			
				curStr = ''
				curStr += '--------------------\n'
				curStr += 'url: ' + baseUrl + '\n'
				curStr += 'command: ' + com['_command'] + '\n\n'
				
				if '_#' in com:
					curStr += 'comment: ' + com['_#'] + '\n\n'
				
				recvRetDict = getRetDict('_recv',com,fullDict)
				sendRetDict = getRetDict('_send',com,fullDict)
				
				if 'list' in sendRetDict:
					recvRetDict['page'] = { '_type':'list', '_optional':True }
				
				recv = getName(recvRetDict)
				send = getName(sendRetDict)
				
				curStr += 'recv:\n' 
				curStr += '\tcommand: ' + com['_command'] + '\n'
				curStr += recv + '\n'
				
				curStr += 'send:\n'
				
				curStr += '\tcode: 200\n'
				curStr += '\tstatus: success\n'
				curStr += send + '\n'
				
				toStr['str'] += curStr
		
		else:
		
			newBaseUrl = baseUrl + '/' + key
			newBaseDict = baseDict[key]
	
			createCommands(newBaseUrl,newBaseDict,toStr,fullDict)

# write document with firstOut at top
def writeDoc(firstOut):

	fi = open('config.json','r')
	confStr = fi.read()
	conf = json.loads(confStr)

	baseUrl = '/api'

	baseDict = conf['_route']['api']
	toStr = { 'str':'' }

	models = route.readModels(conf)
	fullDict = conf
	fullDict['_models'] = models

	#print ''
	#print models
	#print ''

	createCommands(baseUrl,baseDict,toStr,fullDict)

	writeOut = firstOut + toStr['str']

	toFile = open('api.txt','w')
	toFile.write(writeOut)
	toFile.close()

if __name__ == "__main__":
	writeDoc()
	print 'wrote doc'
