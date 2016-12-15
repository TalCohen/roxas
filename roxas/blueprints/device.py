import os
import signal

import structlog

from flask import Blueprint, request, render_template, redirect, url_for, session, flash, g
from sqlalchemy import cast, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import or_

from roxas.models.models import Device
from roxas.util.ldap import ldap_get_user_by_username, ldap_get_user_by_uuid, ldap_get_users_by_uuids, ldap_get_all_groups, ldap_get_all_users, ldap_get_all_active_users, ldap_get_user_groups
from roxas.util.utils import generate_api_key, row_to_dict, update_row_from_dict, ldap_to_dict, ldap_list_to_string_list, list_to_dict, is_admin, is_accessible_by, get_all_users_id, get_all_users_str
from roxas import db, auth

# Get the logger
logger = structlog.get_logger()

# Create the blueprint
device_bp = Blueprint('device_bp', __name__)

@device_bp.before_request
#@auth.oidc_auth
def get_user_info():
    # Get the username
    #username = session['userinfo'].get('preferred_username', '')
    #uuid = session['userinfo'].get('sub', '')
    username = request.headers.get('x-webauth-user')

    # If the uuid isn't set or the usernames are not the same, set the correct values
    #if not session.get('uuid') == uuid or not session.get('username') == username:
    if not session.get('uuid') or not session.get('username') == username:
        # Store the user's username
        session['username'] = username

        # Get the user's uuid and store it 
        user = ldap_get_user_by_username(username, ['entryUUID'])
        session['uuid'] = user.entryUUID.value
        #session['uuid'] = uuid

        # Check to see if the user is an admin or not
        session['is_admin'] = is_admin(session['username'])

def get_context():
    # Create the context with some default values
    context = {}
    context['username'] = session['username']
    context['uuid'] = session['uuid']
    context['display_name'] = "WEBAUTH_USER"#session['userinfo'].get('name', 'CSH Member')
    context['is_admin'] = session['is_admin']

    return context

def get_user_devices(username, uuid):
    # Get the user groups
    user_groups = ldap_get_user_groups(username, ['cn'])
    user_groups = ldap_list_to_string_list(user_groups, 'cn')

     # By default it uses text[], so explicity cast to a varchar[]
    user = cast([uuid], ARRAY(String()))
    user_groups = cast(user_groups, ARRAY(String()))

    # Get the devices where there are device_owners/accessible_by in common
    owned_devices = Device.query.filter(or_(Device.device_owners_users.contains(user), Device.device_owners_groups.overlap(user_groups))).order_by(Device.name).all()

    # Add the get_all_users_id() option
    user = cast([get_all_users_id(), uuid], ARRAY(String()))
    accessible_devices = Device.query.filter(or_(Device.accessible_by_users.overlap(user), Device.accessible_by_groups.overlap(user_groups))).order_by(Device.name).all()

    return (owned_devices, accessible_devices)

def is_device_owner(username, uuid, device):
    # If the user is an owner, return true
    if uuid in device.device_owners_users:
        return True

    # Get the user groups
    user_groups = ldap_get_user_groups(username, ['cn'])
    user_groups = ldap_list_to_string_list(user_groups, 'cn')

    # If the two groups are not disjoint, the user is an owner
    if not set(user_groups).isdisjoint(device.device_owners_groups):
        return True

    return False

def has_owner_rights(username, uuid, device):
    return session['is_admin'] or is_device_owner(username, uuid, device)

def has_access(username, uuid, device):
    return session['is_admin'] or is_accessible_by(username, uuid, device)

def get_people_csv(users, attr):
    # Get the usernames
    users = ldap_list_to_string_list(users, attr)
    return string_list_to_sorted_csv(users)

def string_list_to_sorted_csv(lst):
   lst.sort()
   return ", ".join(lst)

def get_device_context(device):
    # Get the usernames of the owners
    device_owners_users = ldap_get_users_by_uuids(device.device_owners_users, ['uid'])
    device_owners_users_str = get_people_csv(device_owners_users, 'uid')

    # Get the usernames of the accessible by users
    accessible_by_users = ldap_get_users_by_uuids(device.accessible_by_users, ['uid'])
    accessible_by_users_str = get_people_csv(accessible_by_users, 'uid')

    # If get_all_users_id() is in accessible users, add it to the string
    if get_all_users_id() in device.accessible_by_users:
        accessible_by_users_str = get_all_users_str() + (", " if len(accessible_by_users_str) > 0 else "") + accessible_by_users_str

    # Format the names of the groups
    device_owners_groups = string_list_to_sorted_csv(device.device_owners_groups)
    accessible_by_groups = string_list_to_sorted_csv(device.accessible_by_groups)

    # Get the username of the person who created it
    created_user = ldap_get_user_by_uuid(device.created_by, ['uid'])
    created_user = created_user.uid.value

    # Build the context
    device_context = {
        'id': device.id,
        'name': device.name,
        'description': device.description,
        'device_owners_users': device_owners_users_str,
        'device_owners_groups': device_owners_groups,
        'accessible_by_users': accessible_by_users_str,
        'accessible_by_groups': accessible_by_groups,
        'api_key': device.api_key,
        'created_by': created_user,
        'enabled': device.enabled,
    }

    return device_context

