import smtplib
import threading

from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address
# from django.core.mail.utils import DNS_NAME



class SEREmailBackend(BaseEmailBackend):
	host = ''
	port = 587
	username = ''
	password = ''
	use_tls = True 
	use_ssl = False
	fail_silently = False 

	def __init__(self, *args, **kwargs):
		self.connection = None
		self._lock = threading.RLock()
		super(SEREmailBackend, self).__init__(*args, **kwargs)

	def open(self, *args, **kwargs):
		"""
		Ensures we have a connection to the email server. Returns whether or
		not a new connection was required (True or False).
		"""
		if self.connection:
			# Nothing to do if the connection is already open.
			return False

		connection_class = smtplib.SMTP
		try:
			self.connection = connection_class(self.host, self.port)            
			if self.username and self.password:
				self.connection.login(self.username, self.password)
			return True
		except smtplib.SMTPException:
			if not self.fail_silently:
				raise

	def close(self, *args, **kwargs):
		"""Closes the connection to the email server."""
		if self.connection is None:
			return
		try:
			try:
				self.connection.quit()
			except (smtplib.SMTPServerDisconnected):
				self.connection.close()
			except smtplib.SMTPException:
				if self.fail_silently:
					return
				raise
		finally:
			self.connection = None

	def send_messages(self, email_messages):
		if not email_messages:
			return
		with self._lock:
			new_conn_created = self.open()
			if not self.connection:
				# We failed silently on open().
				# Trying to send would be pointless.
				return
			num_sent = 0
			for message in email_messages:
				sent = self._send(message)
				if sent:
					num_sent += 1
			if new_conn_created:
				self.close()
		return num_sent


	def _send(self, email_message):
		"""A helper method that does the actual sending."""
		if not email_message.recipients():
			return False
		
		from_email = sanitize_address(email_message.from_email, email_message.encoding)
		recipients = [sanitize_address(addr, email_message.encoding) for addr in email_message.recipients()]
		message = email_message.message()
		try:
			self.connection.sendmail(from_email, recipients, message.as_bytes(linesep='\r\n'))
		except smtplib.SMTPException:
			if not self.fail_silently:
				raise
			return False
		return True