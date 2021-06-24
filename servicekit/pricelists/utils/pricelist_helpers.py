import sys, os
sys.path.append("/Users/jonathannable 1/Projects/utilities/")
from collections import OrderedDict
from copy import deepcopy
from csv_to_xls import open_workbook, xls_to_dict, dict_to_xls, dict_to_xls2, xlsbook_to_dict

BASE_DIR = os.path.abspath('./')
LABOR_PRICELIST_DIR = os.path.join(BASE_DIR, 'LABOR')
LABOR_SERVICES = ['BOOTHLABOR', 'CLEANING', 'FORKLIFT', 'PORTER']
LABOR_RATES = os.path.join(BASE_DIR, 'data', 'labor_rates_2018.xls')


MH_RATES = os.path.join(BASE_DIR, 'data', 'mh_rates_2018.xls')

FURN_PRICELIST_DIR = os.path.join(BASE_DIR, 'FURN')
# FURN_RATES = os.path.join(BASE_DIR, 'data', 'std_furn_prices_2018.xls')
FURN_RATES = os.path.join(BASE_DIR, 'data', 'std_furn_prices_2018.xls')
FURN_MAP = os.path.join(BASE_DIR, 'data', 'std_furn_map.xlsx')

BASE_RATE_FILENAME = 'base.xls'

def get_pricelist_xls():
    results = []
    dir_list = os.listdir(BASE_DIR)
    for item in dir_list:
        if '.xls' in item:
            results.append(os.path.join(BASE_DIR, item))
    return results


def get_pricelist_as_dict(file_name):
    workbook = open_workbook(file_name)
    sheet = workbook.sheet_by_index(0)
    return xls_to_dict(sheet)

def get_wb_as_dict(file_name):
    workbook = open_workbook(file_name)
    return xlsbook_to_dict(workbook)

def create_mh_pricelists(path_to_base_pl):
    MH_PL_DIR = os.path.dirname(path_to_base_pl)
    product_percent_map = {
        'adv_rate':{
            "MH10-E": 1.00, #Adv Created/Skidded
            "MH20-E": 1.30, #Adv Special
        },
        'dir_rate':{
            "MH30-E": 1.00, #Dir Created/Skidded
            "MH40-E": 1.30, #Dir Created/Skidded
            "MH50-E": 1.00,
        }
    }
    _price_cols = ["Default Advance Price","Default Standard Price\n"]
    pricelist = get_pricelist_as_dict(path_to_base_pl)
    rates = get_pricelist_as_dict(MH_RATES)
    new_rates = [76,80,94,144,82,100,150,174,168,178,44,]

    for rate in rates:
        result = []
        for product in pricelist:            
            product_id = product.get('Product ID')            
            
            if product_id in product_percent_map['adv_rate']:
                _rate = rate['adv_rate'] * product_percent_map['adv_rate'].get(product_id)
                for _col in _price_cols:
                    product[_col] = _rate                     
            if product_id in product_percent_map['dir_rate']:
                _rate = rate['dir_rate'] * product_percent_map['dir_rate'].get(product_id)
                for _col in _price_cols:
                    product[_col] = _rate
            result.append(product)          
        new_workbook = dict_to_xls2({'Default': make_supplier_pl(result)})
        file_name = "%s-%s" % (int(rate['adv_rate']), int(rate['dir_rate']))
        if rate['adv_rate'] in new_rates:
            file_name = "2018-%s" % (file_name)
        new_workbook.save(os.path.join(MH_PL_DIR, "%s-rate.xls" % (file_name)))


