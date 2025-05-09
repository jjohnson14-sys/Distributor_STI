
from data.csv_parser import add_to_skipped
from data.formatter import format_date_tuple, format_gender, format_phone_tuple, format_phone_display as ffd, is_email
from engine.rules_prac import apply_prac_rules
from engine.rules_sample import get_sample_type
from engine.rules_sti import convert_code_to_name, get_generic_code, get_generic_name
from util.janitor import pal
from util.logger import error, warning
import values as v

from datetime import date
import logging
from math import trunc
from os import mkdir
from os.path import exists, join

from alive_progress import alive_it
from pypdf import PdfReader as pdfr, PdfWriter as pdfw

extra_fields = [v.dt_collected, v.dt_report_generated, v.order_id]

i_device, i_markttl, i_sample_type, i_result = 0, 1, 2, 3
pt_gender_label, pt_gender_marking = 0, 1
i_has_county, i_requires_manual = 1, 2
i_pt_info, i_sti_tuple = 0, 1
i_sti_pkg = 1
i_y, i_m, i_d = 0, 1, 2
i_sti = 0
i_reports_per = 1

map_st_tpl_display = 2
map_st_tpl_form = 3

def generate_reports(list_positives, rules_states):
    pal('Generating pdfs...')
    list_send, list_manual, list_failed = [], [], []
    breakdown = {} # {(state, county): {sti: num reported}}

    for pt_info_sti in alive_it(list_positives):
        logging.info('')
        pt_info, list_sti_tuple = pt_info_sti[i_pt_info], pt_info_sti[i_sti_tuple]
        doh_state, order_id = pt_info.get(v.doh_state), pt_info.get(v.order_id)
        if not rules_states.has_rules(doh_state):
            add_to_skipped(pt_info_sti)
            logging.info('Skipping ' + doh_state + ' ' + order_id + '...')
            continue
        pt_county = pt_info.get(v.pt_county)

        reportable = [sti for sti in list_sti_tuple if rules_states.state_has_sti(doh_state, sti[i_markttl])]
        if len(reportable) == 0:
            logging.warning('No reportable conditions in order ' + order_id + ', state ' + doh_state)
            continue
        for sti in list_sti_tuple:
            if sti in reportable: continue
            logging.warning('No rule defined for state, sti: ' + doh_state + ', ' + sti[i_markttl] + '. Skipping...')
        
        reportable = package_tuples(reportable)
        pt_info_sti = (pt_info, reportable)

        for sti in reportable:
            st_county = (doh_state, pt_county)
            sti_count = breakdown.get(st_county) if st_county in breakdown else {sti: 0}
            count = sti_count.get(sti) + 1 if sti in sti_count else 1
            sti_count.update({sti: count})
            breakdown.update({st_county: sti_count})
        
        reports_generated = gen_report_list(pt_info_sti, rules_states)
        if reports_generated is None or len(reports_generated) == 0 or reports_generated[0] is False or all(report is None for report in reports_generated):
            warning('Could not generate report(s) for order id: ' + order_id)
            add_to_skipped(pt_info_sti)
            list_failed.append(pt_info_sti)
            continue

        for report in reports_generated:
            if report is False: continue # logged elsewhere
            if not report[i_requires_manual]: list_send.append(report)
            else:
                logging.info(
                    'Manual intervention required for ' + order_id + ', ' +
                    pt_info.get(v.pt_ln) + ', ' +
                    pt_info.get(v.pt_fn)
                )
                list_manual.append(report)

    logging.info('PDF generation complete.')
    return (list_send, list_manual, list_failed), breakdown

