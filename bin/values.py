
import util.hidden as h

import configparser
from datetime import datetime as dt
import logging
from os import getcwd, mkdir
from os.path import exists, join
import sys

from alive_progress import config_handler as alive_cfg

stamp = dt.today().strftime('%Y%m%d_%I%M%p')

log_name = 'sti-distributor'
dir_log = 'logs'
cwd = getcwd()
path_logs = join(cwd, dir_log)
log_name = log_name + ' ' + stamp + '.log'
path_run_log = join(path_logs, log_name)
if not exists(path_logs): mkdir(path_logs)
logging.basicConfig(filename=path_run_log, encoding='utf-8', level=logging.INFO)

file_cfg = 'settings.ini'
path_cfg = join(cwd, file_cfg)
cfg = configparser.ConfigParser()
logging.info('Reading settings from ' + path_cfg + '...')
try: cfg.read(path_cfg) # TODO rework to download default ini if missing?
except Exception as e:
    for arg in e.args: logging.error(arg)
    logging.error('CANNOT READ ' + file_cfg + '!!!')
    raise

alive_cfg.set_global(bar='classic', spinner='classic')

DEFAULT = 'DEFAULT'
DIRECTORY = 'DIRECTORY'
ENGINE = 'ENGINE'
STI = 'STI'
DEV = 'DEV'

dev = cfg.getboolean(DEV, 'dev', fallback=False)
track = cfg.getboolean(DEV, 'track', fallback=True)
summary = cfg.getboolean(DEV, 'summary', fallback=True)

# ========== DEFAULT ==========
d_usbtl_submitter = cfg.get(DEFAULT, 'submitter_name', fallback=h.default_submitter)
outbound_email = cfg.get(DEFAULT, 'outbound_email', fallback=h.outbound_email)
if not dev:
    submitter = input('Please input your name: ').title()
    logging.info('Submitter name: ' + submitter)
    print('Submitter name: ' + submitter)
    if submitter != '' and submitter is not None: d_usbtl_submitter = submitter
else:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)

d_usbtl_name = cfg.get(DEFAULT, 'lab_name', fallback=h.lab_name)
d_usbtl_street = cfg.get(DEFAULT, 'lab_street', fallback=h.lab_street)
d_usbtl_city = cfg.get(DEFAULT, 'lab_city', fallback=h.lab_city)
d_usbtl_st = cfg.get(DEFAULT, 'lab_state', fallback=h.lab_state)
d_usbtl_zip = cfg.get(DEFAULT, 'lab_zip', fallback=h.lab_zip)
d_usbtl_county = cfg.get(DEFAULT, 'lab_county', fallback=h.lab_county)
d_usbtl_phone = cfg.get(DEFAULT, 'lab_phone', fallback=h.lab_phone)

max_errors = int(cfg.get(DEFAULT, 'max_errors', fallback=5))
max_retries = int(cfg.get(DEFAULT, 'max_retries', fallback=5))
pdf_generic_max_entries = int(cfg.get(DEFAULT, 'pdf_generic_max_entries', fallback=3))
pdf_avg = int(cfg.get(DEFAULT, 'pdf_avg', fallback=15))

send_cmd = cfg.get(DEFAULT, 'send_cmd', fallback='send')
start_delay = int(cfg.get(DEFAULT, 'start_delay', fallback=5))
dry_toggle = cfg.getboolean(DEFAULT, 'dry_run', fallback=True)
distro_list = cfg.get(DEFAULT, 'summary_email_list', fallback=h.dev_email)
omitted_states = cfg.get(DEFAULT, 'omitted_states', fallback='')
omitted_states = omitted_states.replace(' ', '').split(',')

# ========== DIRECTORY ==========
dir_archive = cfg.get(DIRECTORY, 'archive', fallback='archive')
dir_doh = cfg.get(DIRECTORY, 'dir_doh_csvs', fallback='G:\LIS\DOH')
path_tracker = cfg.get(DIRECTORY, 'path_tracker', fallback=h.path_tracker)

