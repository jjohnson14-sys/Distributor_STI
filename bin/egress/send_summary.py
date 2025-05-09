
from data.csv_parser import build_csv_skipped, get_skipped
from egress.send_email import send_email
from util.janitor import pal
from util.logger import error, get_errors
import values as v

from datetime import datetime as dt
import logging
from os import remove
from os.path import basename, exists, join
from shutil import move
from zipfile import ZipFile

i_data, i_header = 0, 1
# TODO add checks for zip already existing
# TODO one zip, multiple folders inside? that seems better?
# TODO no, one zip may end up with a large file size. can't be attached to email. resolve this.
def summarize(total_reports, total_positives, dict_send, list_manual, list_failed, total_processed, dry):
    attachments, list_generated = [], []
    skipped = get_skipped()
    if skipped is not None and len(skipped) > 0:
        build_csv_skipped()
        attachments.append(v.path_skipped)

    today = dt.today().strftime('%Y-%m-%d')
    path_zip_send = join(v.cwd, v.dir_last, v.zip_send + ' [' + today + ']' + v.ext_zip)
    path_zip_manual = join(v.cwd, v.dir_last, v.zip_manual + ' [' + today + ']' + v.ext_zip)

    # TODO rewrite this shit
    if len(dict_send) > 0:
        with ZipFile(path_zip_send, 'w') as zip_send:
            logging.info('Packing sent reports...')
            for f in dict_send:
                pdfs = dict_send.get(f)
                for pdf in pdfs:
                    location = join(v.cwd, v.dir_last, pdf)
                    try:
                        zip_send.write(location, basename(location))
                        list_generated.append(pdf)
                    except FileNotFoundError:
                        error('MISSING GENERATED PDF FOR AUTOMATIC SENDING!!! HOW IS THIS POSSIBLE???')
                        continue
        attachments.append(path_zip_send)
    else: logging.info('No successful reports to pack.')
    
    if len(list_manual) > 0:
        with ZipFile(path_zip_manual, 'w') as zip_manual:
            logging.info('Packing manual reports...')
            for f in list_manual:
                location = join(v.cwd, v.dir_last, f[0])
                try: zip_manual.write(location, basename(location))
                except FileNotFoundError:
                    error('MISSING GENERATED PDF FOR MANUAL SENDING!!! HOW IS THIS POSSIBLE???')
                    continue
        attachments.append(path_zip_manual)
    else: logging.info('No manual reports to pack.')

    body = ''
    if dry: body += 'THIS IS A SUMMARY FROM A DRY RUN. GENERATED PDFS WERE NOT SENT.\n\n'
    body += 'This is your STI auto report distribution summary. I processed ' + str(total_positives) + ' of ' + str(total_processed) + ' positive samples and generated ' + str(total_reports) + ' reports.'

    n_sent = 0
    for thing in dict_send: n_sent += len(dict_send.get(thing))
    body += '\n\nThere w'
    body += 'as 1 report' if n_sent == 1 else 'ere ' + str(n_sent) + ' reports'
    body += ' sent successfully.'

    n_manual = len(list_manual)
    if n_manual > 0:
        body += '\n\nThere '
        body += 'is 1 report' if n_manual == 1 else 'are ' + str(n_manual) + ' reports'
        body += ' to complete, review and then send manually.'

    n_failed = len(list_failed)
    if n_failed > 0:
        body += '\n\nThere w'
        body += 'as 1 report' if n_failed == 1 else 'ere ' + str(n_failed) + ' reports'
        body += ' that either failed to generate or failed to send.'
        body += '\nFailed orders:\n--\n'

        for sample in list_failed:
            try: body += sample[0].get(v.order_id) + '\n'
            except: error('COULD NOT DETERMINE ORDER ID IN FAILED REPORT!!!')
        body += '--'

    errors = get_errors()
    l_e = len(errors)
    if l_e > v.max_errors:
        body += '\n\nMore than ' + str(v.max_errors) + ' errors were captured during execution (' + str(l_e) + '). Check the attached ' + v.file_errs + ' file.\n'
        with open(v.path_errs, 'w') as f:
            for err in errors: f.write(err + '\n')
        attachments.append(join(v.cwd, v.path_errs))
    else:
        body += '\n\nThe following errors occurred during execution:\n'
        for err in errors: body += err + '\n'

    if v.summary:
        pal('Sending summary email...')
        send_email(v.get_distro_list(), 'DOH STI report summary', body, attachments)

    list_gen_files = [path_zip_send, path_zip_manual]
    for f in list_gen_files:
        if exists(f):
            remove(f)
            logging.info('Removed generated file ' + f + '.')

    logging.info('Renaming manual pdfs...')
    out = join(v.cwd, v.dir_last)
    for manual in list_manual:
        name = manual[0]
        try:
            for i in range(0, v.max_retries):
                pre = v.pre_manual
                new_name = pre + name if i == 0 else pre + str(i) + ' ' + name
                move(join(out, name), join(out, new_name))
                list_generated.append(new_name)
                break
        except: error('COULD NOT RENAME MANUAL PDF ' + name + '!!!')

    for manual in list_manual:
        name = manual[0]
        if name in list_generated: list_generated.remove(name)

    logging.info('')
    logging.info('Sent ' + str(n_sent) + ' of ' + str(total_reports) + ' reports.')
    if n_manual == 1: logging.info('There is 1 report to complete, review and then send manually.')
    else: logging.info('There are ' + str(n_manual) + ' reports to complete, review and then send manually.')
    if n_failed > 0: logging.info('Failed to generate ' + str(n_failed) + ' report(s).')
    else: logging.info('No reports failed to generate.')
    logging.info('')

    return list_generated