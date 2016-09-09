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
    #ldap_conn.search(user_search_ou, "(uid=bencentra)", attributes=ALL_ATTRIBUTES)
    #print(ldap_conn.entries)
    #ldap_conn.search(group_search_ou, "(cn=*)", attributes=['cn'])
    #print(ldap_conn.entries[0].cn)