# ========== ENGINE ==========
sti_tuple_size = int(cfg.get(ENGINE, 'sti_tuple_size', fallback=13))
i_device = int(cfg.get(ENGINE, 'i_csv_device', fallback=29))
i_markttl = int(cfg.get(ENGINE, 'i_csv_markttl', fallback=30))
i_spl = int(cfg.get(ENGINE, 'i_csv_spl_type', fallback=31))
i_result = int(cfg.get(ENGINE, 'i_csv_result', fallback=32))

file_rules_state = cfg.get(ENGINE, 'file_rules_states', fallback='rules_states.xlsx')
file_rules_prac = cfg.get(ENGINE, 'file_rules_prac', fallback='rules_prac.xlsx')
file_map_sample_types = cfg.get(ENGINE, 'file_map_sample_types', fallback='map_sample_types.xlsx')
file_map_sti = cfg.get(ENGINE, 'file_map_sti', fallback='map_sti.xlsx')

map_st_col_code = cfg.get(ENGINE, 'map_st_col_code', fallback='A')
map_st_col_label = cfg.get(ENGINE, 'map_st_col_label', fallback='B')
map_st_col_name = cfg.get(ENGINE, 'map_st_col_name', fallback='C')
map_st_col_display = cfg.get(ENGINE, 'map_st_col_display', fallback='D')
map_st_col_form = cfg.get(ENGINE, 'map_st_col_form', fallback='E')

rules_col_county = cfg.get(ENGINE, 'rules_col_county', fallback='A') # also state col for city sheet
rules_col_sti = cfg.get(ENGINE, 'rules_col_sti', fallback='B')
rules_col_doh_target = cfg.get(ENGINE, 'rules_col_doh_target', fallback='C')
rules_col_template = cfg.get(ENGINE, 'rules_col_template', fallback='D')
rules_col_reports_per = cfg.get(ENGINE, 'rules_col_reports_per', fallback='E')
rules_col_city = cfg.get(ENGINE, 'rules_col_city', fallback='F')

rules_prac_col_field = cfg.get(ENGINE, 'rules_prac_col_field', fallback='A')
rules_prac_col_ovrd = cfg.get(ENGINE, 'rules_prac_col_override', fallback='B')

map_sti_col_name = cfg.get(ENGINE, 'map_sti_col_name', fallback='D')
map_sti_col_code = cfg.get(ENGINE, 'map_sti_col_code', fallback='C')
map_sti_col_device = cfg.get(ENGINE, 'map_sti_col_device', fallback='A')
map_sti_map = cfg.get(ENGINE, 'map_sti_map', fallback='STI')
map_sti_generic = cfg.get(ENGINE, 'map_sti_generic', fallback='Generic')
map_sti_g_code = cfg.get(ENGINE, 'map_sti_g_code', fallback='A')
map_sti_g_name = cfg.get(ENGINE, 'map_sti_g_name', fallback='B')

flag_all = cfg.get(ENGINE, 'flag_all', fallback='ALL')
flag_blank = cfg.get(ENGINE, 'flag_blank', fallback='BLANK')
flag_one = cfg.get(ENGINE, 'flag_one', fallback='ONE')
flag_each = cfg.get(ENGINE, 'flag_each', fallback='EACH')
flag_marker = cfg.get(ENGINE, 'flag_marker', fallback='MARKER')
flag_manual = cfg.get(ENGINE, 'flag_manual', fallback='MANUAL')
flag_other = cfg.get(ENGINE, 'flag_other', fallback='OTHER')

sheet_city = cfg.get(ENGINE, 'sheet_city', fallback='Cities')

