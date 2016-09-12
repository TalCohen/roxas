from os import urandom
from binascii import hexlify
from roxas import app

def generate_api_key():
    return hexlify(urandom(20)).decode('UTF-8')

def row_to_dict(row):
    d = {}
    for column in row.__table__.columns:
        d[column.name] = getattr(row, column.name)

    return d

def update_row_from_dict(row, d):
    for key in d.keys():
        setattr(row, key, d[key])

def ldap_to_dict(ldap):
    d = {}
    for attr in ldap._attributes:
        d[attr] = str(ldap[attr].values[0])
    
    return d

def ldap_list_to_string_list(ldap_list, attr):
    return [ldap[attr].value for ldap in ldap_list]

def list_to_dict(l):
    return dict((i, True) for i in l)

@app.template_filter('empty_string_text')
def empty_string_text(s):
    if s == "":
        return "None"
    else:
        return s

@app.template_filter('none_to_empty')
def none_to_empty(s):
    if s is None:
        return ""
    else:
       return s
