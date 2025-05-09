
import util.hidden as h
import logging
import requests

url_send_fax = 'https://api.documo.com/v1/faxes'

def send_fax(target, county, attachments):
    if county is None: county = ''
    logging.info('Sending faxes to target: ' + target + ', county: ' + county)

    headers = {
        'Authorization': h.fax_key
    }

    data = {
        'faxNumber': '1' + target.replace('-', ''),
        'tags': 'STI report',
        'recipientName': county + ' DOH',
        'senderName': 'US BioTek Laboratories',
        'subject': 'STI communicable disease reporting form'
    }

    files = [(('attachments'), (pdf, open(attachments.get(pdf), 'rb'), 'application/pdf')) for pdf in attachments]

    response = requests.request('POST', url_send_fax, headers=headers, data=data, files=files)
    logging.info('\nFax api response:')
    logging.info(response.text)
