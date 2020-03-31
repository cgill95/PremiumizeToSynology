import json
import http.client
import csv

#Setup the Parameter of Premiumize and your NAS
params = open('params.csv', "r")
for line in params:
	line = line.split(',')
	if line[0] == 'synAccName':
		synAccName = line[1].rstrip()
	elif line[0] == 'synAccPw':
		synAccPw = line[1].rstrip()
	elif line[0] == 'synIpAddr':
		synIpAddr = line[1].rstrip()
	elif line[0] == 'premAccID':
		premAccID = line[1].rstrip()
	elif line[0] == 'premAccPw':
		premAccPw = line[1].rstrip()

deletions = True


#Connection Handling
def connection(webAddress, httpType, reqAdress):
	conn = http.client.HTTPConnection(webAddress)
	conn.request(httpType, reqAdress)
	r1 = conn.getresponse()
	data = r1.read()
	conn.close()
	return data

def sConnection(webAddress, httpType, reqAdress):
	conn = http.client.HTTPSConnection(webAddress)
	conn.request(httpType, reqAdress)
	r1 = conn.getresponse()
	data = r1.read()
	conn.close()
	return data

#Creation of Syno Requests
def createSynoRequest(path, api, version, method, param):
	return str("/webapi/"+path+"?api="+api+"&version="+version+"&method="+method+"&"+param)


# Step 1 GET API Information
apiInfoRequest = createSynoRequest("query.cgi", "SYNO.API.Info","1", "query", "query=SYNO.API.Auth")
synApiInfo = json.loads(connection(synIpAddr, "GET", apiInfoRequest))
print("Establishing Connection")


#Step 2 Session Login
API_NAME = "SYNO.API.Auth"
CGI_PATH = synApiInfo["data"][API_NAME]["path"]
VERSION = str(synApiInfo["data"][API_NAME]["maxVersion"])
METHOD = "login"
PARAMS = "account="+synAccName+"&passwd="+synAccPw+"&session=DownloadStation&format=cookie"
req = createSynoRequest(CGI_PATH, API_NAME,VERSION, METHOD, PARAMS)
sid = json.loads(connection(synIpAddr, "GET", req))["data"]["sid"]

apiDSTaskRequest = createSynoRequest("query.cgi", "SYNO.API.Info","1", "query", "query=SYNO.DownloadStation.Task")
synDownloadStationConnect = json.loads(connection(synIpAddr, "GET", apiDSTaskRequest))
print("Established Connection")

API_NAME = "SYNO.DownloadStation.Task"
CGI_PATH = synDownloadStationConnect["data"][API_NAME]["path"]
VERSION = str(synDownloadStationConnect["data"][API_NAME]["maxVersion"] -1 )
METHOD = "create"


#Warn for High Limit
premAccountInfo = json.loads(sConnection("www.premiumize.me","GET", "/api/account/info?customer_id="+premAccID+"&pin="+premAccPw))

if premAccountInfo["limit_used"] > 0.9:
	print("Download Limit is at 90%")
	#optionally exit if the limit is too high
	exit()

#Iterate through all Downloads
premTransferList = json.loads(sConnection("www.premiumize.me","GET", "/api/transfer/list?customer_id="+premAccID+"&pin="+premAccPw))

for key in premTransferList["transfers"]:
	if key["status"] == "finished":
		fileID = key["file_id"]
		if fileID == None:
			folderID = key["folder_id"]
			premFolderList = json.loads(sConnection("www.premiumize.me","GET", "/api/folder/list?id="+folderID+"&customer_id="+premAccID+"&pin="+premAccPw))
			content = premFolderList["content"]

			for item in content:
				if item["type"] == "file":
					link = item["link"]
					PARAMS = "uri="+link+"&_sid="+sid
					apiDownloadReq = createSynoRequest(CGI_PATH, API_NAME,VERSION, METHOD, PARAMS)
					connection(synIpAddr, "GET", apiDownloadReq)
				else:
					continue

		else:
			premFile = json.loads(sConnection("www.premiumize.me","GET", "/api/item/details?id="+fileID+"&customer_id="+premAccID+"&pin="+premAccPw))
			link = premFile["link"]

			PARAMS = "uri="+link+"&_sid="+sid
			apiDownloadReq = createSynoRequest(CGI_PATH, API_NAME,VERSION, METHOD, PARAMS)
			connection(synIpAddr, "GET", apiDownloadReq)
	
	else:
		continue

if deletions:
	sConnection("www.premiumize.me","POST", "/api/transfer/clearfinished?customer_id="+premAccID+"&pin="+premAccPw)

print("Logging out from "+synIpAddr)
apiLogout = createSynoRequest("auth.cgi", "SYNO.API.Auth","1", "logout", "session=DownloadStation")
data = connection(synIpAddr, "GET", apiLogout)
jsonTable = json.loads(data)
print("All Downloads transfered")