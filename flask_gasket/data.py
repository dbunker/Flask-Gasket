# this stores data and runs queries on Riak

import time, datetime, uuid, json
import control
import riak

# server value is always same being pulled and being set

class RiakConn():
	
	def __init__(self,allModels):
	
		# keys show above
		self.connDB = None
		self.models = allModels
	
	def _setupDatabase(self):
	
		if self.connDB == None:
			# connect to riak and pick bucket to store data in.
			self.connDB = riak.RiakClient(port=8087, transport_class=riak.RiakPbcTransport)
		
		return self.connDB

	def _createDict(self,obj,keyName=None,serverDef=None):
		
		data = obj.get_data()
		ind = obj.get_indexes()
		
		allInd = {}
		for v in ind:
			
			# remove _bin
			key = v.get_field()[:-4]
			value = v.get_value()
			
			# uppercase
			for otherkey in serverDef['_data']:
				if otherkey.lower() == key:
					key = otherkey
					break
			
			# for multi index
			if serverDef['_data'][key]['_server'] == '_index_multi':	
				allInd[key] = allInd.get(key,[]) + [value]
				
			else:
				allInd[key] = value
		
		fullDict = dict(allInd.items() + data.items())
		if keyName != None:
			fullDict[keyName] = obj.get_key()
		return fullDict

	def _isUniqueIndex(self,bucketName,index,val):
		
		db = self._setupDatabase()
		query = db.index(bucketName, index+'_bin', val)
		results = query.run()
		
		if len(results) == 0:
			return True
		
		return False
	
	# ex. create follow with userToID = userID
	# add to user with userID: numFollowers
	def _checkChangeList(self,all,serverDef,processList,changeVal):
		
		for serverKey in serverDef['_data']:
			serverDefVal = serverDef['_data'][serverKey]
			
			# consider _index_multi
			if '_server' in serverDefVal and '_index' == serverDefVal['_server']:
				
				if '_counter_model_name' in serverDefVal:
					
					counterSet = serverDefVal['_counter_model_name']
					
					# ex. userID = comment.userToID
					primaryKey = all[serverKey]
					
					# must not be set
					if primaryKey == '':
						continue
					
					(counterModel,counterName) = counterSet
					
					# ex. got user primary key from follow
					modelVal = processList.get((serverKey,primaryKey,counterModel),{})
					processList[(serverKey,primaryKey,counterModel)] = modelVal
					
					counterNameVal = modelVal.get(counterName,0)
					modelVal[counterName] = counterNameVal + changeVal
					
		return processList
	
	# first create a list of all the changes that would be made to each list size
	# then make these changes assuming their are changes to be made
	def _execProc(self,procList,serverDef):
	
		for modelValKey in procList:
			(serverKey,primaryKey,counterModel) = modelValKey
			modelVal = procList[modelValKey]
			
			for counterName in modelVal:
			
				changeVal = modelVal[counterName]
				
				if changeVal != 0:
				
					counterServerDef = self.models[counterModel]['_server']
					resultKeys = self._internalGetPrimary(primaryKey,counterServerDef)
				
					if resultKeys == None:
						continue
				
					fullList = self.getSecondary(serverKey,primaryKey,serverDef)
				
					resultKeys[counterName] = len(fullList)
					self._internalUpdate(primaryKey,resultKeys,counterServerDef)
	
	def _checkAddList(self,all,serverDef):
		procList = {}
		self._checkChangeList(all,serverDef,procList,1)
		self._execProc(procList,serverDef)
		
	def _checkDelList(self,all,serverDef):
	
		procList = {}
		self._checkChangeList(all,serverDef,procList,-1)
		self._execProc(procList,serverDef)
	
	def _checkUpdateList(self,curVals,oldVals,serverDef):
		
		procList = {}
		self._checkChangeList(oldVals,serverDef,procList,-1)
		self._checkChangeList(curVals,serverDef,procList,1)
		self._execProc(procList,serverDef)
	
	def _storeData(self,bucketID,overKey,recv,toServer,serverDef,isUpdate=False,oldVals=None):
		
		mainKeyName = None
		mainKey = overKey
		valsToSet = dict(recv.items() + toServer.items())
		
		newIndexes = []
		newData = {}
		
		# current time
		now = round(time.time(),3)
		
		uniqueKeys = {}
		
		for serverKey in serverDef['_data']:
			serverDefVal = serverDef['_data'][serverKey]
			type = serverDefVal['_type']
			newVal = None
			
			if type == '_primary':
				mainKeyName = serverKey
			
			# if not set, _counter values set to 0
			elif type == '_counter' or type == '_counter_list':
				if serverKey in valsToSet:
					newVal = valsToSet[serverKey]
				else:
					newVal = 0
			
			# check if data has _created type, set this value
			elif type == '_created':
				if isUpdate:
					newVal = valsToSet[serverKey]
				else:
					newVal = now
			
			elif type == '_updated':
				newVal = now
			
			else:
			
				if serverKey in valsToSet:
					newVal = valsToSet[serverKey]
				else:
					if '_default' in serverDefVal:
						newVal = serverDefVal['_default']
					elif '_optional' in serverDefVal:
						continue
					else:
						print valsToSet
						print str(serverKey) + ' not in valsToSet'
						assert(False)
			
			# set the value
			
			if '_index_multi' == serverDefVal['_server']:
				
				for elem in newVal:
					newIndexes.append((serverKey+'_bin',elem))
			
			elif '_index' == serverDefVal['_server']:
				newIndexes.append((serverKey+'_bin',newVal))
			
			elif '_value' == serverDefVal['_server']:
				newData[serverKey] = newVal
			
			if '_unique' in serverDefVal:
				uniqueKeys[serverKey] = newVal
		
		if (bucketID == None):
			print 'bad bucketID'
			assert(False)
			
		if (mainKey == None):
			print 'bad mainKey'
			assert(False)
		
		# check that indexes set to _unique are unique
		# this maters only when first being created,
		# or if one of the unique values has changed
		if not isUpdate or oldVals != None:
			for key in uniqueKeys:
				val = uniqueKeys[key]
				
				# skip checking this value if it is unchanged
				if oldVals != None:
					oldVal = oldVals[key]
					if oldVal == val:
						continue
				
				isUnique = self._isUniqueIndex(bucketID,key,val)
				if not isUnique:
					return control.valTaken(key)
		
		# set values and indexes
		db = self._setupDatabase()
		bucket = db.bucket(bucketID)
		
		obj = bucket.new(mainKey)
		obj.set_data(newData)
		
		obj.set_indexes(newIndexes)
		obj.store()
		
		ret = self._createDict(obj,mainKeyName,serverDef)
		return ret
	
	def _getMainKey(self,serverDef):
	
		mainKeyName = None
		for key in serverDef['_data']:
			if serverDef['_data'][key]['_type'] == '_primary':
				mainKeyName = key
				
		return mainKeyName
	
	def create(self,overKey,recv,toServer,serverDef):
		
		bucketID = serverDef['_container']
		
		if overKey == None:
			overKey = uuid.uuid4().hex
		
		ret = self._storeData(bucketID,overKey,recv,toServer,serverDef)
		
		# if this is part of a list, add it
		all = ret
		self._checkAddList(all,serverDef)
		
		return ret
	
	def _internalGetPrimary(self,key,serverDef):
		
		bucketID = serverDef['_container']
		
		mainKeyName = self._getMainKey(serverDef)
		
		db = self._setupDatabase()
		bucket = db.bucket(bucketID)
		
		obj = bucket.get(key)
		if obj == None or obj.get_data() == None:
			return None
		
		fullDict = self._createDict(obj,mainKeyName,serverDef=serverDef)
		fromServer = fullDict
		
		return fromServer
	
	# conflict resolution
	# caching
	def getPrimary(self,key,serverDef):
		
		bucketID = serverDef['_container']
		
		mainKeyName = self._getMainKey(serverDef)
		
		db = self._setupDatabase()
		bucket = db.bucket(bucketID)
		
		obj = bucket.get(key)
		if obj == None or obj.get_data() == None:
			return None
		
		fullDict = self._createDict(obj,mainKeyName,serverDef=serverDef)
		fromServer = fullDict
		
		return fromServer
	
	def _internalGetRange(self,indexKey,indexStart,indexEnd,serverDef):
		
		bucketID = serverDef['_container']
		
		mainKeyName = self._getMainKey(serverDef)
		
		db = self._setupDatabase()
		results = None
		buck = db.bucket(bucketID)
		
		if indexStart == indexEnd:
			results = buck.get_index(indexKey + '_bin', indexStart)
		else:
			results = buck.get_index(indexKey + '_bin', indexStart, indexEnd)
		
		# map reduce
		# results = query.run()
		
		objRes = []
		for curKey in results:
			
			obj = buck.get(curKey)
			if obj.get_data() == None:
				continue
			
			res = self._createDict(obj,mainKeyName,serverDef=serverDef)
			objRes.append(res)
		
		return objRes
	
	def getSecondary(self,indexKey,indexVal,serverDef):

		objRes = self._internalGetRange(indexKey,indexVal,indexVal,serverDef)
		return objRes
	
	def getRange(self,indexKey,indexStart,indexEnd,serverDef):
		
		objRes = self._internalGetRange(indexKey,indexStart,indexEnd,serverDef)
		return objRes
	
	def _internalUpdate(self,overKey,toServer,serverDef):
	
		bucketID = serverDef['_container']
		ret = self._storeData(bucketID,overKey,{},toServer,serverDef,isUpdate=True)
		return ret
	
	# _counter
	def update(self,overKey,recv,toServer,serverDef,oldVals=None):
		
		bucketID = serverDef['_container']
		
		if oldVals == None:
			oldVals = self._internalGetPrimary(overKey,serverDef)
		
		ret = self._storeData(bucketID,overKey,recv,toServer,serverDef,isUpdate=True,oldVals=oldVals)
		
		self._checkUpdateList(ret,oldVals,serverDef)
		
		return ret
	
	def delete(self,key,serverDef):
	
		bucketID = serverDef['_container']
	
		# delete by primary key
		db = self._setupDatabase()
		bucket = db.bucket(bucketID)
		obj = bucket.get(key)
		
		all = self._createDict(obj,key,serverDef)
		ret = obj.delete()
		
		# if this is part of a list, remove it
		self._checkDelList(all,serverDef)
		
		return ret

