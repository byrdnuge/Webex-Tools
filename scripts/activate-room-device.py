import requests
import urllib3
import csv
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
import os

# Load environment variables from a .env file
load_dotenv()

# Disable SSL warnings
urllib3.disable_warnings()

def activate_deskpro(ip, activation_code):
    rs = requests.Session()
    rs.verify = False
    rs.headers['Accept'] = 'application/xml'
    rs.headers['Content-Type'] = 'text/xml'
    xml_str = f'''
                <Command>
                    <Webex>
                        <Registration>
                            <Start>
                                <ActivationCode>{activation_code}</ActivationCode>
                                <SecurityAction>NoAction</SecurityAction>
                            </Start>
                        </Registration>
                    </Webex>
                </Command>'''
    # They default to admin with no password on initial boot
    auth = HTTPBasicAuth('admin', '')
    try:
        r = rs.post(f'https://{ip}/putxml', data=xml_str, auth=auth)
        r.raise_for_status()
        print(f'Successfully activated device at {ip}')
    except requests.exceptions.RequestException as e:
        print(f'Failed to activate device at {ip}: {e}')

def process_csv(input_csv):
    with open(input_csv, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            ip, activation_code = row
            activate_deskpro(ip, activation_code)

if __name__ == "__main__":
    input_csv = '/Users/jbergoon/PycharmProjects/WebexTools/input/device_activation.csv'
    process_csv(input_csv)