from twisted.internet import protocol, reactor, endpoints
from twisted.protocols.basic import LineReceiver
import logging
logging.basicConfig(level=logging.DEBUG)

class POP3Protocol(LineReceiver):
	def __init__(self):
		self.user=None
		self.auth=False
		
	def connectionMade(self):
		logging.info("Incoming pop3 connection")
		greeting="+OK mailsafe ready."
		self.sendLine(greeting.encode('utf8'))
		
	def lineReceived(self, line):
		parms=line.split()
		if len(parms)==0:
			logging.warn("Unknown command")
			self.sendLine("-ERR Unknown command.".encode('utf8'))
			return
		cmd=parms[0].decode('utf8','backslashreplace').upper()
		if self.auth:
			prefix="cmd_"
		else:
			prefix="auth_"
		f=getattr(self, prefix+cmd, None)
		if f==None:
			logging.warn("Unknown command '%s'",cmd)
			self.sendLine("-ERR Unknown command.".encode('utf8'))
			return
		logging.info("Received command '%s'",cmd)
		f(line)
		
	def auth_CAPA(self, line):
		self.sendLine("+OK".encode('utf8'))
		for c in ["TOP", "UIDL", "USER", "IMPLEMENTATION mailsafe"]:
			self.sendLine(c.encode('utf8'))
		self.sendLine(".".encode('utf8'))
		
	def auth_QUIT(self, line):
		greeting="+OK See you later alligator".encode('utf8')
		self.sendLine(greeting)
		self.transport.loseConnection()
		
	def auth_USER(self, line):
		try:
			usr=line.split()[1].decode('utf8','backslashreplace')
			self.user=usr
			greeting="+OK Now enter your password".encode('utf8')
			self.sendLine(greeting)
		except:
			err="-ERR I don't understand".encode('utf8')
			self.sendLine(err)
		
	def auth_PASS(self, line):
		if self.auth==None:
			err="-ERR USER first.".encode('utf8')
			self.sendLine(err)
			return
		try:
			pwd=line.split()[1]
			if self.db.validLogin(self.user, pwd):
				self.auth=True
				greeting="+OK You are now logged in".encode('utf8')
			else:
				greeting="-ERR user {} sus".format(self.user).encode('utf8')
			self.sendLine(greeting)
		except:
			err="-ERR I don't understand".encode('utf8')
			self.sendLine(err)
		
		
	def cmd_QUIT(self, line):
		greeting="+OK See you later alligator".encode('utf8')
		self.sendLine(greeting)
		self.transport.loseConnection()
		
	def cmd_NOOP(self, line):
		greeting="+OK".encode('utf8')
		self.sendLine(greeting)
		
	def cmd_RSET(self, line):
		greeting="+OK".encode('utf8')
		self.sendLine(greeting)
		
	def cmd_DELE(self, line):
		msg="-ERR Messages are permanent".encode('utf8')
		self.sendLine(msg)
		
	def cmd_STAT(self, line):
		msglist=self.db.listEmail(self.user)
		ttsize=0
		for i in msglist:
			ttsize+=i[1]
		statusLine="+OK {} {}".format(len(msglist),ttsize).encode('utf8')
		self.sendLine(statusLine)
		
	def cmd_RETR(self, line):
		try:
			msgnum=int(line.split()[1])
		except:
			self.sendLine("-ERR wrong".encode('utf8'))
			return
		msg=self.db.getEmail(self.user,msgnum)
		if msg==None:
			self.sendLine("-ERR not found".encode('utf8'))
		else:
			self.sendLine("+OK {} octets".format(len(msg)).encode('utf8'))
			for l in msg.split(b"\r\n"):
				self.sendLine(l)
		self.sendLine(".".encode('utf8'))
		
	def cmd_TOP(self, line):
		try:
			msgnum=int(line.split()[1])
			lines=int(line.split()[2])
		except:
			self.sendLine("-ERR wrong".encode('utf8'))
			return
		msg=self.db.getEmail(self.user,msgnum)
		if msg==None:
			self.sendLine("-ERR not found".encode('utf8'))
		else:
			self.sendLine("+OK {} octets".format(len(msg)).encode('utf8'))
			for i,l in enumerate(msg.split(b"\r\n")):
				if i>=lines:
					break
				self.sendLine(l)
		self.sendLine(".".encode('utf8'))
		
	def cmd_LIST(self, line):
		parms=line.split()
		if len(parms)>1:
			try:
				msgnum=int(parms[1])-1
			except:
				self.sendLine("-ERR wrong".encode('utf8'))
				return
		else:
			msgnum=None
		msglist=self.db.listEmail(self.user)
		ttsize=0
		for i in msglist:
			ttsize+=i[1]
		if msgnum==None:
			statusLine="+OK {} messages ({} octets)".format(len(msglist),ttsize).encode('utf8')
			self.sendLine(statusLine)
			i=0
			for m in msglist:
				i=i+1
				self.sendLine("{} {}".format(i,m[1]).encode('utf8'))
			self.sendLine(".".encode('utf8'))
		elif len(msglist)>msgnum and msgnum>0:
			self.sendLine("+OK {} {}".format(msgnum+1,msglist[msgnum][1]).encode('utf8'))
		else:
			self.sendLine("-ERR You what?".encode('utf8'))
		
	def cmd_UIDL(self, line):
		parms=line.split()
		if len(parms)>1:
			try:
				msgnum=int(parms[1])-1
			except:
				self.sendLine("-ERR wrong".encode('utf8'))
				return
		else:
			msgnum=None
		msglist=self.db.listEmail(self.user)
		if msgnum==None:
			self.sendLine("+OK".encode('utf8'))
			i=0
			for m in msglist:
				i=i+1
				self.sendLine("{} {}".format(i,m[0]).encode('utf8'))
			self.sendLine(".".encode('utf8'))
		elif len(msglist)>msgnum and msgnum>0:
			self.sendLine("+OK {} {}".format(msgnum+1,msglist[msgnum][0]).encode('utf8'))
		else:
			self.sendLine("-ERR You what?".encode('utf8'))
		

class POP3Factory(protocol.ServerFactory):
	protocol=POP3Protocol

	def __init__(self, db, *a, **kw):
		protocol.ServerFactory.__init__(self, *a, **kw)
		self.db=db
	
	def buildProtocol(self, addr):
		p = protocol.ServerFactory.buildProtocol(self, addr)
		p.db = self.db
		return p
