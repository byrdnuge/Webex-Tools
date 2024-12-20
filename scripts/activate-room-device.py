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
    
    # Activation XML
    activation_xml = f'''
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
    
    # Time zone XML
    timezone_xml = '''
    <Configuration>
        <Time>
            <Zone>America/Chicago</Zone>
        </Time>
    </Configuration>'''
    
    # Time format XML
    time_format_xml = '''
    <Configuration>
        <Time>
            <TimeFormat>12H</TimeFormat>
        </Time>
    </Configuration>'''
    
    # Stop FirstTimeWizard XML
    stop_wizard_xml = '''
    <Command>
        <SystemUnit>
            <FirstTimeWizard>
                <Stop></Stop>
            </FirstTimeWizard>
        </SystemUnit>
    </Command>'''
    
    # They default to admin with no password on initial boot
    auth = HTTPBasicAuth('admin', '')
    
    try:
        print(f'\nUpdating device at {ip}')
        
        # Send activation command
        print('Activating...')
        r = rs.post(f'https://{ip}/putxml', data=activation_xml, auth=auth)
        r.raise_for_status()
        print(f'Activation response: {r.text}')
        
        # Send timezone command
        print('Setting timezone...')
        r = rs.post(f'https://{ip}/putxml', data=timezone_xml, auth=auth)
        r.raise_for_status()
        print(f'Timezone set response: {r.text}')
        
        # Send time format command
        print('Setting time format...')
        r = rs.post(f'https://{ip}/putxml', data=time_format_xml, auth=auth)
        r.raise_for_status()
        print(f'Time format set response: {r.text}')
        
        # Send stop FirstTimeWizard command
        print('Stopping FirstTimeWizard...')
        r = rs.post(f'https://{ip}/putxml', data=stop_wizard_xml, auth=auth)
        r.raise_for_status()
        print(f'FirstTimeWizard stop response: {r.text}')
        
    except requests.exceptions.RequestException as e:
        print(f'Failed to configure device at {ip}: {e}')

def process_csv(input_csv):
    with open(input_csv, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            ip, activation_code = row
            activate_deskpro(ip, activation_code)

if __name__ == "__main__":
    input_csv = '/Users/jbergoon/PycharmProjects/WebexTools/input/device_activation.csv'
    process_csv(input_csv)