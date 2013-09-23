import json

####### Errors ############

# errors
errorNotFound = {'status':'error','code':404,'message':'not found'}
errorInvalidJson = {'status':'error','code':410,'message':'invalid json'}
errorInvalidUrl = {'status':'error','code':410,'message':'invalid url'}
errorInternalServer = {'status':'error','code':413,'message':'internal server'}
errorUnauthorized = {'status':'error','code':414,'message':'unauthorized'}

def valTaken(val):
	return {'status':'error','code':411,'message':val + ' taken'}

def invalidNoMatch(val):
	msg = 'argument ' + val + ' in url does not match json'
	return {'status':'error','code':415,'message':msg}
	
def jsonError(code,msg):
	return {'status':'error','code':code,'message':msg}
	
def invalidJsonKey(key):
	return {'status':'error','code':410,'message':'invalid json, missing key: ' + key}

def invalidJsonKeylist(keysList):
	return {'status':'error','code':410,'message':'invalid json, expected keys: ' + str(keysList)}

def invalidJsonCommand(commandsList):
	return {'status':'error','code':410,
		'message':'invalid json, expected commands: ' + str(commandsList)}

def invalidObject(objList):
	return {'status':'error','code':410,
		'message':'invalid json, expected object request: ' + str(commandsList)}

def createError(code,msg):
	return (False,nitro.control.jsonError(code,msg))

#############################

def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = _decode_dict(item)
        rv.append(item)
    return rv

def _decode_dict(data):
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
           key = key.encode('utf-8')
        if isinstance(value, unicode):
           value = value.encode('utf-8')
        elif isinstance(value, list):
           value = _decode_list(value)
        elif isinstance(value, dict):
           value = _decode_dict(value)
        rv[key] = value
    return rv

def loadJson(data):

	obj = json.loads(data, object_hook=_decode_dict)
	return obj

def loadJsonFile(fileName):

	# can't have unicode characters in config file
	data = open(fileName).read()
	obj = json.loads(data, object_hook=_decode_dict)
	return obj
	
def loadJsonReg(fileName):

	data = open(fileName).read()
	obj = json.loads(data)
	return obj

######### Internal Enum ############

class NotPresent():
	pass

#############################

def printJson(val):

	show = sorted(val.keys())
	for key in show:
		print str(key) + ': ' + str(val[key])
