# https://djangosnippets.org/snippets/10332/
import xlwt
import datetime

from copy import deepcopy

from django.utils import timezone
from django.http import HttpResponseRedirect, HttpResponse

datetime.tzinfo = timezone.get_current_timezone()

from django.forms.forms import pretty_name
from django.core.exceptions import ObjectDoesNotExist

HEADER_STYLE = xlwt.easyxf('font: bold on')
DEFAULT_STYLE = xlwt.easyxf()
CELL_STYLE_MAP = (
    # (datetime.date, xlwt.easyxf(num_format_str='DD/MM/YYYY')),
    # (datetime.time, xlwt.easyxf(num_format_str='HH:MM')),
    # (datetime.datetime, xlwt.easyxf(num_format_str='DD/MM/YYYY HH:MM')),
    (bool, xlwt.easyxf(num_format_str='BOOLEAN')),
)


def download_workbook(queryset, columns, report_name='SK-Report'):
    workbook = queryset_to_workbook(queryset, columns)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="%s.xls"' % (report_name)
    workbook.save(response)
    return response

def multi_getattr(obj, attr, default=None):
    attributes = attr.split(".")
    for i in attributes:
        try:
            obj = getattr(obj, i)
        except AttributeError:
            if default:
                return default
            else:
                raise
    return obj

def get_column_head(obj, name):
    # name = name.rsplit('.', 1)[-1]
    if not name:
        return 'N/A'
    name = ' '.join(name.rsplit('.', 1))
    name = name.replace('_', ' ').title()
    return name
    # return pretty_name(name)

def get_column_cell(obj, name):
    try:
        attr = multi_getattr(obj, name)
    except ObjectDoesNotExist:
        return None
    if hasattr(attr, '_meta'):
        # A Django Model (related object)                                                                                                                                                                          
        return unicode(attr).strip()
    elif hasattr(attr, 'all'):
        # A Django queryset (ManyRelatedManager)                                                                                                                                                                   
        return ', '.join(unicode(x).strip() for x in attr.all())
    return attr

def queryset_to_workbook(queryset, columns, header_style=None,
                         default_style=None, cell_style_map=None):
    workbook = xlwt.Workbook()
    # add custom color:
    xlwt.add_palette_colour("light_red", 0x21)
    workbook.set_colour_RGB(0x21, 238, 144, 144)    

    report_date = datetime.date.today()
    # report_date = datetime.today()
    sheet_name = 'Export {0}'.format(report_date.strftime('%Y-%m-%d'))
    sheet = workbook.add_sheet(sheet_name)

    if not header_style:
        header_style = HEADER_STYLE
    if not default_style:
        default_style = DEFAULT_STYLE
    if not cell_style_map:
        cell_style_map = CELL_STYLE_MAP

    obj = queryset.first()
    for y, column in enumerate(columns):
        value = get_column_head(obj, column)
        sheet.write(0, y, value, header_style)

    for x, obj in enumerate(queryset, start=1):
        for y, column in enumerate(columns):            
            value = get_column_cell(obj, column)
            style = deepcopy(default_style)
            
            for value_type, cell_style in cell_style_map:                
                if isinstance(value, value_type):
                    style = cell_style_map

            if  xlwt.Style.colour_map.has_key(obj.servicekitstatus_xls_color):                
                style.pattern.pattern = xlwt.Pattern.SOLID_PATTERN
                style.pattern.pattern_fore_colour = xlwt.Style.colour_map[obj.servicekitstatus_xls_color ]
            
            if isinstance(value, datetime.datetime):
                value = value.strftime('%m/%d/%Y %I:%M %P')
            sheet.write(x, y, value, style)

    return workbook