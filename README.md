# Roxas
[Roxas](https://roxas.csh.rit.edu) is a new authentication solution for CSH. You can register an iButton/RFID/NFC reader on the site and then use the authentication API to authenticate a user with the registered device. 

Usage
-----
The easiest way to use the authentication API is to use the [RoxasAuth](https://github.com/TalCohen/roxasauth) Python wrapper. If that's not an option, instructions on using the API are listed below.

For ibutton authentication, make a POST request to `https://roxas.csh.rit.edu/ibutton/auth` with a JSON payload containing the device's API key as `api_key`, the user's ibutton serial number as `ibutton`, and a list of desired LDAP attributes to be returned for the user as `attrs`.

Below is an example in Python:
```
>>> import requests
>>>
>>> url = "https://roxas.csh.rit.edu/ibutton/auth"
>>> data = {
    'api_key': 'API_KEY',
    'ibutton': '4F0A0D0022824A01',
    'attrs': ['uid', 'entryUUID', 'roomNumber']
}
>>>
>>> r = requests.post(url, json=data)
>>> r.json()
{'message': 'Successfully authenticated user.', 'can_access': True, 'returned_attrs': {'uid': 'tcohen', 'entryUUID': 'ba9b46f4-94cb-1031-9eb0-1fc026a2fe14', 'roomNumber': '3074'}}
```

A JSON object is returned with three keys: whether the user can access the device or not, a message, and the requested attributes as a dictionary of attributes to their values, as shown in the example above.


For NFC authentication, *TO BE FINISHED*
