from filebrowser.base import FileObject

furniture = [
	["booth_equipment_special", "booth_equipment_special.docx"],
	["computer_kiosk_form", "computer_kiosk_form.docx"],
	["counters_form", "counters_form.docx"],
	["floral_form", "floral_form.docx"],
	["gondola_form", "gondola_form.docx"],
	["graphic_form", "graphic_form.docx"],
	["gridwall_form", "gridwall_form.docx"],
	["led_light_form", "led_light_form.docx"],
	["modular_rental_form", "modular_rental_form.docx"],
	["pegboard_form", "pegboard_form.docx"],
	["premium", "premium-graphic_form.docx"],
	["showcase_form", "showcase_form.docx"],
	["std_furn_form", "std_furn_form.docx"],
	["tent_form", "tent_form.docx"],
]

labor = [
 ["banner_hanging_form", "banner_hanging_form.docx"],
 ["booth_cleaning_form", "booth_cleaning_form.docx"],
 ["booth_labor_form", "booth_labor_form.docx"],
 ["forklift_form", "forklift_form.docx"],
 ["non_official_service_contractor", "non_official_service_contractor.docx"],
 ["porter_form", "porter_form.docx"],
]

mh = [
    ["material_handling_adv_only_form", "material_handling_adv_only_form.docx"],
    ["material_handling_form", "material_handling_form.docx"]
]

def bulk_create_formtemplate(forms, directory, service_type)
for form in forms:
    furn_dir = directory
    if FormTemplate.objects.filter(template__icontains=form[1]) and os.path.exists(os.path.join(furn_dir, form[1])):
        print(form[1])
        continue
    file_obj = FileObject(os.path.join(furn_dir, form[1]))
    title = form[0]
    FormTemplate.objects.create(
        title=title, template=file_obj, service_type=service_type)