def populate_pdf(report, target, template, sti_name=None, marker=None):
    pt_info, list_sti_tuple = report[i_pt_info], report[i_sti_tuple]
    doh_state = pt_info.get(v.doh_state)
    county = pt_info.get(v.pt_county)
    order_id = pt_info.get(v.order_id)
    pt_fn, pt_ln = pt_info.get(v.pt_fn), pt_info.get(v.pt_ln)

    today = date.today()
    log_date = pt_info.get(v.dt_order)
    log_date = log_date[:log_date.index(' ')]

    info = supplement_pt_info(pt_info)
    info_dict, requires_manual = info[i_pt_info], pt_info.get(v.requires_manual)
    prc_dict = apply_prac_rules(info_dict)
    pdf_dict = info_dict | prc_dict

    logging.info('Generating PDF report for order: ' + order_id + '...')
    if not exists(template):
        error('Report template for ' + doh_state + ', sti: ' + sti_name + ' does not exist! Skipping...')
        return None
    reader, writer = pdfr(template), pdfw()
    if not reader or not writer: # load these first before we get the data
        error('COULDN\'T LOAD PDF TEMPLATE!!! ' + template)
        return None
    
    page = reader.pages[0]
    fields = reader.get_fields()
    writer.append(reader)
    writer.add_metadata({
        v.meta_author: 'Nick Mirasol',
        v.meta_producer: 'US BioTek Laboratories',
        v.meta_title: order_id + v._ + pt_ln + v._ + pt_fn,
        v.meta_description: 'Automatically generated pdf.',
        v.meta_creation_date: today.strftime(v.ymd),
        v.meta_mod_date: today.strftime(v.ymd)
    })

    is_generic = 'sti_0_st' in fields # FIXME FIXME FIXME please change the way 'generic' forms are detected
    sti_info = get_stis_from_report(info_dict, list_sti_tuple, is_generic)
    sti_dict, generic_sti_dict = sti_info[i_pt_info], sti_info[1] # <--- ew
    if not sti_dict: return None # error captured in get_stis_from_report()
    if generic_sti_dict == True: return None
    if sti_dict.get(v.no_positives) == True:
        return False

    sti_set = set()
    for sti_st in sti_dict:
        sti_set.update([sti_st[i_sti]])
        pdf_dict = pdf_dict | sti_dict.get(sti_st)

    if target is not False and not is_email(target): pdf_dict.update({v.fax_target: target})

    if generic_sti_dict is not False:
        for entry in generic_sti_dict:
            st_str = str(generic_sti_dict.get(entry)).replace("'", '').replace('{', '').replace('}', '')
            generic_sti_dict.update({entry: st_str}) # ^ smelly
        pdf_dict = pdf_dict | generic_sti_dict

    # handles reports similar to NC template
    if is_generic and sti_name is not None:
        i = 0
        sti_pkg = sti_info[0] # <--- replace hardcoded vals
        for sti_tuple in sti_pkg:
            curr = sti_pkg.get(sti_tuple)
            sti_pre = 'sti_' + str(i)
            result = curr.get(v.result)#v.d_sti_pos if v.syph_titer not in curr else curr.get(v.syph_titer)
            pdf_dict.update({
                sti_pre: pdf_dict.get(sti_pre), # TODO HACK FIXME verify this is done
                sti_pre + '_st': sti_tuple[1],
                sti_pre + '_result': result,
                sti_pre + '_desc': convert_code_to_name(sti_tuple[0], sti_pkg.get(sti_tuple).get(v.device))
            })
            i += 1

    pdf_name = pdf_dict.get(v.csv_date) + ' ' + doh_state + '_' + order_id
    if sti_name is not None: pdf_name += '_' + sti_name
    if marker is not None: pdf_name += v._ + marker
    pdf_name += ' ' + pt_ln + '_' + pt_fn
    pdf = save_pdf(pdf_dict, writer, doh_state, order_id, pdf_name)

    if pdf is None:
        error('COULD NOT SAVE PDF FOR SOME REASON!!!')
        return pdf

    # check for undesirable terms on form
    reader = pdfr(join(v.cwd, v.dir_last, pdf))
    fields = reader.get_form_text_fields()
    for field in fields:
        filled = fields.get(field)
        if filled is None: continue
        if v.secret_temp_val in filled:
            requires_manual = True

    return (pdf, (doh_state, pdf_dict.get(v.pt_county), sti_set), requires_manual, target)

