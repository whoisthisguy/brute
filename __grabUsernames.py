import sys, random, re
from threading import Thread
from grab import Grab, GrabError
from Queue import Queue
reload(sys)
sys.setdefaultencoding("utf-8")
# Define some globals
# 
indexArray = [0,1,6,7,12,13,18,19,24,25,30,31,36,37,42,43,48,49,54,55]
postsAndUsername = []
usersOnPage = []
outputFile = 'dump_last.lst'
plFile = 'proxy.lst'
savedProxy = ''
useProxy = False
changeProxyText = u'url(http://zismo.ru/plan_ru/error404.jpeg)'
g = Grab()
g.setup(hammer_mode=False)
g.setup(headers={'Connection': 'Keep-Alive'})
connectTimeout = 2
timeout = 5
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

# Get posts and Username
def getPostsAndUsername(index, node):
        global postsAndUsername 

        if index in indexArray:
                postsAndUsername.append(node.text_content())
                if len(postsAndUsername) == 2:
                        if int(postsAndUsername[0]) > 10 and ' **' not in postsAndUsername[1]: #not in postsAndUsername[1]:
                                oFile = open(outputFile, 'a')
                                oFile.write(removeSpaces(postsAndUsername[1])+'\n')
                                oFile.close()
                        # clear 
                        postsAndUsername[:] = []
        
def grb(page):
        proxyForRequest = getAproxy(pl)
        if useProxy:
                g.setup(proxy=proxyForRequest, proxy_type='http', connect_timeout=connectTimeout, timeout=timeout)               
        try:
                g.go('http://zismo.biz/index/15-'+str(page))
                if g.search(changeProxyText):
                        removeBad(pl, proxyForRequest)
                        grbAgain(page)
                else: 
                        usersNode = g.pyquery('table.uTable td.uTd')
                        usersNode.each(getPostsAndUsername)
                        saveProxy(proxyForRequest)

        except GrabError:
                removeBad(pl, proxyForRequest)
                print '>>> Error'
                grbAgain(page)

def grbAgain(page):
        saveProxy(getNext(pl))
        useProxy = True
        grb(page)


# Main function              
pl = loadFile(plFile)
for page in xrange(8201, 12588):#12588):
        grb(page)
        print '>>> '+ str(page)