# ========== STI ==========
d_sti_pos = cfg.get(STI, 'd_positive', fallback='Positive')
d_sti_neg = cfg.get(STI, 'd_negative', fallback='Negative')
d_equ = cfg.get(STI, 'd_equ', fallback='Equivocal')
d_equ_pcr = cfg.get(STI, 'd_equ_pcr', fallback='Inconclusive')

res_neg = cfg.get(STI, 'res_neg', fallback=0)
res_equ = cfg.get(STI, 'res_equ', fallback=1)
res_pos = cfg.get(STI, 'res_pos', fallback=2)

code_hep = cfg.get(STI, 'code_hep', fallback='HEP')
code_syph = cfg.get(STI, 'code_syph', fallback='SYPH')
code_hiv = cfg.get(STI, 'code_hiv', fallback='HIV')

# ========== PDF ==========
g_f, g_m = 'f', 'm'

dt_order = 'dt_order'
dt_run = 'dt_run'
doh_state = 'doh_state'
order_id = 'order_id'

pt_fn = 'pt_fn'
pt_ln = 'pt_ln'
pt_name = 'pt_name'
pt_dob = 'pt_dob'
pt_dob_y = 'pt_dob_y'
pt_dob_m = 'pt_dob_m'
pt_dob_d = 'pt_dob_d'
pt_age = 'pt_age'
pt_phone = 'pt_phone'
pt_phone_area = 'pt_phone_area'
pt_phone_exch = 'pt_phone_exch'
pt_phone_line = 'pt_phone_line'
pt_addr = 'pt_addr'
pt_city = 'pt_city'
pt_st = 'pt_st'
pt_zip = 'pt_zip'
pt_county = 'pt_county'
pt_race = 'pt_race'
pt_ethnicity = 'pt_ethnicity'
pt_gender = 'pt_gender'
chk_gender_f = 'chk_gender_f'
chk_gender_m = 'chk_gender_m'
chk_gender_x = 'chk_gender_x'
pt_orientation = 'pt_orientation'
pt_pregnant = 'pt_pregnant'

prac_name = 'prac_name'
prc_fn = 'prc_fn'
prc_ln = 'prc_ln'
prc_clinic = 'prc_clinic'
loc_phone = 'loc_phone'
loc_addr1 = 'loc_addr1'
loc_addr2 = 'loc_addr2'
loc_city = 'loc_city'
loc_st = 'loc_st'
loc_zip = 'loc_zip'
prc_addr = 'prc_addr'

loc_collected_name = 'loc_collected_name'
loc_collected_addr = 'loc_collected_addr'
loc_collected_city = 'loc_collected_city'
loc_collected_phone = 'loc_collected_phone'

dt_collected = 'dt_collected'
dt_today = 'dt_today'
dt_report_generated = 'dt_report_generated'

lab_phone = 'lab_phone'
usbtl_name = 'usbtl_name'
usbtl_submitter = 'usbtl_submitter'
usbtl_street = 'usbtl_street'
usbtl_city = 'usbtl_city'
usbtl_st = 'usbtl_st'
usbtl_zip = 'usbtl_zip'
usbtl_county = 'usbtl_county'
usbtl_addr_full = 'usbtl_addr_full'

dt_d = '_dt_d'
dt_m = '_dt_m'
dt_y = '_dt_y'

symptoms = 'symptoms'
treated = 'treated'
partners = 'partners'

requires_manual = 'requires_manual'
sti_pkg_name = 'sti_pkg_name'
fax_target = 'fax_target'
prc_clinic_addr = 'prc_clinic_addr'
device = 'device'
result = 'result'
loc_addr_full = 'loc_addr_full'
no_positives = 'no_positives'
naat = 'naat'

# ================================================================================
#with open(join(cwd, file_cfg), 'w') as c: cfg.write(c)

_ = '_' # lol?
flag_not = '!'
pre_manual = '_manual '
ext_sti_template = '_sti_template.pdf'
ext_csv = '.csv'
ext_pdf = '.pdf'
ext_zip = '.zip'
ext_2 = '_2'
pre_sti = 'sti_'
ext_st = '_st'
ext_result = '_result'
pdf_st_other_text = '_st_other_txt'
csv_date = 'csv_date'