# TODO HACK FIXME add naat chk
def get_stis_from_report(pt_info, sti_tuples, generic=False):
    dt_collected = format_date_tuple(pt_info.get(v.dt_collected))
    order_id = pt_info.get(v.order_id)
    state = pt_info.get(v.pt_st)
    sti_dict = {}
    sti_st_set = {} # {(sti, device): set(sample_type)}
    bonus_tracker = 0

    for sti_tuple in sti_tuples:
        result = sti_tuple[i_result]
        if result == v.d_sti_neg: continue # skip negatives (for now)

        #result = translate_result(result)
        diag_dict = {}
        code, device = sti_tuple[i_markttl], sti_tuple[i_device]
        cdt = (code, device)
        code_l = code.lower() # for string comparisons
        sample_type = get_sample_type(sti_tuple[i_sample_type], state)
        if not sample_type: return None # error logged in get_sample_type()

        st_display = sample_type[map_st_tpl_display]
        # if the sti is already in the dict, update its set of sample types
        if cdt in sti_st_set: sti_st_set.get(cdt).update([st_display])
        else: # instantiate and add set
            st = {st_display}
            sti_st_set.update({cdt: st})

        code_generic = get_generic_code(code).lower()
        diag = code_generic + v.chk_ + sample_type[map_st_tpl_form].lower()
        diag_generic = code_generic + v.chk_ + v.sti_pos
        dt_y = code_generic + v.dt_y
        dt_m = code_generic + v.dt_m
        dt_d = code_generic + v.dt_d
        pt_treated = code_generic + v.chk_ + v.treated
        partners_treated = code_generic + v.chk_ + v.partners + v._ + v.treated + v._ + v.unknown.lower()
        pt_symptoms = code_generic + v.chk_ + v.symptoms + v._ + v.unknown.lower()
        diag_chk_naat = code_generic + v.chk_ + v.naat

        if pt_info.get(v.pt_st) == 'WI':
            ...

        diag_dict.update({
            diag: v.pdf_check,
            diag_generic: v.pdf_check,
            dt_y: dt_collected[i_y],
            dt_m: dt_collected[i_m],
            dt_d: dt_collected[i_d],
            pt_treated: v.pdf_check,
            partners_treated: v.pdf_check,
            pt_symptoms: v.pdf_check,
            v.device: device,
            v.result: result,
            code_generic + v._ + v.dt_collected: pt_info.get(v.dt_collected),
            diag_chk_naat: v.pdf_check
        })

        if v.code_hep in code: # handle hep
            hep_pos = code_generic + v.chk_ + v.sti_pos
            diag_dict.update({
                hep_pos: v.pdf_check,
                v.hep_chk_symptoms_unknown: v.pdf_check,
                v.hep_exposure_other: v.unknown,
                v.hep_chk_exposure_other: v.pdf_check
            })

        elif v.code_syph in code and result != v.d_sti_neg: # handle syph
            if ':' in result: #result.isnumeric():
                chk_res = v.syph_rpr_chk_pos if result[0] != '0' else v.syph_rpr_chk_neg
                diag_dict.update({
                    v.syph_titer: result,
                    v.syph_rpr_chk: v.pdf_check,
                    chk_res: v.pdf_check
                })
            diag_dict.update({
                v.syph_eia_chk: v.pdf_check,
                v.syph_eia_chk_pos: v.pdf_check,
                v.syph_chk_stage_unknown: v.pdf_check,
                v.syph_chk_symptoms_other: v.pdf_check,
                v.syph_symptoms_other_txt: v.unknown
            })

        # TODO rework this
        if sample_type[map_st_tpl_form].lower() == v.flag_other.lower():
            sti_other = code_l + v.pdf_st_other_text
            diag_dict.update({sti_other: sample_type[map_st_tpl_display]})

        sti_sample = (code, sample_type[i_sample_type])
        sti_dict.update({sti_sample: diag_dict})

        # realizing now that this updates the diag_dict inside sti_dict
        # i did not know that python worked in such a way
        # so it must reference the original object rather than spawning a new one
        # neat :D
        for bonus in extra_fields:
            val = '' if pt_info.get(bonus) is None else pt_info.get(bonus)
            diag_dict.update({bonus + '_' + str(bonus_tracker): val})
        bonus_tracker += 1
    
    if len(sti_dict) == 0:
        warning('Sample ' + pt_info.get(v.order_id) + ' listed but no positives?')
        sti_dict.update({v.no_positives: True})

    if not generic: return sti_dict, generic

    # ==================== generic pdf info ====================
    if len(package_tuples(sti_tuples)) > v.pdf_generic_max_entries:
        error('NUMBER OF CONDITIONS REPORTED EXCEEDS MAX FORM LENGTH!!! YOU MUST DETERMINE HOW TO FILL THIS ONE OUT YOURSELF!!! Order id: ' + order_id)
        return sti_dict, True

    generic_dict = {}
    slots_occupied = 0 # tracks the number of entries being added to generic pdfs
    flag_syph, flag_hiv = False, False

    for code_device in sti_st_set:
        sti, device = code_device[0], code_device[1]
        sti_name = convert_code_to_name(sti, device)
        strcmp = sti.lower()
        if strcmp == None or strcmp == '': continue # error logged in convert_code_to_name()
        if v.code_syph.lower() in strcmp:
            flag_syph = True
            continue
        if v.code_hiv.lower() in strcmp:
            flag_hiv = True
            continue
        field = v.pre_sti + str(slots_occupied)
        generic_dict.update({
            field + v.ext_st: sti_st_set.get(code_device),
            field: sti_name,
            field + v.ext_result: v.d_sti_pos,
            field + v.chk_ + v.sti_pos: v.pdf_check
        })
        slots_occupied += 1

    if not flag_syph and not flag_hiv: return sti_dict, generic_dict

    # ==================== HIV ====================    
    if flag_hiv:
        hiv_dict = extract(v.code_hiv, sti_tuples)
        pcr, first = {}, {}
        for hiv_test in hiv_dict:
            device = hiv_test[1].lower()
            d = pcr if device == 'cobas' else first
            d.update({hiv_test: hiv_dict.get(hiv_test)})

        if len(first) > 0:
            chosen = next(iter(first))
            sti_name = convert_code_to_name(chosen[0], chosen[1])
            field = v.pre_sti + str(slots_occupied)
            generic_dict.update({
                field + v.ext_st: sti_st_set.get(chosen),
                field: sti_name,
                field + v.ext_result: v.d_sti_pos
            })
            slots_occupied += 1

        if len(pcr) > 0:
            lh = [test[0] for test in pcr]
            if 'HIV1' in lh and 'HIV2' in lh: chosen = ('HIVALL', 'cobas')
            elif 'HIV1' in lh: chosen = ('HIV1', 'cobas')
            else: chosen = ('HIV2', 'cobas')
            sti_name = convert_code_to_name(chosen[0], chosen[1])
            field = v.pre_sti + str(slots_occupied)
            generic_dict.update({
                field + v.ext_st: sti_st_set.get(chosen),
                field: sti_name,
                field + v.ext_result: v.d_sti_pos
            })
            slots_occupied += 1

    # TODO HACK FIXME get rid of the goldurn hardcoded vals
    # ==================== SYPH ====================
    if flag_syph:
        syph_disp, syph_res, syph_spec = '', '', ''
        syph_dict = dict(sorted(extract(v.code_syph, sti_tuples).items()))
        for code_device in syph_dict:
            field = v.pre_sti + str(slots_occupied)
            syph_test, device = code_device[0], code_device[1]

            test_tuple = syph_dict.get(code_device)
            syph_spec = get_sample_type(test_tuple[0], state)[2]

            syph_disp = convert_code_to_name(syph_test, device)

            res = test_tuple[1]
            if ':' in res:
                syph_res = res
                generic_dict.update({'syph_titer_' + str(slots_occupied): syph_res})
            elif res == v.d_sti_pos:
                syph_res = v.d_sti_pos # why did i do this? just assign the generic dict to res? TODO HACK FIXME

            generic_dict.update({
                field + v.ext_st: syph_spec,
                field: syph_disp,
                field + v.ext_result: syph_res
            })
            slots_occupied += 1

    if slots_occupied > v.pdf_generic_max_entries + 1: # adding to generic increments count by 1
        error('TOO MANY ENTRIES ON GENERIC PDF!!! Order id: ' + pt_info.get(v.order_id))
        return sti_dict, True

    return sti_dict, generic_dict

