from twisted.internet import protocol, reactor, endpoints
import logging
import smtp
import pop3
import db

logging.basicConfig(level=logging.DEBUG)
immudb=db.db()

smtp_endpoint=endpoints.serverFromString(reactor,"tcp:7125")
pop3_endpoint=endpoints.serverFromString(reactor,"tcp:7110")

smtp_endpoint.listen(smtp.SMTPFactory(immudb))
pop3_endpoint.listen(pop3.POP3Factory(immudb))

reactor.run()