def create_labor_pricelists(path_to_base_pl):
    LABOR_PL_DIR = os.path.dirname(path_to_base_pl)
    product_percent_map = {
        'rate': {
            "L10": 1.00, # Instsall Labor
            "L20": 1.00, # Dismantle
            "L50": 1.00, # Forklift in
            "L60": 1.00, # Forklift out
            "L70": 1.00, # porter
        },
    }
    _price_cols = ["Default Advance Price", "Default Standard Price\n"]
    pricelist = get_pricelist_as_dict(path_to_base_pl)
    rates = get_pricelist_as_dict(LABOR_RATES)
    old_rate = [75,80,85,152,125,180.25,204.75,98]
    new_rates = [82,88,94,168,138,198,225,108,]
    for rate in rates:
        result = []
        for product in pricelist:
            product_id = product.get('Product ID')

            if product_id in product_percent_map['rate']:
                _rate = rate['rate'] * product_percent_map['rate'].get(product_id)
                product["Default Advance Price"] = _rate
                product["Default Standard Price\n"] = _rate * 1.30

            result.append(product)
        new_workbook = dict_to_xls2({'Default': make_supplier_pl(result)})
        file_name = int(rate['rate'])
        if rate['rate'] in new_rates:
            file_name = "2018-%s" % file_name
        new_workbook.save(os.path.join(LABOR_PL_DIR, "%s-rate.xls" % (file_name)))

def bulk_create_labor_pricelists():
    for _labor_service in LABOR_SERVICES:
        service_base_pricelist = os.path.join(LABOR_PRICELIST_DIR, _labor_service, BASE_RATE_FILENAME)
        if os.path.exists(service_base_pricelist):
            create_labor_pricelists(service_base_pricelist)

def create_furn_pricelist():
    item_map = get_pricelist_as_dict(FURN_MAP)
    template = get_pricelist_as_dict(os.path.join('FURN', BASE_RATE_FILENAME))
    pricelists = get_wb_as_dict(FURN_RATES)

    # map the old std_furn_prices items to boomer product_id    
    for pl_name, pricelist in pricelists.items():
        for item in pricelist:
            item['product_id'] = ''
            for _map in item_map:
                if item.get('Item') == _map.get('Item'):
                    item['product_id'] = _map.get('product_id')

        result = []
        # merge the old prices with the boomer template
        for item in pricelist:
            for row in template:
                # import ipdb; ipdb.set_trace()
                if item.get('product_id') == row.get('Product ID'):
                    row['Default Advance Price'] = item.get('Advance')
                    row['Default Standard Price\n'] = item.get('Regular')
                    result.append(row)
        new_workbook = dict_to_xls2({'Default': make_supplier_pl(result)})
        new_workbook.save(os.path.join(FURN_PRICELIST_DIR, "%s-rate.xls" % pl_name))
        # merge nicole's new prices with the boomer template
        result = []        
        for item in pricelist:
            if not item.get('Advanced 2018') and not item.get('Regular 2018'):
                break
            for row in template:
                if item.get('product_id') == row.get('Product ID'):
                    row['Default Advance Price'] = item.get('Advanced 2018')
                    row['Default Standard Price\n'] = item.get('Regular 2018')
                    result.append(row)
            new_workbook = dict_to_xls2({'Default': make_supplier_pl(result)})
            new_workbook.save(os.path.join(FURN_PRICELIST_DIR, "2018-%s-rate.xls" % pl_name))

def make_supplier_pl(data):
    # import ipdb; ipdb.set_trace()
    field_map = [
        ("Product ID", "Product ID"),
        ("Item Name", "Item Name\n"),
        ("Published to Store", "Auto Publish to Storefront"),
        ("Published to Admin", "Auto Publish in Admin"),
        ("Advance Price", "Default Advance Price"),
        ("Standard Price", "Default Standard Price\n"),
    ]
    default_items = [
        ("Advanced Split Type", "", "Amount"),
        ("Advanced Split Amount", "", "0.00"),
        ("Standard Split Type","","Amount"),
        ("Standard Split Amount", "", "0.00"),
    ]
    results = []
    for item in data:
        obj = OrderedDict()
        for _field in field_map:
            obj[_field[0]] = None
            if item.get(_field[1]):
                obj[_field[0]] = item.get(_field[1])
        for _default_item in default_items:
            obj[_default_item[0]] = _default_item[2]  
        results.append(obj)

    return results

