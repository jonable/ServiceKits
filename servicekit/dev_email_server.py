import os
import asyncore
from datetime import datetime
from smtpd import SMTPServer

# This is a simple email server for debugging purposes
# 
# Client
# 
# import smtplib
# import email.utils
# from email.mime.text import MIMEText

# # Create the message
# msg = MIMEText('This is the body of the message.')
# msg['To'] = email.utils.formataddr(('Recipient', 'recipient@example.com'))
# msg['From'] = email.utils.formataddr(('Author', 'author@example.com'))
# msg['Subject'] = 'Simple test message'

# server = smtplib.SMTP(server_addr)
# server.set_debuglevel(True) # show communication with the server
# try:
#     server.sendmail('author@example.com', ['recipient@example.com'], msg.as_string())
# finally:
#     server.quit()

server_addr = ('0.0.0.0', 8989)
output_path = os.path.abspath('./uploads/emsl/')
class EmlServer(SMTPServer):
	no = 0
	def process_message(self, peer, mailfrom, rcpttos, data):
		filename = '%s-%d.eml' % (datetime.now().strftime('%Y%m%d%H%M%S'), self.no)
		filepath = os.path.join(output_path, filename)
		f = open(filepath, 'w')
		f.write(data)
		f.close
		print '%s saved.' % filepath
		self.no += 1


def run():
	foo = EmlServer(server_addr, None)
	try:
		asyncore.loop()
	except KeyboardInterrupt:
		pass


if __name__ == '__main__':
	run()