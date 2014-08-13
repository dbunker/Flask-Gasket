import json, uuid, time, datetime
import base64, hmac, hashlib
import smtplib

# uuid.uuid4().hex
picPass = '<random key>'

myUrl = 'http://localhost:5600/'
myUrl = '<my host url>'

# amazon s3
s3bucket = '<s3 bucket>'
s3url = 'https://' + s3bucket + '.s3.amazonaws.com/'

AWS_SECRET_ACCESS_KEY = '<s3 secret key>'
AWSAccessKeyId = '<s3 access key>'

SES_USERNAME = '<ses username>'
SES_PASSWORD = '<ses password>'

# Example Curl
# curl -XPOST \
# -F key=avatar/2451352745-8f334hf094.jpg \
# -F AWSAccessKeyId=1ASWBD1BD8FX3PFXT6G2 \
# -F acl=public-read \
# -F success_action_redirect=http://localhost/ \
# -F policy=eyJleHBpcmF0aW9uIjogIjIwMTQtMDEtMDFUMDA9MDA6MDBaIiwKICAiY29uZGl0aW9ucyI6IFsgCiAgICB7ImJ1Y2tldCI6ICJwaGFzZTcifSwgCiAgICBbInN0YXJ0cy13aXRoIiwgIiRrZXkiLCAiYXZhdGFyLzhmOTM0aGYwOTQuanBnIl0sCiAgICB7ImFjbCI6ICJwdWJsaWMtcmVhZCJ9LAogICAgeyJzdWNjZXNzX2FjdGlvbl9yZWRpcmVjdCI6ICJodHRwOi8vbG9jYWxob3N0LyJ9LAogICAgWyJzdGFydHMtd2l0aCIsICIkQ29udGVudC1UeXBlIiwgIiJdLAogICAgWyJjb250ZW50LWxlbmd0aC1yYW5nZSIsIDAsIDEwNDg1NzZdCiAgXQp9 \
# -F signature=kabmsOW4ufZsS9A2FEBkO391OcU= \
# -F Content-Type=image/jpeg \
# -F file=@test.jpg \
# https://mys3bucket.s3.amazonaws.com/

def _awsPic(key):
	
	# given 10 minutes
	now = time.time()
	expire = now + 60 * 60
	
	expireDate = datetime.datetime.utcfromtimestamp(expire).isoformat()
	expireDate = expireDate[:-7] + 'Z'
	
	# for starts: "starts-with"
	# for exact match: "eq"
	
	redirect = myUrl + 'api/pic/' + key
	
	# .jpg added to pickkey
	# 2014-01-01T00:00:00Z
	policy_document = '''{"expiration": "''' + expireDate + '''",
	  "conditions": [ 
		{"bucket": "''' + s3bucket + '''"}, 
		["eq", "$key", "''' + key + '''"],
		{"acl": "public-read"},
		{"success_action_redirect": "''' + redirect + '''"},
		["eq", "$Content-Type", "image/jpeg"],
		["content-length-range", 0, 1048576]
	  ]
	}'''
	
	policy = base64.b64encode(policy_document)
	signature = base64.b64encode(hmac.new(AWS_SECRET_ACCESS_KEY, policy, hashlib.sha1).digest())
	
	return (policy,signature,redirect)

def makePic(folder,setid):
	
	mainKey = folder + '/' + setid
	
	picKey = mainKey + '.jpg'
	(picPolicy,picSignature,picRedirect) = _awsPic(picKey)
	picUpload = s3url
	picDownload = s3url + picKey
	
	thumbKey = mainKey + '-thumb.jpg'
	(thumbPolicy,thumbSignature,thumbRedirect) = _awsPic(thumbKey)
	thumbUpload = s3url
	thumbDownload = s3url + thumbKey
	
	midKey = mainKey + '-mid.jpg'
	(midPolicy,midSignature,midRedirect) = _awsPic(midKey)
	midUpload = s3url
	midDownload = s3url + midKey
	
	coreKey = mainKey + hashlib.sha256(mainKey + picPass).hexdigest()
	
	returnJson = {
		'AWSAccessKeyId':AWSAccessKeyId,
		'acl':'public-read',
		'Content-Type':'image/jpeg',
		'coreKey':coreKey,
		
		'picKey':picKey,
		'picRedirect':picRedirect,
		'picUpload':picUpload,
		'picPolicy':picPolicy,
		'picSignature':picSignature,
		'picDownload':picDownload,
		
		'thumbKey':thumbKey,
		'thumbRedirect':thumbRedirect,
		'thumbUpload':thumbUpload,
		'thumbPolicy':thumbPolicy,
		'thumbSignature':thumbSignature,
		'thumbDownload':thumbDownload,
		
		'midKey':midKey,
		'midRedirect':midRedirect,
		'midUpload':midUpload,
		'midPolicy':midPolicy,
		'midSignature':midSignature,
		'midDownload':midDownload,
	}
	
	return returnJson

# confirms that a coreKey was made in makePic, and returns the associated ID
def getCoreID(folder,coreKey):
	
	startID = len(folder)+1
	endID = startID+32
	
	if coreKey[:startID-1] != folder:
		return None
	
	testKey = coreKey[:endID]
	testCore = testKey + hashlib.sha256(testKey + picPass).hexdigest()
	
	if testCore != coreKey:
		return None
	
	retID = coreKey[startID:endID]
	return retID

def sendEmail(fromAddr,toAddr,subject,sendMsg):

	fromaddr = fromAddr
	toaddrs  = toAddr

	msg = '''From: ''' + fromAddr + '''
	To: ''' + toAddr + '''
	Subject: ''' + subject + '''
	MIME-Version: 1.0
	Content-type: text/html

	''' + sendMsg
	
	#Change according to your settings
	smtp_server = 'email-smtp.us-east-1.amazonaws.com'
	smtp_username = SES_USERNAME
	smtp_password = SES_PASSWORD
	smtp_port = '587'
	smtp_do_tls = True

	server = smtplib.SMTP(
		host = smtp_server,
		port = smtp_port,
		timeout = 10
	)

	server.starttls()
	server.ehlo()

	server.login(smtp_username, smtp_password)
	server.sendmail(fromaddr, toaddrs, msg)