def convert_product_export_to_pricelist(excel_path):
    result = xls_to_dict(open_workbook(excel_path).sheet_by_index(0))
    new_workbook = dict_to_xls2({'Default': make_supplier_pl(result)})
    new_workbook.save(os.path.join(BASE_DIR, "pricelist_export.xls"))

def main():
    create_furn_pricelist()

if __name__ == '__main__':
    main()


# forms = [
# 	["MH - Adv 40 Dir 36", "MH/40-36-rate.xls"],
# 	["MH - Adv 69 Dir 65", "MH/69-65-rate.xls"],
# 	["MH - Adv 72 Dir 69", "MH/72-69-rate.xls"],
# 	["MH - Adv 74 Dir 71", "MH/74-71-rate.xls"],
# 	["MH - Adv 75 Dir 72", "MH/75-72-rate.xls"],
# 	["MH - Adv 75 Dir 75", "MH/75-75-rate.xls"],
# 	["MH - Adv 85 Dir 82", "MH/85-82-rate.xls"],
# 	["MH - Adv 91 Dir 88", "MH/91-88-rate.xls"],
# 	["MH - Adv 131 Dir 125", "MH/131-125-rate.xls"],
# 	["MH - Adv 137 Dir 131", "MH/137-131-rate.xls"],
# 	["MH - Adv 152 Dir 152", "MH/152-152-rate.xls"],
# 	["MH - Adv 157 Dir 157", "MH/157-157-rate.xls"],
# 	["MH - Adv 161 Dir 177", "MH/161-177-rate.xls"],
# 	["MH - Adv 44 Dir 40", "MH/2018-44-40-rate.xls"],
# 	["MH - Adv 76 Dir 72", "MH/2018-76-72-rate.xls"],
# 	["MH - Adv 80 Dir 76", "MH/2018-80-76-rate.xls"],
# 	["MH - Adv 82 Dir 78", "MH/2018-82-78-rate.xls"],
# 	["MH - Adv 94 Dir 90", "MH/2018-94-90-rate.xls"],
# 	["MH - Adv 100 Dir 97-", "MH/2018-100-97-rate.xls"],
# 	["MH - Adv 144 Dir 138", "MH/2018-144-138-rate.xls"],
# 	["MH - Adv 150 Dir 144", "MH/2018-150-144-rate.xls"],
# 	["MH - Adv 168 Dir 168", "MH/2018-168-168-rate.xls"],
# 	["MH - Adv 174 Dir 174", "MH/2018-174-174-rate.xls"],
# 	["MH - Adv 178 Dir 195", "MH/2018-178-195-rate.xls"],
# 	["Labor - Booth Labor 75", "LABOR/BOOTHLABOR/75-rate.xls"],
# 	["Labor - Booth Labor 80", "LABOR/BOOTHLABOR/80-rate.xls"],
# 	["Labor - Booth Labor 85", "LABOR/BOOTHLABOR/85-rate.xls"],
# 	["Labor - Booth Labor 98", "LABOR/BOOTHLABOR/98-rate.xls"],
# 	["Labor - Booth Labor 125", "LABOR/BOOTHLABOR/125-rate.xls"],
# 	["Labor - Booth Labor 152", "LABOR/BOOTHLABOR/152-rate.xls"],
# 	["Labor - Booth Labor 180", "LABOR/BOOTHLABOR/180-rate.xls"],
# 	["Labor - Booth Labor 204", "LABOR/BOOTHLABOR/204-rate.xls"],
# 	["Labor - Booth Labor 82", "LABOR/BOOTHLABOR/2018-82-rate.xls"],
# 	["Labor - Booth Labor 88", "LABOR/BOOTHLABOR/2018-88-rate.xls"],
# 	["Labor - Booth Labor 94", "LABOR/BOOTHLABOR/2018-94-rate.xls"],
# 	["Labor - Booth Labor 108", "LABOR/BOOTHLABOR/2018-108-rate.xls"],
# 	["Labor - Booth Labor 138", "LABOR/BOOTHLABOR/2018-138-rate.xls"],
# 	["Labor - Booth Labor 168", "LABOR/BOOTHLABOR/2018-168-rate.xls"],
# 	["Labor - Booth Labor 198", "LABOR/BOOTHLABOR/2018-198-rate.xls"],
# 	["Labor - Booth Labor 225", "LABOR/BOOTHLABOR/2018-225-rate.xls"],
# 	["Labor - Forklift 75", "LABOR/FORKLIFT/75-rate.xls"],
# 	["Labor - Forklift 80", "LABOR/FORKLIFT/80-rate.xls"],
# 	["Labor - Forklift 85", "LABOR/FORKLIFT/85-rate.xls"],
# 	["Labor - Forklift 98", "LABOR/FORKLIFT/98-rate.xls"],
# 	["Labor - Forklift 125", "LABOR/FORKLIFT/125-rate.xls"],
# 	["Labor - Forklift 152", "LABOR/FORKLIFT/152-rate.xls"],
# 	["Labor - Forklift 180", "LABOR/FORKLIFT/180-rate.xls"],
# 	["Labor - Forklift 204", "LABOR/FORKLIFT/204-rate.xls"],
# 	["Labor - Forklift 82", "LABOR/FORKLIFT/2018-82-rate.xls"],
# 	["Labor - Forklift 88", "LABOR/FORKLIFT/2018-88-rate.xls"],
# 	["Labor - Forklift 94", "LABOR/FORKLIFT/2018-94-rate.xls"],
# 	["Labor - Forklift 108", "LABOR/FORKLIFT/2018-108-rate.xls"],
# 	["Labor - Forklift 138", "LABOR/FORKLIFT/2018-138-rate.xls"],
# 	["Labor - Forklift 168", "LABOR/FORKLIFT/2018-168-rate.xls"],
# 	["Labor - Forklift 198", "LABOR/FORKLIFT/2018-198-rate.xls"],
# 	["Labor - Forklift 225", "LABOR/FORKLIFT/2018-225-rate.xls"],
# 	["Labor - Porter 75", "LABOR/PORTER/75-rate.xls"],
# 	["Labor - Porter 80", "LABOR/PORTER/80-rate.xls"],
# 	["Labor - Porter 85", "LABOR/PORTER/85-rate.xls"],
# 	["Labor - Porter 98", "LABOR/PORTER/98-rate.xls"],
# 	["Labor - Porter 125", "LABOR/PORTER/125-rate.xls"],
# 	["Labor - Porter 152", "LABOR/PORTER/152-rate.xls"],
# 	["Labor - Porter 180", "LABOR/PORTER/180-rate.xls"],
# 	["Labor - Porter 204", "LABOR/PORTER/204-rate.xls"],
# 	["Labor - Porter 82", "LABOR/PORTER/2018-82-rate.xls"],
# 	["Labor - Porter 88", "LABOR/PORTER/2018-88-rate.xls"],
# 	["Labor - Porter 94", "LABOR/PORTER/2018-94-rate.xls"],
# 	["Labor - Porter 108", "LABOR/PORTER/2018-108-rate.xls"],
# 	["Labor - Porter 138", "LABOR/PORTER/2018-138-rate.xls"],
# 	["Labor - Porter 168", "LABOR/PORTER/2018-168-rate.xls"],
# 	["Labor - Porter 198", "LABOR/PORTER/2018-198-rate.xls"],
# 	["Labor - Porter 225", "LABOR/PORTER/2018-225-rate.xls"],
# ]
# BASE_DIR = os.path.abspath('/ Users/jonathannable 1/OneDrive - SER Exposition Services/Projects/boomer/pricelists')
# for form in forms:
# 	pricelist = Pricelist.objects.create(title=form[0])
# 	workbook = open_workbook(os.path.join(BASE_DIR, form[1]))
# 	sheet = workbook.sheet_by_index(0)
# 	data = xls_to_dict(sheet)
# 	price_tier = "Default"
# 	derp = process_import(data, pricelist, price_tier)