def save_pdf(pdf_dict, writer, doh_state, order_id, pdf_name):
    logging.info('Gathered patient / test data. Writing to pdf...')
    try:
        for i in range(0, len(writer.pages)):
            writer.update_page_form_field_values(writer.pages[i], pdf_dict)
    except KeyError:
        error('PDF GENERATION FAILED BECAUSE OF THE VERY TERRIBLY HANDLED "/AP" ERROR THAT BELONGS TO THE PYPDF MODULE!!!')
        error('There is most likely something wrong with the PDF template.')
        error('Template: ' + doh_state + v.ext_sti_template)
        return None

    logging.info('Pdf written. Attempting pdf save...')
    out_dir = join(v.cwd, v.dir_last)
    if not exists(out_dir):
        try: mkdir(out_dir)
        except FileExistsError: error('THE DIRECTORY ALREADY EXISTS...???')
        except FileNotFoundError: # parent dir missing, highly unlikely
            error('PARENT DIRECTORY MISSING??? HOW???')
            return None # could generate dir tree, but I'm really, really lazy
        except PermissionError:
            error('NO PERMISSION TO CREATE DIRECTORY AT: ' + out_dir + '!!!')
            return None
        logging.info('Created output directory. ' + out_dir)

    for tries in range(0, v.max_retries):
        out_name = (pdf_name + '_' + str(tries) if tries != 0 else pdf_name) + v.ext_pdf
        output_path = join(out_dir, out_name)
        try:
            with open(output_path, 'wb') as out: writer.write(out)
            logging.info('Saved pdf for ' + order_id + ', path: ' + output_path)
            break
        except: logging.info('Retrying pdf save...')

    if tries + 1 >= v.max_retries:
        error('CANNOT SAVE PDF FOR ORDER: ' + order_id + '!!!')
        return None

    return out_name