chk = 'chk'
chk_ = _ + chk + _

pdf_check = '/Yes'
meta_author = '/Author'
meta_producer = '/Producer'
meta_title = '/Title'
meta_description = '/Description'
meta_creation_date = '/CreationDate'
meta_mod_date = '/ModDate'

dir_last = 'last_run'
dir_temp = 'temp'
dir_output = 'output'
dir_report_templates = 'report_templates'
dir_rules = 'rules'

path_archive = dir_archive if ':' in dir_archive else join(cwd, dir_archive)
path_rules_state = join(dir_rules, file_rules_state)
path_rules_prac = join(dir_rules, file_rules_prac)
path_map_sample_types = join(dir_rules, file_map_sample_types)
path_map_sti = join(dir_rules, file_map_sti)

file_errs = 'errors.txt'
file_warns = 'warnings.txt'
path_errs = join(dir_last, file_errs)
path_warns = join(dir_last, file_warns)
default = 'Default'
unknown = 'Unknown'
sti_pos = 'pos'
sti_neg = 'neg'

hep_exposure_other = 'hep_exposure_other'
hep_chk_exposure_other = 'hep_chk_exposure_other'
hep_chk_symptoms_unknown = 'hep_chk_symptoms_unknown'
syph_rpr = code_syph.lower() + '_rpr'
syph_rpr_chk = syph_rpr + _ + chk
syph_rpr_chk_pos = syph_rpr + chk_ + sti_pos
syph_rpr_chk_neg = syph_rpr + chk_ + sti_neg
syph_eia = code_syph.lower() + '_eia'
syph_eia_chk = syph_eia + _ + chk
syph_eia_chk_pos = syph_eia + chk_ + sti_pos
syph_titer = code_syph.lower() + '_titer'
syph_chk_stage_unknown = code_syph.lower() + '_chk_stage_unknown'
syph_chk_symptoms_other = code_syph.lower() + '_chk_symptoms_other'
syph_symptoms_other_txt = code_syph.lower() + '_symptoms_other_txt'

pt_fn_2 = pt_fn + ext_2
pt_ln_2 = pt_ln + ext_2
pt_dob_2 = pt_dob + ext_2

ymd = '%Y-%m-%d'
re_ymd = '\d{4}\-\d{2}\-\d{2}'

zip_send = 'sent'
zip_manual = 'manual'
zip_failed = 'failed'

c_prefix = 'https://geocoding.geo.census.gov/geocoder/geographies/address?'
c_bench = 'benchmark=Public_AR_Current'
c_vintage = 'vintage=Current_Current'
c_key = 'key=' + h.c_key
c_format = 'format=json'
census_link = c_prefix + c_bench + '&' + c_vintage + '&' + c_key + '&' + c_format

secret_temp_val = 'FIXME'

test_csv = '\\\\Usbtl-serv-pdc1\\Users\\nmirasol\\My Documents\\Python\\auto-sti-fax\\testing\\testing 1776-07-02.csv'

states = [
    'AL', 'AK', 'AZ', 'AR',
    'CA', 'CO', 'CT',
    'DE',
    'FL',
    'GA',
    'HI',
    'ID', 'IL', 'IN', 'IA',
    'KS', 'KY',
    'LA',
    'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT',
    'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND',
    'OH', 'OK', 'OR',
    'PA',
    'RI',
    'SC', 'SD',
    'TN', 'TX',
    'UT',
    'VT', 'VA',
    'WA', 'WV', 'WI', 'WY'
]

path_skipped = join(cwd, dir_last, 'skipped ' + dt.today().strftime(ymd) + '.csv')

def get_distro_list(): return distro_list.replace(',', ';').replace(' ', '')
