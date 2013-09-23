import riak, json, re
import sys, os, time, uuid

def printAll():

	client = riak.RiakClient(port=8087, transport_class=riak.RiakPbcTransport)
	buckets = client.get_buckets()
	
	for buckName in buckets:
		print 'bucket name: ' + buckName
		buck = client.bucket(buckName)
		keys = buck.get_keys()
		print ''
		print 'keys'
		
		for key in keys:
			print key
			info = buck.get(key)
			print info.get_data()
			
			indexes = info.get_indexes()
			for ind in indexes:
				print ind
			print ''

# delete all data in Riak database
def delAll():
	
	client = riak.RiakClient(port=8087, transport_class=riak.RiakPbcTransport)
	buckets = client.get_buckets()
	
	for buckName in buckets:
		buck = client.bucket(buckName)
		keys = buck.get_keys()
		
		for key in keys:
			buck.get(key).delete()

def runCommand(urlRec,sendJson):

	sendJsonStr = json.dumps(sendJson)

	command = '''curl -XPOST \
	-H 'Content-Type:application/json' \
	-d \'''' + sendJsonStr + '''\' \
	http://localhost:5600/api''' + urlRec + ' > response.txt 2> /dev/null'
	
	# print command
	os.system(command)
	
	fi = open('response.txt','r')
	ans = fi.read()
	
	try:
		getJson = json.loads(ans)
		
	except ValueError:
		print '\n\nNot Json\n\n'
		print ans
		print ''
		exit()
	
	return getJson

# assert keys match the expected values
def doAssert(key,expectKeys,actualVals,msg):

	keysList = list(expectKeys.items())
	valKeysList = list(actualVals.items())
	
	keysList.sort()
	valKeysList.sort()

	print ''
	
	if key == None:
		print 'Incorrect Size\n'
	else:
		print 'On Key: ' + str(key) + '\n'	
	
	print 'expected: ' + str(keysList) + '\n'
	print 'actual  : ' + str(valKeysList) + '\n'
	
	keys1 = expectKeys.keys()
	keys2 = actualVals.keys()
	
	keys1.sort()
	keys2.sort()
	
	print 'expected keys: ' + str(keys1) + '\n'
	print 'actual   keys: ' + str(keys2) + '\n'
	print 'failed ' + msg + '\n'
	exit()

def checkValsMain(expectKeyVals,actualVals,msg,isSub):

	for key in expectKeyVals:
		if key in expectKeyVals:
			
			if key not in actualVals:
				print '\nNot Found'
				doAssert(key,expectKeyVals,actualVals,msg)
				
			if expectKeyVals[key] != '<any>':
				
				if expectKeyVals[key] != actualVals[key]:
				
					check1 = isinstance(expectKeyVals[key],list)
					check2 = isinstance(actualVals[key],list)
					
					if isSub and check1 and check2:
						
						if len(expectKeyVals[key]) != len(actualVals[key]):
						
							print '\nDoes Not Match List Size'
							doAssert(key,expectKeyVals,actualVals,msg)
						
						for i in range(len(actualVals[key])):
							
							checkValsMain(expectKeyVals[key][i],actualVals[key][i],msg,isSub)
					
					else:
						print '\nIncorrect Value'
						doAssert(key,expectKeyVals,actualVals,msg)

def checkValsSub(expectKeyVals,actualVals,msg):

	checkValsMain(expectKeyVals,actualVals,msg,True)
	print 'passed: ' + msg

# expectKeyVals
def checkVals(expectKeyVals,actualVals,msg):

	checkValsMain(expectKeyVals,actualVals,msg,False)
				
	if len(expectKeyVals) != len(actualVals):
		doAssert(None,expectKeyVals,actualVals,msg)
	
	print 'passed: ' + msg
	