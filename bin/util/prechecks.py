
from util.blurbs import get_greeting
from util.hidden import github_token as g_token, rules_url
from util.logger import error, pal
import values as v

from io import BytesIO
from os import mkdir
from os.path import basename, exists, join
from requests import get
from shutil import move, rmtree
from time import sleep
from zipfile import ZipFile

from alive_progress import alive_it

def prechecks():
    idx = v.d_usbtl_submitter.index(' ') if ' ' in v.d_usbtl_submitter else len(v.d_usbtl_submitter)
    print('How are you doing today, ' + v.d_usbtl_submitter[:idx] + '? ' + get_greeting() + '\n')

    path_last = join(v.cwd, v.dir_last)
    if exists(path_last): 
        try:
            for i in range(0, v.max_retries):
                rmtree(path_last)
                if not exists(path_last): break
                else: sleep(.5)
        except:
            pal('Couldn\'t remove last run folder! Someone might have a document inside it opened.')
            error('COULDN\'T REMOVE LAST RUN FOLDER!!!')
            return False
    mkdir(path_last)

    try: download_rules()
    except:
        error('COULDN\'T DOWNLOAD RULES!!!')
        return False

    return True

def download_rules():
    pal('Downloading rules...')
    headers = {'Authorization': 'Bearer {}'.format(g_token)}
    r = get(rules_url, headers=headers)
    z = ZipFile(BytesIO(r.content))

    members = z.namelist()
    topdir = members[0]
    if exists(topdir): rmtree(topdir)
    members.remove(topdir)    
    z.extractall()
    z.close()

    moving = []
    for file in members:
        if '.' not in file:
            actual = basename(file.rstrip('/'))
            if exists(actual): rmtree(actual)
            mkdir(actual)
        else: moving.append(file)
    for file in alive_it(moving):
        move(file, file[file.index(topdir) + len(topdir):])
    rmtree(topdir, ignore_errors=True) #spooky
