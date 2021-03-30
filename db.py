import immudb.client
import time,string,random,re,crypt,logging

IMMUDB_USER="immudb"
IMMUDB_PASS="immudb"
IMMUDB_HOST="localhost"
IMMUDB_PORT="3322"

def rndstring(size):
	chars=string.ascii_uppercase + string.digits
	return ''.join(random.choice(chars) for _ in range(size))


class db:
	def __init__(self):
		self.cli=immudb.client.ImmudbClient("{}:{}".format(IMMUDB_HOST,IMMUDB_PORT))
		self.cli.login(IMMUDB_USER,IMMUDB_PASS)
		self.t=time.time()
		
	def _refresh(self):
		if time.time()-self.t>3000:
			self.cli.login(IMMUDB_USER,IMMUDB_PASS)
		
	def validUser(self, username):
		self._refresh()
		k="USER:{}".format(username).encode('utf8')
		try:
			u=self.cli.safeGet(k)
			return u.verified
		except:
			return False
		
	def validLogin(self, username, password):
		self._refresh()
		k="USER:{}".format(username).encode('utf8')
		try:
			u=self.cli.safeGet(k)
			pw=password.decode('utf8')
			val=u.value.decode('utf8')
			return u.verified and val==crypt.crypt(pw,val)
		except Exception as e:
			logging.exception(e)
			return False

	def storeEmail(self, username, message):
		self._refresh()
		uniq="{}.{}".format(time.time(), rndstring(8))
		k="MAIL:{}:{}:S{}".format(username, uniq,len(message))
		self.cli.safeSet(k.encode('utf8'), message)

	def listEmail(self, username):
		self._refresh()
		prefix="MAIL:{}:".format(username).encode('utf8')
		ret=[]
		prev=None
		rx=re.compile(r"MAIL:.*:(.+):S([0-9]+)")
		while True:
			sc=self.cli.scan(prev, prefix, False, 10)
			if len(sc)==0:
				break
			for i in sc.keys():
				prev=i
				m=rx.match(i.decode('utf8'))
				if m!=None:
					ret.append((m.group(1),int(m.group(2))))
		return ret

	def getEmail(self, username, idx):
		self._refresh()
		prefix="MAIL:{}:".format(username).encode('utf8')
		ret=[]
		prev=None
		rx=re.compile(r"MAIL:.*:(.+):S([0-9]+)")
		curr=0
		while True:
			sc=self.cli.scan(prev, prefix, False, 10)
			if len(sc)==0:
				break
			for i in sc.keys():
				curr+=1
				prev=i
				if curr==idx:
					return sc[i]
		return None
