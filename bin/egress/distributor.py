
from data.formatter import is_email
from egress.send_email import send_email
from egress.send_fax import send_fax
from egress.send_summary import summarize
from engine.rules_sti import get_generic_name
import util.hidden as h
from util.janitor import pal, zip_files
from util.logger import warning
import values as v

import logging
from os import remove
from os.path import exists, join

from alive_progress import alive_it

i_send, i_manual, i_failed = 0, 1, 2
i_state, i_county, i_targets = 0, 1, 3
i_pdf_name, i_county_rule = 0, 1
i_target = 2

def send_reports(reports_breakdown, total_positives, total_processed, is_dry):
    list_reports, breakdown = reports_breakdown[0], reports_breakdown[1]
    grouped = group_reports(list_reports)
    dict_send, list_manual, list_failed = grouped[i_send], grouped[i_manual], grouped[i_failed]

    total_reports = len(list_manual)
    for state in dict_send: total_reports += len(dict_send.get(state))

    distribute(dict_send, breakdown, is_dry)
    return summarize(total_reports, total_positives, dict_send, list_manual, list_failed, total_processed, is_dry)

# could turn this into a "hotfix" sorta deal
# have a list of terms saved to a file that can be updated
# no code push necessary to pull certain STIs out, etc
#def process_exceptions(report):
#    for sti in report[i_county_rule][2]:
#        if v.code_syph in sti: return True
#    return False

def group_reports(reports):
    logging.info('Grouping reports for distribution...')
    list_send, list_manual, list_failed = reports[i_send], reports[i_manual], reports[i_failed]
    dict_target_pdfs = {} # {target : [reports...]}
    for report in list_send:
        pdf_name, doh = report[i_pdf_name], report[i_county_rule]
        doh_state, doh_county = doh[i_state], doh[i_county]
        target = report[i_targets]

        # unnecessary at this moment
        #if process_exceptions(report):
        #    list_manual.append(report)
        #    continue

        #for target in targets:
        if target is None or target is False:
            list_manual.append(report) # issue captured in get_doh_target()
            if doh_county is None: warning('Missing county for report ' + report[0])
            else: warning('No doh target for ' + doh_state + ', county ' + doh_county + ', pdf ' + pdf_name + '!')
            continue
        elif target.lower() == v.flag_manual.lower():
            if report not in list_manual: list_manual.append(report)
            continue
        target_tuple = (doh_state, doh_county, target)
        set_names = dict_target_pdfs.get(target_tuple) if target_tuple in dict_target_pdfs else set()
        set_names.update({pdf_name})
        dict_target_pdfs.update({target_tuple: set_names}) # is this a pythonic way to write this block?

    # cleanse other lists
    for report in list_manual:
        name = report[i_pdf_name]
        for destination in dict_target_pdfs:
            struct = dict_target_pdfs.get(destination)
            if name in struct: struct.remove(name)

    logging.info('')
    return (dict_target_pdfs, list_manual, list_failed)

def distribute(dict_send, breakdown, dry):
    if v.dev or dry: return
    pal('Sending reports...')
    for tc in alive_it(dict_send):
        state, county, target = tc[i_state], tc[i_county], tc[i_target]
        summary = breakdown.get((state, county))
        set_pdfs = dict_send.get(tc)
        if is_email(target) and county is not None: email_reports(target, county, set_pdfs, summary)
        else: fax_reports(target, county, set_pdfs)
    logging.info('STI report distribution complete.')

def email_reports(target, county, set_pdfs, summary):
    full_paths = []
    logging.info('Sending the following pdfs to ' + target + ':')
    for pdf in set_pdfs:
        full_paths.append(join(v.cwd, v.dir_last, pdf))
        logging.info(pdf)
    packaged_reports = [zip_files(county + ' sti reports', full_paths)]

    count, stats = 0, ''
    for sti in summary:
        num = summary.get(sti)
        sti_name = get_generic_name(sti) # error captured in convert_code_to_name()
        if sti_name is None: sti_name = 'Please report this bug to US BioTek :)'
        stats += str(num) + ' --- ' + sti_name + '\n' 
        count += num # need error handling?
    subject = county + ' County positive STI reports'
    body = 'Hi,\n\nThis is an automated report summary from US BioTek Laboratories.'
    body += '\nTotal reports: ' + str(count) + '\n\n'
    body += stats
    send_email(target, subject, body, packaged_reports)

    for f in packaged_reports:
        if exists(f): remove(f)
    logging.info('')

def fax_reports(target, county, set_pdfs):
    logging.info('Sending faxes of the following pdfs to ' + target)
    name_path = {pdf: join(v.cwd, v.dir_last, pdf) for pdf in set_pdfs}
    send_fax(target, county, name_path)

def send_crash(message):
    send_email(h.dev_email, 'Auto STI Sender: Fatal crash report', '༎ຶ⁠‿⁠༎ຶ\n' + str(message), attachments=[v.path_run_log])
