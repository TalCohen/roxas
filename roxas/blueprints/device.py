import structlog

from flask import Blueprint, request, render_template, redirect, url_for, session
from sqlalchemy import cast, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import or_

from roxas.models.models import Device
from roxas.util.ldap import ldap_get_user_by_username, ldap_get_user_by_uuid, ldap_get_users_by_uuids, ldap_get_all_groups, ldap_get_all_active_users, ldap_get_user_groups
from roxas.util.utils import generate_api_key, row_to_dict, ldap_to_dict, ldap_list_to_string_list
from roxas import db

logger = structlog.get_logger()

device_bp = Blueprint('device_bp', __name__)

@device_bp.before_request
def get_users():
    # Get the username
    username = request.headers.get('REMOTE_USER')
    print(username)

    # If the uuid isn't set or the usernames are not the same, set the correct values
    if not session.get('uuid') or not session.get('username') == username:
        # Store the user's username
        session['username'] = username

        # Get the user's uuid and store it 
        user = ldap_get_user_by_username(username, ['entryUUID'])
        session['uuid'] = user.entryUUID.value

def get_owned_devices(username, uuid):
    # Get the user groups
    user_groups = ldap_get_user_groups(username, ['cn'])
    user_groups = [group.cn.value for group in user_groups]
    print(user_groups)

     # By default it uses text[], so explicity cast to a varchar[]
    user = cast([uuid], ARRAY(String()))
    user_groups = cast(user_groups, ARRAY(String()))

    # Get the devices where there are device_owners in common
    devices = Device.query.filter(or_(Device.device_owners_users.contains(user), Device.device_owners_groups.overlap(user_groups))).all()

    return devices

def can_view_device(username, uuid, device):
    # if the user is an owner, the user can view it
    if uuid in device.device_owners_users:
        return True

    # Get the user groups
    user_groups = ldap_get_user_groups(username, ['cn'])
    user_groups = ldap_list_to_string_list(user_groups, 'cn')
    #user_groups = [group.cn.value for group in user_groups]

    # If the two groups are not disjoint, the user can view it
    if not set(user_groups).isdisjoint(device.device_owners_groups):
        return True

    return False

def get_people_csv(users, attr):
    # Get the usernames
    users = ldap_list_to_string_list(users, attr)
    return string_list_to_sorted_csv(users)

def string_list_to_sorted_csv(lst):
   lst.sort()
   return ", ".join(lst)

@device_bp.route('/devices', methods=['GET'])
def index():
    # Get the owned devices for the user
    devices = get_owned_devices(session['username'], session['uuid'])

    # Map the rows to a list of dictionaries
    device_dicts = [row_to_dict(device) for device in devices]

    print(devices)
    print(device_dicts)

    context = {}
    context['devices'] = device_dicts

    return render_template("devices_index.html", **context)

@device_bp.route('/devices', methods=['POST'])
def create():
    # Retrieve the form values
    name = request.form.get('name')
    description = request.form.get('description')
    device_owners_users = request.form.getlist('device_owners_users')
    device_owners_groups = request.form.getlist('device_owners_groups')
    accessible_by_users = request.form.getlist('accessible_by_users')
    accessible_by_groups = request.form.getlist('accessible_by_groups')
    
    # If no owners were selected, default to the current user
    if not device_owners_users and not device_owners_groups:
        device_owners_users = [session['uuid']]

    # Generate an api_key for the device
    api_key = generate_api_key()

    # Create the device
    device = Device(name, description, session['uuid'], api_key, device_owners_users, device_owners_groups, accessible_by_users, accessible_by_groups)
    db.session.add(device)
    db.session.commit()

    return redirect(url_for('device_bp.index'))

@device_bp.route('/devices/new', methods=['GET'])
def new():
    # Get the sorted ldap groups
    ldap_groups = ldap_get_all_groups(['cn'])
    ldap_groups_dicts = [ldap_to_dict(group) for group in ldap_groups]
    ldap_groups_dicts.sort(key=lambda x: x['cn'])

    # Get the sorted ldap active users
    ldap_users = ldap_get_all_active_users(['uid', 'entryUUID'])
    ldap_users_dicts = [ldap_to_dict(user) for user in ldap_users]
    ldap_users_dicts.sort(key=lambda x: x['uid'])

    context = {}
    context["ldap_groups"] = ldap_groups_dicts
    context["ldap_users"] = ldap_users_dicts
    return render_template("devices_new.html", **context)

@device_bp.route('/devices/<device_id>', methods=['GET'])
def show(device_id):
    # Get the device
    device = Device.query.get(device_id)

    # Make sure the user is allowed to view this device
    if not can_view_device(session['username'], session['uuid'], device):
        return redirect(url_for('device_bp.index'))
    
    # Get the usernames of the owners
    device_owners_users = ldap_get_users_by_uuids(device.device_owners_users, ['uid'])    
    device_owners_users_str = get_people_csv(device_owners_users, 'uid')

    # Get the usernames of the accessible by users
    accessible_by_users = ldap_get_users_by_uuids(device.accessible_by_users, ['uid'])
    accessible_by_users_str = get_people_csv(accessible_by_users, 'uid')

    # Format the names of the groups
    device_owners_groups = string_list_to_sorted_csv(device.device_owners_groups)
    accessible_by_groups = string_list_to_sorted_csv(device.accessible_by_groups)

    # Get the username of the person who created it
    created_user = ldap_get_user_by_uuid(device.created_by, ['uid'])

    context = {}
    context['device'] = device
    context['device_owners_users'] = device_owners_users_str
    context['device_owners_groups'] = device_owners_groups
    context['accessible_by_users'] = accessible_by_users_str
    context['accessible_by_groups'] = accessible_by_groups
    context['created_by'] = created_user.uid
    return render_template("devices_show.html", **context)

@device_bp.route('/devices/<device_id>', methods=['PATCH', 'PUT'])
def update(device_id):
    device = Device.query.get(device_id)

    # Make sure the user is allowed to view this device
    if not can_view_device(session['username'], session['uuid'], device):
        return redirect(url_for('device_bp.index'))

    print(request.form)

    return redirect(url_for('device_bp.index'))

@device_bp.route('/devices/<device_id>', methods=['DELETE'])
def delete(device_id):
    return "delete %s" % device_id
