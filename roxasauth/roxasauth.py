import requests

class roxasauth():
    def __init__(self):
        self.roxas_url = 'http://gravity.csh.rit.edu:3333/'
        self.ibutton_url = 'ibutton/auth'
        self.nfc_auth_url = 'nfc/auth'
        self.nfc_verify_url = 'nfc/verify'

    
    def ibutton(self, api_key, ibutton, attrs=None):
        """ 
        Authenticate with a user's ibutton.

        @param: api_key - The api key for the device
        @param: ibutton - The user's ibutton/serial number
        @param: attrs - The attributes to return. The entryUUID and uid of the user is always returned.

        @return: If the request was successful, a json object with the fields 'can_access', 'message', 'returned_attributes'.
                 If the request was unsuccessful, None.
        """

        # Get the url
        url = self.roxas_url + self.ibutton_url

        # Create the payload
        data = {
            'api_key': api_key,
            'ibutton': ibutton,
            'attrs': attrs,
        }

        # Send the request
        r = requests.post(url, json=data)

        # Return the result
        if r.status_code == 200:
            return r.json()
        else: 
            return None

    def nfc(self, secret_key, api_key, serial_number, rolling_key, attrs=None):
        url = self.roxas_url + self.nfc_auth_url
        data = {
            'secret_key': secret_key,
            'api_key': api_key,
            'serial_number': serial_number,
            'rolling_key': rolling_key,
            'attrs': attrs,
        }

        r = requests.post(url, json=data)

        if not r.status_code == 200:
            return None

        d = r.json()

        # This is the information that the client needs
        print(d)

        new_rolling_key = d.get('new_rolling_key')
        if new_rolling_key is None:
            return None

        # TODO: Write to nfc and read

        # Verify
        url = self.roxas_url + self.nfc_verify_url
        data = {
            'secret_key': secret_key,
            'api_key': api_key,
            'serial_number': serial_number,
            'rolling_key': new_rolling_key,
        }

        r = requests.post(url, json=data)

        if not r.status_code == 200:
            return None

        return r.text
