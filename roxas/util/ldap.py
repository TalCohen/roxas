from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES

# Global state is gross. I'm sorry.
ldap_conn = None
user_search_ou = None
committee_search_ou = None
group_search_ou = None
read_only = False

def ldap_init(ro, ldap_url, bind_dn, bind_pw, user_ou, group_ou, committee_ou):
    global user_search_ou, group_search_ou, committee_search_ou, ldap_conn, read_only
    read_only = ro
    user_search_ou = user_ou
    group_search_ou = group_ou
    committee_search_ou = committee_ou
    
    server = Server(ldap_url, use_ssl=True, get_info=ALL)
    ldap_conn = Connection(server, bind_dn, bind_pw, auto_bind=True)

    print(ldap_conn)
    #ldap_conn.search(group_search_ou, "(member:=uid=tcohen,ou=Users,dc=csh,dc=rit,dc=edu)", attributes=['cn'])
    #print(ldap_conn.entries)
    #ldap_conn.search(group_search_ou, "(cn=*)", attributes=['cn'])
    #print(ldap_conn.entries[0].cn)
    #ldap_conn.search(user_search_ou, "(uid=bencentra)", attributes=['uid', 'entryUUID'])
    #entry = ldap_conn.entries[0]

def ldap_get_user(filter, returned_attributes):
    ldap_conn.search(user_search_ou, filter, attributes=returned_attributes)
    return ldap_conn.entries[0] if len(ldap_conn.entries) else None

def ldap_get_user_by_username(uid, returned_attributes):
    return ldap_get_user("(uid=%s)" % uid, returned_attributes)

def ldap_get_user_by_uuid(uuid, returned_attributes):
    return ldap_get_user("(entryUUID=%s)" % uuid, returned_attributes)

def ldap_get_user_by_ibutton(nfc, returned_attributes):
    return ldap_get_user("(ibutton=%s)" % nfc, returned_attributes)

def ldap_get_user_by_nfc(nfc, returned_attributes):
    # Currently there is no NFC attribute in LDAP, so ibutton is used here too.
    return ldap_get_user("(ibutton=%s)" % nfc, returned_attributes)

def build_filter(attrs, attr_name):
    # Build the filter that matches any of the uuids
    filter = '(|'
    for attr in attrs:
        filter += '(%s=%s)' % (attr_name, attr)
    filter += ')'

    return filter

def ldap_get_users_by_uuids(uuids, returned_attributes):
    # If we received no uuids, return emtpy array
    if len(uuids) == 0:
        return []

    filter = build_filter(uuids, 'entryUUID')

    ldap_conn.search(user_search_ou, filter, attributes=returned_attributes)
    return ldap_conn.entries

def ldap_get_groups_by_fields(fields, returned_attributes):
    ldap_conn.search(group_search_ou, fields, attributes=returned_attributes)
    return ldap_conn.entries

def ldap_get_all_groups(returned_attributes):
    return ldap_get_groups_by_fields("(cn=*)", ['cn'])

def ldap_get_users_by_fields(fields, returned_attributes):
    ldap_conn.search(user_search_ou, fields, attributes=returned_attributes)
    return ldap_conn.entries

def ldap_get_all_users(returned_attributes):
    return ldap_get_users_by_fields("(uid=*)", returned_attributes)

def ldap_get_all_active_users(returned_attributes):
    return ldap_get_users_by_fields("(active=1)", returned_attributes)

def ldap_get_user_groups(uid, returned_attributes):
    ldap_conn.search(group_search_ou, "(member:=uid=%s,ou=Users,dc=csh,dc=rit,dc=edu)" % uid, attributes=returned_attributes)
    return ldap_conn.entries

