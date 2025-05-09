
from util.logger import error
import values as v
import logging
from win32com.client import Dispatch

app_outlook = 'Outlook.Application'
client = Dispatch(app_outlook)

def send_email(target, subject, body, attachments=None):
    acct = None
    for outlook_account in client.Session.Accounts:
        if outlook_account.SmtpAddress == v.outbound_email:
            acct = outlook_account
            break

    if acct is None:
        error('FAILED TO FIND ' + v.outbound_email + '\'S OUTLOOK ACCOUNT ON HOST MACHINE!')
        return

    # whatever is being invoked is what links the sender's account to the mail object
    #new_mail._oleobj_.Invoke(*(64209, 0, 8, 0, acct)) <--- this is the magic
    mail_out = client.CreateItem(0)
    mail_out._oleobj_.Invoke(*(64209, 0, 8, 0, acct))
    mail_out.To = target
    mail_out.Subject = subject
    mail_out.Body = body
    for attachment in attachments:
        logging.info('Attaching ' + attachment + ' to email.')
        try: mail_out.Attachments.Add(Source=attachment)
        except: error('COULD NOT ATTACH ' + attachment + ' TO EMAIL!!!')

    mail_out.Send()
    logging.info('Email sent via outlook to ' + target + '.')