def get_form_context(
        device_context,
        title,
        action,
        submit_button_str,
        device_owners_users_dict,
        device_owners_groups_dict,
        accessible_by_users_dict,
        accessible_by_groups_dict):

    # Get the sorted ldap groups
    ldap_groups = ldap_get_all_groups(['cn'])
    ldap_groups_dicts = [ldap_to_dict(group) for group in ldap_groups]
    ldap_groups_dicts.sort(key=lambda x: x['cn'])

    # Get the sorted ldap active users
    ldap_users = ldap_get_all_users(['uid', 'entryUUID'])
    ldap_users_dicts = [ldap_to_dict(user) for user in ldap_users]
    ldap_users_dicts.sort(key=lambda x: x['uid'])

    form_context = {
        'device': device_context,
        'title': title,
        'action': action,
        'submit_button_str': submit_button_str,
        'ldap_groups': ldap_groups_dicts,
        'ldap_users': ldap_users_dicts,
        'device_owners_users_dict': device_owners_users_dict,
        'device_owners_groups_dict': device_owners_groups_dict,
        'accessible_by_users_dict': accessible_by_users_dict,
        'accessible_by_groups_dict': accessible_by_groups_dict,
        'all_users': get_all_users_id(),
        'all_users_str': get_all_users_str(),
    }
    form_context.update(get_context())

    return form_context

def validate_fields(d):
    # If the name is empty, give a test name
    if d['name'].strip() == "":
        d['name'] = "Test Device"
    # If the description is empty, give a test description
    if d['description'].strip() == "":
        d['description'] = "Test Description"

    # If no owners were selected, default to the current user
    if len(d['device_owners_users']) + len(d['device_owners_groups']) == 0:
        d['device_owners_users'] = [session['uuid']]
    # If no accessible_by users were selected, default to the current user
    if len(d['accessible_by_users']) + len(d['accessible_by_groups']) == 0:
        d['accessible_by_users'] = [session['uuid']]

@device_bp.route('/', methods=['GET'])
def index():
    # Get the devices for the user
    (owned_devices, accessible_devices) = get_user_devices(session['username'], session['uuid'])

    # Map the rows to a list of dictionaries
    owned_device_dicts = [row_to_dict(device) for device in owned_devices]
    accessible_device_dicts = [row_to_dict(device) for device in accessible_devices]

    context = get_context()
    context['owned_devices'] = owned_device_dicts
    context['accessible_devices'] = accessible_device_dicts

    return render_template("devices_index.html", **context)

@device_bp.route('/devices/all', methods=['GET'])
def all():
    # If the user isn't an admin, redirect
    if not session['is_admin']:
        return redirect(url_for('device_bp.index'))

    # Get all the devices
    devices = Device.query.order_by(Device.name).all()

    # Map the rows to a list of dictionaries
    device_dicts = [row_to_dict(device) for device in devices]

    context = get_context()
    context['devices'] = device_dicts
    return render_template("devices_all.html", **context)

@device_bp.route('/devices/new', methods=['GET'])
def new():
    # Get the context for the form
    context = get_form_context(
        {},
        "New Device",
        url_for('device_bp.index'),
        'Register',
        {},
        {},
        {},
        {})
    return render_template("devices_form.html", **context)

@device_bp.route('/', methods=['POST'])
def create():
    # Retrieve the form values
    fields = {
        'name': request.form.get('name'),
        'description': request.form.get('description'),
        'device_owners_users': request.form.getlist('device_owners_users'),
        'device_owners_groups': request.form.getlist('device_owners_groups'),
        'accessible_by_users': request.form.getlist('accessible_by_users'),
        'accessible_by_groups': request.form.getlist('accessible_by_groups'),
    }

    # Make sure all fields are valid
    validate_fields(fields)

    # Generate an api_key for the device
    api_key = generate_api_key()

    # Fill the rest of the fields
    fields['created_by'] = session['uuid']
    fields['api_key'] = api_key

    # Create the device
    device = Device(**fields)
    db.session.add(device)
    db.session.commit()

    flash("Successfully created device %s" % fields['name'])

    return redirect(url_for('device_bp.index'))