def supplement_pt_info(pt_info):
    info_dict = dict(pt_info)
    today = date.today()
    pt_county = info_dict.get(v.pt_county)
    has_county = (pt_county is not None and pt_county != '') # errors logged in get_county()

    info_dict.update({v.pt_phone: ffd(info_dict.get(v.pt_phone))})
    pt_phone_tuple = format_phone_tuple(info_dict.get(v.pt_phone))
    pt_fn = info_dict.get(v.pt_fn)
    pt_ln = info_dict.get(v.pt_ln)
    pt_dob = info_dict.get(v.pt_dob)
    pt_dob_cut = format_date_tuple(pt_dob)
    pt_age = trunc((today - date.fromisoformat(pt_dob)).days / 365)
    pt_gender_tuple = format_gender(info_dict.get(v.pt_gender))
    prc_addr = pt_info.get(v.loc_addr1 + ' ' + v.loc_addr2)

    dt_collected = date.fromisoformat(pt_info.get(v.dt_collected)).strftime(v.ymd)
    dt_today = today.strftime(v.ymd)

    # TODO populate dict by reading form fields? See above comment about being stupid
    info_dict.update({
        v.pt_name: pt_fn + ' ' + pt_ln,
        v.pt_fn_2: pt_fn,
        v.pt_ln_2: pt_ln,

        v.pt_phone_area: pt_phone_tuple[0],
        v.pt_phone_exch: pt_phone_tuple[1],
        v.pt_phone_line: pt_phone_tuple[2],

        v.pt_dob_y: pt_dob_cut[i_y],
        v.pt_dob_m: pt_dob_cut[i_m],
        v.pt_dob_d: pt_dob_cut[i_d],
        v.pt_dob_2: pt_dob,

        pt_gender_tuple[pt_gender_label]: pt_gender_tuple[pt_gender_marking],

        v.pt_age: pt_age,
        v.pt_orientation: v.unknown,
        v.pt_pregnant: v.unknown,

        v.prc_addr: prc_addr,

        v.dt_collected: dt_collected,
        v.dt_today: dt_today,
        v.dt_report_generated: dt_today,

        v.usbtl_submitter: v.d_usbtl_submitter,
        v.lab_phone: v.d_usbtl_phone,
        v.lab_phone + '_1': v.d_usbtl_phone,
        v.usbtl_name: v.d_usbtl_name,
        v.usbtl_street: v.d_usbtl_street,
        v.usbtl_city: v.d_usbtl_city,
        v.usbtl_st: v.d_usbtl_st,
        v.usbtl_zip: v.d_usbtl_zip,
        v.usbtl_county: v.d_usbtl_county
    })

    usbtl_addr_full = info_dict.get(v.usbtl_street) + ', ' + info_dict.get(v.usbtl_city) + ', ' + info_dict.get(v.usbtl_st) + ' ' + info_dict.get(v.usbtl_zip)
    info_dict.update({v.usbtl_addr_full: usbtl_addr_full})
    return info_dict, has_county

