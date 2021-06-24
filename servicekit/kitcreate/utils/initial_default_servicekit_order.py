default_order = [
 u'event_schedule',
 u'recap_of_services',
 u'third_party_auth_billing',
 u'STD_FURN_99',
 u'STD_FURN_118',
 u'STD_FURN_124',
 u'STD_FURN_129.8',
 u'STD_FURN_159',
 u'STD_FURN_180',
 u'STD_FURN_185',
 u'STD_FURN_212',
 u'booth_equipment_special',
 u'modular_rental',
 u'graphics',
 u'gridwall',
 u'computer_kiosk',
 u'LED_LIGHTS_118',
 u'LED_LIGHTS_124',
 u'LED_LIGHTS_129.8',
 u'LED_LIGHTS_159',
 u'LED_LIGHTS_180',
 u'LED_LIGHTS_185',
 u'LED_LIGHTS_212',
 u'LED_LIGHTS_99',
 u'showcases',
 u'MH_131',
 u'MH_137',
 u'MH_69',
 u'MH_72',
 u'MH_74',
 u'MH_85',
 u'MH_91',
 u'MH_ADV_ONLY_131',
 u'MH_ADV_ONLY_137',
 u'MH_ADV_ONLY_69',
 u'MH_ADV_ONLY_72',
 u'MH_ADV_ONLY_74',
 u'MH_ADV_ONLY_85',
 u'MH_ADV_ONLY_91',
 u'booth_labor_75',
 u'booth_labor_80',
 u'booth_labor_85',
 u'booth_labor_125',
 u'booth_labor_152',
 u'booth_labor_204.75',
 u'forklift_125',
 u'forklift_152',
 u'forklift_75',
 u'forklift_80',
 u'forklift_85',
 u'forklift_204.75',
 u'porter_125',
 u'porter_152',
 u'porter_75',
 u'porter_80',
 u'porter_85',
 u'porter_204.75',
 u'banner_hanging',
 u'booth_cleaning',
 u'non_official_service_contractor'
]

def set_order(servicekit):
	def _sort(x):
		# default_servicekit_order ServiceKit doesn't contain user upload forms
		# give them an unnasseary big index so they should up at hte end.
		if x.title in default_order:
			return default_order.index(x.title)
		else:
			return len(default_order) + 100
	result = sorted(servicekit.forms.all(), key=_sort)	
	servicekit.forms = result
	return servicekit




