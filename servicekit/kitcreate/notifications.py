"""
Helper function to handle sending notifications
"""
from django.template import loader
from django.contrib.auth.models import User
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
# Use this module to send notifications.
# Could use some additional refactoring or maybe some abstraction
# like using a model to describe the functions so things can be configured outside this script
# 
# from django.contrib.auth.models import User, Group
# class NotificationGroup(models.Model):
# 	group    = models.ForeignKey('django.auth.Group')
# 	template = models.CharField(max_length=255, blank=True, null=True)
# 	subject  = models.CharField(max_length=255, blank=True, null=True)
# 	STATUS   = Choices('draft', 'review', 'approved', 'published', 'expired')
# 	status   = StatusField()
# 	active   = models.BooleanField(default=False)


# from django.template.loader import render_to_string
# from django.template import Template, Context
# class Notification(object):
# 	title = models.CharField(max_length=255, blank=True, null=True)
# 	group = models.ForeignKey('Group', related_name=notifications)
# 	subject = models.CharField(max_length=255, blank=True, null=True)
# 	message = models.CharField(max_length=255, blank=True, null=True)
	
# 	def get_notify_group(self):	
# 		users = self.group.users.distinct()
# 		if not users:
# 			raise Exception('No users setup for group %s.' % self.group)
# 		return [x.email for x in User.objects.filter(groups__name=group_name)]

# 	def render_message(self, context):		
# 		message = loader.render_to_string(self.template, context)
# 		return message

# 	def render_subject(self, context):
# 		t = Template(self.subject)
# 		c = Context(context)
# 		subject = t.render(c)
# 		return subject

# 	def send(self):
# 		emails = self.get_notify_group()
# 		subject = self.render_subject(context)
# 		message = self.render_message(context)
# 		return email_notification(subject, message, emails)

def get_notify_group(group_name):
	if type(group_name) == list:
		users = User.objects.filter(groups__name__in=group_name).distinct()
	else:
		users = User.objects.filter(groups__name=group_name)
	if not users:
		raise Exception('No users setup for group %s.' % group_name)
	return [x.email for x in User.objects.filter(groups__name=group_name)]
	
def email_notification(subject, message, to):
	from_email = settings.DEFAULT_FROM_EMAIL
	text_content = message
	html_content = message
	msg = EmailMultiAlternatives(subject, text_content, from_email, to)
	msg.attach_alternative(html_content, "text/html")
	return msg.send()

def notification_generic(eventinfo, subject, message, to, context=None):
	# message arg is not used
	context = context or {}
	context.update({'object':eventinfo})
	template_name = "%s-%s" % (context.get('status_type', 'default') or 'default', context.get('status', 'default') or 'default')
	message = loader.render_to_string(
		['kitcreate/emails/%s.html' % (template_name), 
		'kitcreate/emails/status-generic.html'], context)
	if email_notification(subject, message, to):
		return to
	return []

def notification_draft(eventinfo):
	to_email_addresses = get_notify_group('EventCoordinators')
	subject = 'Kit Status Changed for %s' % (eventinfo.event_name)
	message = loader.render_to_string('kitcreate/emails/status-draft.html', {'object':eventinfo})
	if email_notification(subject, message, to_email_addresses):
		return to_email_addresses
	return []

def notification_review(eventinfo):
	to_email_addresses = get_notify_group('EventCoordinators')
	subject = 'Kit Status Changed for %s' % (eventinfo.event_name)
	message = loader.render_to_string('kitcreate/emails/status-review.html', {'object':eventinfo})
	if email_notification(subject, message, to_email_addresses):
		return to_email_addresses
	return []

def notification_approved(eventinfo):
	to_email_addresses = get_notify_group('EventCoordinators')
	subject = 'Kit Status Changed for %s' % (eventinfo.event_name)
	message = loader.render_to_string('kitcreate/emails/status-approved.html', {'object':eventinfo})
	if email_notification(subject, message, to_email_addresses):
		return to_email_addresses
	return [] 

def notification_published(eventinfo):
	to_email_addresses = get_notify_group('EventCoordinators')
	subject = 'Kit Status Changed for %s' % (eventinfo.event_name)
	message = loader.render_to_string('kitcreate/emails/status-published.html', {'object':eventinfo})
	if email_notification(subject, message, to_email_addresses):
		return to_email_addresses
	return []	

def notification_expired(eventinfo):

	to_email_addresses = [settings.DEFAULT_FROM_EMAIL]
	subject = 'Kit Status Changed for %s' % (eventinfo.event_name)
	message = loader.render_to_string('kitcreate/emails/status-expired.html', {'object':eventinfo})
	if email_notification(subject, message, to_email_addresses):
		return to_email_addresses
	return []


def notification_pending(eventinfo):
	return [settings.DEFAULT_FROM_EMAIL]
	
def create_status_notification(eventinfo, status):
	mapping = {
		"pending": notification_pending,
		"draft": notification_draft,
		"review": notification_review,
		"approved": notification_approved,
		"published": notification_published,
		"expired": notification_expired,
	}
	if mapping.has_key(status):
		return mapping[status](eventinfo)
	else:
		raise Exception('No status notification setup for %s' % status)
		return False

def create_storefrontstatus_notification(eventinfo, status):
	to_email_addresses = get_notify_group('CustomerService')
	subject = '%s Storefront Status' % (eventinfo.event_name)
	message = loader.render_to_string('kitcreate/emails/storefrontstatus-generic.html', {'object':eventinfo, 'status':status})
	if email_notification(subject, message, to_email_addresses):
		return to_email_addresses
	return [] 