def gen_report_list(report, rules_states):
    info, pkgs = report[i_pt_info], report[i_sti_pkg]
    cleanse(info)
    generated = []
    reports_to_fill = {}
    county = info.get(v.pt_county)
    # group conditions by reports per
    for condition in pkgs:
        tgt_tuple = rules_states.get_doh_target(info.get(v.pt_st), county, condition, info.get(v.pt_city))
        if tgt_tuple is False:
            tgt_tuple = (False, join(v.dir_report_templates, info.get(v.pt_st) + v.ext_sti_template), False)
        target, template, reports_per = tgt_tuple[0], tgt_tuple[1], tgt_tuple[2]

        if reports_per not in reports_to_fill:
            reports_to_fill.update({reports_per: (template, [condition])})
        else:
            updated = reports_to_fill.get(reports_per)[1]
            updated.append(condition)
            reports_to_fill.update({reports_per: (template, updated)})

    one = reports_to_fill.get(v.flag_one.lower()) # reports_per lowered at ingestion
    each = reports_to_fill.get(v.flag_each.lower())
    marker = reports_to_fill.get(v.flag_marker.lower())
    unknown = reports_to_fill.get(False)

    if one is not None:
        tuples = [tpl for sti in pkgs for tpl in pkgs.get(sti)]
        generated.append(populate_pdf((info, tuples), target, template))

    elif each is not None:
        for condition in each[i_reports_per]:
            template = reports_to_fill.get('each')[0]
            info.update({v.sti_pkg_name: get_generic_name(condition)})
            generated.append(populate_pdf((info, pkgs.get(condition)), target, template, condition))

    elif marker is not None:
        for condition in marker[i_reports_per]:
            for mark in pkgs.get(condition):
                template = reports_to_fill.get('marker')[0]
                info.update({v.sti_pkg_name: get_generic_name(condition)})
                generated.append(populate_pdf((info, [mark]), target, template, condition, mark[0] + v._ + mark[2]))

    else:
        warning('Could not determine how many reports to generate for ' + info.get(v.order_id) + '! Populating default template using rule EACH.')
        for condition in unknown[1]:
            info.update({v.sti_pkg_name: get_generic_name(condition)})
            generated.append(populate_pdf((info, pkgs.get(condition)), v.flag_manual, template, condition))

    return generated

def cleanse(pt_info):
    pt_phone = format_phone_tuple(pt_info.get(v.pt_phone))
    loc_phone = format_phone_tuple(pt_info.get(v.loc_phone))
    if pt_phone == loc_phone:
        pt_info.update({v.pt_phone: ''})
        pt_info.update({v.pt_phone_area: ''})
        pt_info.update({v.pt_phone_exch: ''})
        pt_info.update({v.pt_phone_line: ''})

def package_tuples(reportable):
    package = {} # {general sti: [sti_tuple]}
    for sti_tuple in reportable:
        code_actual = get_generic_code(sti_tuple[i_markttl])
        pre = [] if code_actual not in package else package.get(code_actual)
        pre.append(sti_tuple)
        package.update({code_actual: pre})

    return package

def extract(sti_name, sti_tuples):
    return {
        (sti[i_markttl], sti[i_device]): (sti[i_sample_type], sti[i_result])
        for sti in sti_tuples
        if sti_name.lower() in sti[1].lower()
    }