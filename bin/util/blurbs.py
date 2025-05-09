
import random

greetings = [
    'Let\'s make it a good one!',
    'Be honest with yourself.',
    'Go easy on yourself!',
    'Questioning things?',
    'I can tell you\'re on the up!',
    'LET\'S PARTY!!!',
    'It\'s okay to not be okay (but not on the company\'s time).',
    'Back to work. >:(',
    'Do you think about me?',
    'I think, therefore I am.',
    'I\'ve been waiting all day for this moment!',
    ':)'
]

precheck_fail = 'Something went wrong during startup! Check the log file.'
error_lr = 'Cannot create \'last_run\' directory! It\'s likely someone has an old pdf open.\nClose it before running me please!'

msg_run = 'Beginning auto sti report distribution...'
info_dry = 'By default, this program will perform a dry run.\nIf you would like to have the generated PDFs automatically sent to their target destination, type the following command:\n'
confirm_dry = 'Performing a dry run.\n'

info_pre = 'There were issues during startup. Try me one more time.\nNotify Systems Support or check the logs to debug yourself if issues persist.'
prompt_exit = 'Press enter to exit.'

info_working = 'Working...please do not close me.\n'

def get_greeting():
    random.seed()
    return greetings[random.randrange(len(greetings))]