@device_bp.route('/devices/<device_id>', methods=['GET'])
def show(device_id):
    # Get the device
    device = Device.query.get(device_id)

    # If the device doesn't exist, redirect
    if device is None:
        return redirect(url_for('device_bp.index'))

    # Get the rights/access for the user 
    owner_rights = has_owner_rights(session['username'], session['uuid'], device)
    access = has_access(session['username'], session['uuid'], device)

    # Make sure the user is allowed to view this device
    if not (owner_rights or access): 
        return redirect(url_for('device_bp.index'))
   
    # Get the device context
    device_context = get_device_context(device)

    context = get_context()
    context['device'] = device_context
    context['has_owner_rights'] = owner_rights
    return render_template("devices_show.html", **context)

@device_bp.route('/devices/<device_id>/edit', methods=['GET'])
def edit(device_id):
    device = Device.query.get(device_id)

    # Make sure the user is allowed to view this device
    if device is None or not has_owner_rights(session['username'], session['uuid'], device):
        return redirect(url_for('device_bp.index'))

    # Get the device context
    device_context = get_device_context(device)

    # Also generate a dictionary for each of the four lists, which will perform faster 
    # than iterating over the lists over and over in the template
    device_owners_users_dict = list_to_dict(device.device_owners_users)
    device_owners_groups_dict = list_to_dict(device.device_owners_groups)
    accessible_by_users_dict = list_to_dict(device.accessible_by_users)
    accessible_by_groups_dict = list_to_dict(device.accessible_by_groups)

    # Get the context for the form
    context = get_form_context(
        device_context,
        device.name + " - Edit",
        url_for('device_bp.update', 
        device_id=device_id),
        'Update',
        device_owners_users_dict,
        device_owners_groups_dict,
        accessible_by_users_dict,
        accessible_by_groups_dict)
    return render_template("devices_form.html", **context)

@device_bp.route('/devices/<device_id>', methods=['POST'])
def update(device_id):
    device = Device.query.get(device_id)

    # Make sure the user is allowed to update this device
    if device is None or not has_owner_rights(session['username'], session['uuid'], device):
        return redirect(url_for('device_bp.index'))

    # Retrieve the form values
    fields = {
        'name': request.form.get('name'),
        'description': request.form.get('description'),
        'device_owners_users': request.form.getlist('device_owners_users'),
        'device_owners_groups': request.form.getlist('device_owners_groups'),
        'accessible_by_users': request.form.getlist('accessible_by_users'),
        'accessible_by_groups': request.form.getlist('accessible_by_groups'),
    }
    
    # Make sure all fields are valid
    validate_fields(fields)

    # Update the device
    update_row_from_dict(device, fields)
    db.session.commit()

    flash("Successfully updated device %s" % device.name)

    return redirect(url_for('device_bp.show', device_id=device_id))

@device_bp.route('/devices/<device_id>/delete', methods=['POST'])
def delete(device_id):
    device = Device.query.get(device_id)

    # Make sure the user is allowed to delete this device
    if device is None or not has_owner_rights(session['username'], session['uuid'], device):
        return redirect(url_for('device_bp.index'))

    name = device.name

    # Delete the device
    db.session.delete(device)
    db.session.commit()

    flash("Successfully deleted device %s" % name)

    return redirect(url_for('device_bp.index'))

@device_bp.route('/devices/<device_id>/toggle-enabled', methods=['POST'])
def toggle_enabled(device_id):
    device = Device.query.get(device_id)

    # Make sure the user is allowed to view this device
    if device is None or not has_owner_rights(session['username'], session['uuid'], device):
        return redirect(url_for('device_bp.index'))
    
    device.enabled = not device.enabled
    db.session.commit()

    action = "enabled" if device.enabled else "disabled"
    flash("Successfully %s device %s" % (action, device.name))

    route = 'device_bp.%s' % request.form.get('route')
    return redirect(url_for(route))

@device_bp.route('/restart', methods=['GET'])
def restart_app():
    # If an admin, restart the app
    if session['is_admin']:
        logger.info('api', action='restart app')
        os.kill(os.getpid(), signal.SIGINT)

        flash("Successfully restarted application.")

    return redirect(url_for('device_bp.index'))
