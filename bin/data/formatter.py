
from util.logger import error, warning
import values as v
from datetime import date

keys = ['.', '@']

def format_date_tuple(p_date):
    try:
        d = date.fromisoformat(p_date)
        return (d.strftime('%Y'), d.strftime('%m'), d.strftime('%d'))
    except ValueError:
        error('DATE RECEIVED NOT IN ISO8601 FORMAT!!! RECEIVED: ' + p_date)
        return ('1776', '07', '04')

def format_gender(gender):
    try: gender = gender.lower()
    except AttributeError: warning('Gender detected in STI csv is not a string...?')
    box = v.chk_gender_x

    if gender == v.g_m: box = v.chk_gender_m
    elif gender == v.g_f: box = v.chk_gender_f
    return (box, v.pdf_check)

def format_phone_tuple(phone):
    stripped = phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
    if len(stripped) != 10:
        warning('Improper phone number: ' + phone + ' (if there\'s nothing to my left, the phone number was blank!)')
        return ('999', '999', '9999')
    return (stripped[:3], stripped[3:6], stripped[6:])

def format_phone_display(phone):
    if '-' in phone: return phone
    return phone[:3] + '-' + phone[3:6] + '-' + phone[6:]

# TODO consider using py3-validate-email
def is_email(target): return all(key in target for key in keys)

# TODO needs to be updated eventually
def translate_result(result_code):
    result = None
    match result_code:
        case str(v.res_neg): result = v.d_sti_neg
        case str(v.res_equ): result = v.d_equ
        case str(v.res_pos): result = v.d_sti_pos
        case _:
            if '^' in result_code and ':' in result_code:
                return result_code.replace('^', '')
            warning('Could not translate result: ' + result_code)
            return result_code
    return result