# recursively goes through lists
def _matchSingleSend(subDict,sendDefData):
	
	# can confirm types
	send = {}
	
	for sendKey in sendDefData:
		
		sendVal = sendDefData[sendKey]
		
		def getRes(sendKey):
			return subDict[sendKey]
		
		if sendVal['_type'] == '_created' or sendVal['_type'] == '_updated' or sendVal['_type'] == '_datetime':
			
			def getRes(sendKey):
				
				val = subDict[sendKey]
				sendTime = datetime.datetime.utcfromtimestamp(val).isoformat()
				sendTime = sendTime[:-3] + 'Z'
				return sendTime
		
		if sendKey in subDict:
			send[sendKey] = getRes(sendKey)
		
		elif '_default' in sendVal:
			send[sendKey] = sendVal['_default']
		
		# debug
		# if not present, but not optional, this is an internal error
		elif '_optional' not in sendVal:
			print subDict
			print 'does not have ' + str(sendKey)
			assert(False)
	
	return send
	
def matchSend(full,sendDef):
	
	if 'isList' in sendDef:
	
		sendList = []
		thisList = full['list']
		
		for val in thisList:
			newVal = _matchSingleSend(val,sendDef['_data']['list'])
			sendList.append(newVal)
		
		send = { 'list':sendList }
	
	else:
		send = _matchSingleSend(full,sendDef['_data'])
	
	return send

def matchRecv(full,recvDef,recUrl):

	actualVals = full
	expectKeys = recvDef['_data']

	recv = {}
	
	for key in expectKeys:
		if not key in actualVals:
			
			if '_optional' in expectKeys[key]:
				continue
			else:
				return (False,control.invalidJsonKey(key))
		else:
			recv[key] = actualVals[key]
	
	for key in recUrl:
		recv[key] = recUrl[key]
	
	return (True,recv)
