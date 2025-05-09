
from data.county_extractor import get_county
from data.csv_parser import add_to_skipped, get_skipped
from util.blurbs import prompt_exit
from util.logger import cleanup as clean_errors, error, pal, warning
import values as v

import logging
from os import makedirs, mkdir
from os.path import basename, exists, join
import re
from shutil import copy2, move, rmtree
from time import time
from zipfile import ZipFile

from alive_progress import alive_it
from openpyxl import load_workbook

i_pt_info, i_sti_tuple = 0, 1

# TODO cleanup the cleanup, this shit be whackkkkk
def cleanup(csvs, reports):
    if v.dev or v.dry_toggle: return
    pal('Cleaning up...')
    if not exists(v.path_archive): makedirs(v.path_archive)

    for csv in csvs:
        path_actual = join(v.dir_doh, csv)
        csv_name = csv[csv.rfind('\\') + 1:]
        path_last = join(v.cwd, v.dir_last, csv_name)
        matched = re.search(v.re_ymd, csv)

        if matched:
            ymd = matched.group(0)
            dest = join(v.path_archive, ymd)
            if exists(dest):
                try: rmtree(dest)
                except:
                    error('COULDN\'T REMOVE PREEXISTING ARCHIVE!!!')
                    dest += ' recovery'
            for i in range(0, v.max_retries):
                try:
                    mkdir(dest)
                    break
                except: error('CAN\'T MAKE ARCHIVE DIRECTORY? Attempt ' + str(i) + ' / ' + str(v.max_retries))

        else: # temp covers files without dates in the name, shouldn't ever occur
            path_temp = join(v.cwd, v.dir_temp)
            if not exists(path_temp): mkdir(path_temp)
            dest = path_temp
        path_archive = join(v.cwd, dest, csv_name)

        try:
            copy2(path_actual, path_last)
            move(path_actual, path_archive)
        except Exception as e:
            for arg in e.args: error(arg)
            error('COULD NOT ARCHIVE CSV ' + csv + '!!!')
    
    for report in reports:
        path_actual = join(v.cwd, v.dir_last, report)
        matched = re.search(v.re_ymd, report)
        if matched:
            ymd = matched.group(0)
            dest = join(v.path_archive, ymd)
        else:
            warning('Creating temp archive folder...')
            path_temp = join(v.cwd, v.dir_temp)
            if not exists(path_temp): mkdir(path_temp)
            dest = path_temp
        if not exists(dest): mkdir(dest)
        try: copy2(path_actual, dest)
        except Exception as e:
            for arg in e.args: error(arg)
            error('COULD NOT ARCHIVE ' + report + '!!!')

    skipped = get_skipped()
    if skipped is not None:
        path_archive = join(v.dir_archive, ymd)
        if exists(v.path_skipped):
            try: copy2(v.path_skipped, path_archive)
            except:
                error('COULD NOT ARCHIVE SKIPPED CSV: ' + v.path_skipped + '!!!')
                raise
    else: logging.info('No skipped results to save.')

    clean_errors()
    pal('Clean-up complete.')

# TODO rename
def prune_positives(list_positives, rules_states, csv_header):
    print('Downloading census data...')
    list_positives.sort(key=lambda k: k[0].get(v.doh_state))
    pruned, skipped = [], []

    for pt_sti in alive_it(list_positives):
        pt_info = pt_sti[i_pt_info]
        pt_st = pt_info.get(v.pt_st)
        if not rules_states.has_rules(pt_st):
            skipped.append(pt_sti)
            logging.info('No rules for state ' + pt_st + '. Skipping...')
            continue

        sti_tuple = pt_sti[i_sti_tuple]
        # eliminate carriage returns in addr
        pt_addr = pt_info.get(v.pt_addr).replace('\n', ' ')
        pt_city = pt_info.get(v.pt_city)
        pt_zip = pt_info.get(v.pt_zip)
        pt_county = get_county(pt_addr, pt_city, pt_st, pt_zip)

        pt_info.update({v.pt_addr: pt_addr})
        pt_info.update({v.pt_county: pt_county})
        pruned.append((pt_info, sti_tuple))

    for entry in skipped: add_to_skipped(entry)
    return pruned

def stop_timer(t_start, num_pruned, num_reports):
    t_elapsed = time() - t_start
    s_elapsed = str(t_elapsed)
    s_elapsed = s_elapsed[:s_elapsed.index('.') + 3]
    t_human = v.pdf_avg * num_pruned
    t_diff = str((t_human * 60 - t_elapsed) / 60)
    t_diff = t_diff[:t_diff.index('.') + 3]
    blurb = '' if t_human < 180 else ' (' + str((t_human / 60)) + ' hrs!!!)'
    pal('Complete!')
    pal('\nMy execution time was ' + s_elapsed + ' seconds to generate ' + str(num_reports) + ' reports.')
    pal('On average, you would\'ve spent ~' + str(t_human) + ' minutes filling out these reports.' + blurb)
    pal('You saved ' + t_diff + ' minutes by running me! :D')
    input(prompt_exit)

def update_tracker(full, partial, failed):
    wb_tracker = load_workbook(v.path_tracker)
    sheet = wb_tracker.active
    sheet['A7'] = int(sheet['A7'].value) + full
    sheet['A9'] = int(sheet['A9'].value) + partial
    sheet['A11'] = int(sheet['A11'].value) + failed
    wb_tracker.save(v.path_tracker)

def zip_files(name, file_list):
    path_out = join(v.cwd, v.dir_last, name + v.ext_zip)
    with ZipFile(path_out, 'w') as zipf:
        logging.info('Building zip of files: ' + str(file_list))
        for f in file_list: zipf.write(f, basename(f))
    return path_out
