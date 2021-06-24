
# ServiceKitField.objects.filter(form__in=[x.pk for x in eventinfo.service_kit.forms.all()]).distinct()
# eventinfo.service_kit.forms.filter(form_field__isnull=False)

# forms_with_fields = []
# # find all the servicekitforms in the kit with extra fields
# for form in eventinfo.service_kit.forms.filter(form_field__isnull=False).distinct():
# 	forms_with_fields.append(form)
# # create a form to fill in the values and save them
from django import forms
class DynamicForm(forms.Form):
	def __init__(self, model_instance=None, *args, **kwargs):
		self.model_instance = model_instance
		super(DynamicForm, self).__init__(*args, **kwargs)
		if self.model_instance:
			self.add_the_fields()

	def add_the_fields(self, *args, **kwargs):
		for field in self.model_instance.form_fields.all().order_by('title'):
			self.fields[field.title] = forms.CharField(
				label=field.title, 
				required=False, 
			)

from .models import ServiceKitFieldValue, ServiceKitField


class ServiceKitAdditionalFormValues(DynamicForm):	
	def __init__(self, servicekit, model_instance=None, *args, **kwargs):

		self.servicekit = servicekit
		super(ServiceKitAdditionalFormValues, self).__init__(model_instance=model_instance, *args, **kwargs)

	def save_values(self):
		results = []
		
		for key, value in self.cleaned_data.items():
			servicekitfield = self.model_instance.form_fields.filter(title=key).first()
			
			if not servicekitfield:
				continue
			
			servicekitfieldvalue, created = ServiceKitFieldValue.objects.get_or_create(
				field=servicekitfield, 
				kit=self.servicekit, 
			)
			if not value:
				servicekitfieldvalue.delete()
				continue

			servicekitfieldvalue.value = value
			servicekitfieldvalue.save()
			results.append(servicekitfieldvalue.pk)
		return results

	def add_the_fields(self, *args, **kwargs):
		for field in self.model_instance.form_fields.all().order_by('title'):
			value = None
			servicekitfieldvalue = ServiceKitFieldValue.objects.filter(field__title=field.title, kit=self.servicekit).first()			

			if servicekitfieldvalue and servicekitfieldvalue.value:
				value = servicekitfieldvalue.value

			self.fields[field.title] = forms.CharField(
				# label=field.label, 
				required=field.required,
				help_text=field.help_text,
				initial=value
			)



class ServiceKitFieldValueForm(forms.Form):	
	def __init__(self, servicekitforms, servicekit=None, *args, **kwargs):
		super(ServiceKitFieldValueForm, self).__init__(*args,**kwargs)

		self._fieldsets = []
		self.servicekit = servicekit
		self.servicekitforms = servicekitforms
		for servicekitform in self.servicekitforms:
			_fields = []
			for servicekitfield in servicekitform.form_fields.all().order_by('title'):
				value = None
				servicekitfieldvalue = ServiceKitFieldValue.objects.filter(field__title=servicekitfield.title, kit=self.servicekit).first()			

				if servicekitfieldvalue and servicekitfieldvalue.value:
					value = servicekitfieldvalue.value				

				field_title = "%s-%s" % (servicekitform.pk, servicekitfield.title)
				self.fields[field_title] = forms.CharField(
					label=servicekitfield.label, 
					required=False,
					initial=value
					# prefix=servicekitform.title
				)
				self.fields[field_title].servicekitfield_pk = servicekitfield.pk
				self.fields[field_title].servicekitform_pk = servicekitform.pk
				_fields.append(field_title)
			
			self._fieldsets.append(({
				"key": servicekitform.pk, 
				"title": servicekitform.title, 
				"fields": _fields
			}))

	def has_fieldsets(self):
		return True

	def fieldsets(self):
		results = []
		for fieldset in self._fieldsets:
			title = fieldset.get('title')
			fields = [self[x] for x in fieldset.get('fields')]
			results.append({
				"title": title,
				"fields": fields
			})
		return results

	def save_values(self, servicekit):
		results = []
		for key, value in self.cleaned_data.items():
			_pk = self.fields[key].servicekitfield_pk			
			servicekitfield = ServiceKitField.objects.filter(pk=_pk).first()
			if not servicekitfield:
				continue
			servicekitfieldvalue, created = ServiceKitFieldValue.objects.get_or_create(
				field=servicekitfield, 
				kit=servicekit, 
			)
			if not value:
				servicekitfieldvalue.delete()
				continue
			servicekitfieldvalue.value = value
			servicekitfieldvalue.save()
			results.append(servicekitfieldvalue.pk)
		return results
		
	# def save_values(self):
	# 	results = []
		
	# 	for key, value in self.cleaned_data.items():
	# 		servicekitfield = self.model_instance.form_fields.filter(title=key).first()
			
	# 		if not servicekitfield:
	# 			continue
			
	# 		servicekitfieldvalue, created = ServiceKitFieldValue.objects.get_or_create(
	# 			field=servicekitfield, 
	# 			kit=self.servicekit, 
	# 		)
	# 		if not value:
	# 			servicekitfieldvalue.delete()
	# 			continue

	# 		servicekitfieldvalue.value = value
	# 		servicekitfieldvalue.save()
	# 		results.append(servicekitfieldvalue.pk)
	# 	return results

	# def add_the_fields(self, *args, **kwargs):
	# 	for field in self.model_instance.form_fields.all().order_by('title'):
	# 		value = None
	# 		servicekitfieldvalue = ServiceKitFieldValue.objects.filter(field__title=field.title, kit=self.servicekit).first()			

	# 		if servicekitfieldvalue and servicekitfieldvalue.value:
	# 			value = servicekitfieldvalue.value

	# 		self.fields[field.title] = forms.CharField(
	# 			# label=field.label, 
	# 			required=field.required,
	# 			help_text=field.help_text,
	# 			initial=value 
	# 		)



	# def get_servicekitforms_pks(self):
	# 	# if not valid, fail?
	# 	pks = []
	# 	for key, value in self.cleaned_data.items():
	# 		if value:
	# 			pks.append(self.fields[key]._servicekitform_pk)
	# 	return pks

	# def get_servicekitforms(self):
	# 	return ServiceKitForm.objects.filter(pk__in=self.get_servicekitforms_pks())		

	# def has_fieldsets(self):
	# 	return True

	# def fieldsets(self):
	# 	results = []
	# 	for fieldset in self._fieldsets:
	# 		title = fieldset.get('title')
	# 		fields = [self[x] for x in fieldset.get('fields')]
	# 		results.append({
	# 			"title": title,
	# 			"fields": fields
	# 		})
	# 	return results