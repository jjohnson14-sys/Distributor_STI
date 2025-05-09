
from data.csv_parser import build_sti_pos_list
from data.pdf_populator import generate_reports
from egress.distributor import send_crash, send_reports
from engine.rules_states import Rules_States
import util.blurbs as b
from util.janitor import cleanup, prune_positives, stop_timer, update_tracker
from util.logger import error, pal
from util.prechecks import prechecks
import values as v

import logging
from time import sleep, time
from traceback import format_exc

i_reports = 0
i_list_pos, i_header, i_csvs = 0, 1, 2
i_send, i_manual, i_fail = 0, 1, 2

# TODO PRIO
# update archive so that top folder is day of run incl. skipped csv, subfolder contains doh csv archive
# email try except
# verify addr differences between pt and prac
# TODO
# check @ and . order in email verification
# pdf metadata
# search for sample type in fields and, if not matched, default to other?
def main():
    if v.dev: dry_actual = True
    else:
        logging.info(b.msg_run)
        dry_actual = v.dry_toggle
        if not dry_actual:
            print(b.info_dry + v.send_cmd)
            cmd = input('Send PDFs? ' + v.send_cmd + ' / no: ') 
            logging.info('User input: ' + cmd)
            dry_actual = not cmd == v.send_cmd

        if dry_actual: pal(b.confirm_dry)
        else:
            print('Distributing PDFs. You have ' + str(v.start_delay) + ' seconds to press CTRL + C to cancel execution.\n')
            sleep(v.start_delay)
    t_start = time() # start timer
    print(b.info_working)

    if not prechecks():
        pal(b.precheck_fail)
        return

    csv_tpl = build_sti_pos_list()
    list_pos, header, csvs = csv_tpl[i_list_pos], csv_tpl[i_header], csv_tpl[i_csvs]
    total_processed = len(list_pos)
    if total_processed < 1:
        pal('\nNo reports found. Perhaps I already ran today?\nCheck ' + v.dir_doh + ' for missing CSVs.\nCheck ' + v.dir_archive + ' past runs.')
        input(b.prompt_exit)
        return

    states = set(pos[0].get(v.doh_state) for pos in list_pos)
    rules_states = Rules_States(states)
    if rules_states.get_rules() is None: return # error handled in constructor

    pruned = prune_positives(list_pos, rules_states, header)

    reports = generate_reports(pruned, rules_states)
    rpt_tpl = reports[i_reports]
    if not dry_actual and v.track: update_tracker(len(rpt_tpl[i_send]), len(rpt_tpl[i_manual]), len(rpt_tpl[i_fail]))

    num_pruned = len(pruned)
    list_reports = send_reports(reports, num_pruned, total_processed, dry_actual)
    cleanup(csvs, list_reports)
    stop_timer(t_start, num_pruned, len(list_reports))

try: main()
except Exception as e: # rework later
    error('!!!', 'UNHANDLED EXCEPTION OCCURRED!!!!', '!!!')
    msg = format_exc()
    error(msg)
    if not v.dev: send_crash(msg)
    pal('\nUh oh! I crashed :(')
    input('An error message has been sent. Consult Systems Support. Press enter to close.')
    raise
