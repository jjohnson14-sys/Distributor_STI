
import values as v
import logging
from os import remove
from os.path import exists

errors, warnings = [], []
none = ['None! :)']

def pal(string):
    if not v.dev: print(string)
    logging.info(string)

def warning(*message):
    s = ''
    for m in message:
        logging.warning(m)
        s += m + '\n'
    warnings.append(s)

def error(*message):
    s = ''
    for m in message:
        logging.error(m)
        s += str(m) + '\n'
    errors.append(s)

def cleanup():
    if exists(v.path_errs):
        remove(v.path_errs)
        logging.info('Deleted ' + v.path_errs + '.')
    if exists(v.path_warns):
        remove(v.path_warns)
        logging.info('Deleted ' + v.path_warns + '.')

    logging.info('Finished operations with ' + str(len(errors)) + ' errors and ' + str(len(warnings)) + ' warnings.')

def get_errors():
    if len(errors) < 1: return none
    return errors
def get_warnings():
    if len(warnings) < 1: return none
    return warnings
