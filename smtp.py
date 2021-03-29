from twisted.internet import protocol, reactor, endpoints, defer
from twisted.mail import smtp
from zope.interface import implementer
from twisted.internet import defer
import datetime
import time
from email import utils
from email.header import Header
import logging
import db

@implementer(smtp.IMessageDelivery)
class ImmudbMessageDelivery:
	def __init__(self, db):
		self.db=db
		
	def receivedHeader(self, helo, origin, rcpt):
		recv="from {hello0} [{hello1}] message to {rcpts}; {date}"
		rcpts=",".join([str(r.dest) for r in rcpt])
		date = utils.format_datetime(datetime.datetime.now())
		hh=Header("Received")
		hh.append(recv.format(hello0=helo[0].decode('ascii'),
		     hello1=helo[1].decode('ascii'),
		     rcpts=rcpts, date=date).encode('ascii'))
		return hh.encode().encode('ascii')

	def validateFrom(self, helo, origin):
		logging.info("validating from %s",origin)
		# All addresses are accepted
		return origin

	def validateTo(self, user):
		# Only messages directed to configured users are accepted
		logging.info("validating to %s",user)
		if self.db.validUser(user.dest):
			logging.info("ok")
			return lambda: ImmudbMessage(self.db, user.dest)
		raise smtp.SMTPBadRcpt(user)

@implementer(smtp.IMessage)
class ImmudbMessage:
	def __init__(self, db, rcpt):
		self.msg = b''
		self.db=db
		self.rcpt=str(rcpt)

	def lineReceived(self, line):
		self.msg+=line+b"\r\n"

	def eomReceived(self):
		logging.info("New message received for %s",self.rcpt)
		self.db.storeEmail(self.rcpt, self.msg)
		self.lines = None
		return defer.succeed(None)

	def connectionLost(self):
		# There was an error, throw away the stored lines
		self.lines = None


class SMTPProtocol(smtp.ESMTP):
	def connectionMade(self):
		logging.info("smtp connection")
		smtp.ESMTP.connectionMade(self)

class SMTPFactory(protocol.ServerFactory):
	protocol=SMTPProtocol
	domain="lazzaris.net"
	def __init__(self, db, *a, **kw):
		smtp.SMTPFactory.__init__(self, *a, **kw)
		self.delivery=ImmudbMessageDelivery(db)
	
	def buildProtocol(self, addr):
		p = smtp.SMTPFactory.buildProtocol(self, addr)
		p.delivery = self.delivery
		return p
