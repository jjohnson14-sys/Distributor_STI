
from data.formatter import translate_result
from util.logger import error, warning
import values as v

import csv
from datetime import datetime as dt
import logging
from os import listdir
from os.path import exists, join
from re import match, search

from alive_progress import alive_it

i_res = 3
header = None
skipped = []

def build_csv_skipped():
    if len(skipped) == 0:
        logging.info('No skipped / failed orders to record. :)')
        return None

    try:
        with open(v.path_skipped, 'w', newline='') as new_csv:
            writer = csv.writer(new_csv, delimiter=',')
            writer.writerow(header)
            for entry in skipped:
                pt, sti = entry[0], entry[1]
                row = [pt.get(val) for val in pt if val != v.csv_date]
                for sti_st in sti:
                    for d in sti_st: row.append(d)
                writer.writerow(row)
        return v.path_skipped
    except:
        error('COULD NOT WRITE CSV ' + v.path_skipped + '!!!')
        return None

def build_sti_pos_list():
    try:
        if v.dev: csvs = [v.test_csv]
        else: csvs = [
            join(v.dir_doh, f) for f in listdir(v.dir_doh)
            if match('.*?\d{4}-\d{2}-\d{2}.csv$', f.lower())
        ]
    except FileNotFoundError:
        error('NO CSVS IN TARGET FOLDER!!!')
        return

    sti_report_list, list_header = [], None
    print('Ingesting csvs...')
    for path_csv in alive_it(csvs):
        logging.info('Reading from ' + path_csv + '...')
        if not exists(path_csv):
            error('DOH STI CSV DOES NOT EXISTS AT SPECIFIED LOCATION!!!')
            return

        with open(path_csv, encoding='utf8') as sti_report:
            reader = csv.reader(sti_report)
            if reader is None:
                warning('The targeted csv is empty! Is this expected?')
                return

            matched = search(v.re_ymd, path_csv)
            csv_date = '1776-07-04' if not matched else matched.group(0)
            flag = True
            for entry in reader:
                if (flag): # process header
                    flag = False
                    if len(entry) < 1:
                        error('IMPROPERLY FORMATTED CSV!!! UNEXPECTED HEADER LENGTH!!!')
                        return
                    set_header(entry)
                    continue

                pt_info, sti_tuples = {}, []
                pt_info.update({v.csv_date: csv_date})
                len_entry = len(entry)
                try: # handle vals in csv except for sti results
                    for i in range(0, len_entry): pt_info.update({get_header()[i]: entry[i]})
                except IndexError:
                    error('INDEX ERROR POPULATING PT INFO!!! SKIPPING...')
                    continue

                pt_st = pt_info.get(v.pt_st)
                if pt_st not in v.states:
                    warning(str(pt_st) + ' isn\'t a state...? Skipping...')
                    continue
                if pt_st in v.omitted_states:
                    logging.info('Skipping omitted state ' + pt_st + '...')
                    continue

                # this handles the unknown number of sti results
                len_extra = int((len_entry - v.i_device + 1) / v.sti_tuple_size)
                for i in range(0, len_extra):
                    offset = i * v.sti_tuple_size - 1 # MIGOS
                    sti_tuples.append((
                        entry[offset + v.i_device], # to account for human csv col #s
                        entry[offset + v.i_markttl],
                        entry[offset + v.i_spl],
                        translate_result(entry[offset + v.i_result])
                    ))

                if len(sti_tuples) < 1:
                    error('PROBLEM READING STI INFORMATION FROM CSV!!! SKIPPING...')
                    continue

                pruned = [sti_tuple for sti_tuple in sti_tuples if (sti_tuple[i_res] == v.d_sti_pos or ':' in sti_tuple[i_res])]
                if len(pruned) < 1:
                    logging.info('No positives found for order ' + pt_info.get(v.order_id))
                    continue

                # truncate dt_run to just date
                dt_run = pt_info.get(v.dt_run)
                try: pt_info.update({v.dt_run: dt_run[:dt_run.index(' ')]})
                except: pt_info.update({v.dt_run: dt_run})

                sti_report_list.append((pt_info, pruned))

        logging.info('Read ' + path_csv + ' successfully.')
    return sti_report_list, header, csvs

def add_to_skipped(order):
    skipped.append(order)

def get_skipped():
    return skipped

def get_header():
    global header
    return header

def set_header(data):
    global header
    header = data
