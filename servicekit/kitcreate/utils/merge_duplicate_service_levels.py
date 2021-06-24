def fix_servicelevel(title):
	# "pl-Furn-Std Furn 253.50"
	levels = ServiceLevel.objects.filter(title=title)
	last = levels.last()
	forms = []

	for level in levels:
		for form in level.servicekitform_set.all():
			forms.append(form)

	last.servicekitform_set.add(*forms)
	last.save()

	to_be_deleted = levels.exclude(pk=last.pk)
	if to_be_deleted:
		return to_be_deleted
