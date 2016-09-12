import structlog

from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from sqlalchemy import cast, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import or_

from roxas.models.models import Device
from roxas.util.ldap import ldap_get_user_by_username, ldap_get_user_by_uuid, ldap_get_users_by_uuids, ldap_get_all_groups, ldap_get_all_users, ldap_get_all_active_users, ldap_get_user_groups
from roxas.util.utils import generate_api_key, row_to_dict, update_row_from_dict, ldap_to_dict, ldap_list_to_string_list, list_to_dict
from roxas import db

logger = structlog.get_logger()

device_bp = Blueprint('device_bp', __name__)

@device_bp.before_request
def get_users():
    # Get the username
    username = request.headers.get('REMOTE_USER')

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

     # By default it uses text[], so explicity cast to a varchar[]
    user = cast([uuid], ARRAY(String()))
    user_groups = cast(user_groups, ARRAY(String()))

    # Get the devices where there are device_owners in common
    devices = Device.query.filter(or_(Device.device_owners_users.contains(user), Device.device_owners_groups.overlap(user_groups))).order_by(Device.name).all()

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

def get_device_context(device):
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
        'created_by': created_user,
        'enabled': device.enabled,
    }

    return device_context

def get_form_context(device_context, title, action, submit_button_str, device_owners_users_dict, device_owners_groups_dict, accessible_by_users_dict, accessible_by_groups_dict):
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
    }

    return form_context

@device_bp.route('/devices', methods=['GET'])
def index():
    # Get the owned devices for the user
    devices = get_owned_devices(session['username'], session['uuid'])

    # Map the rows to a list of dictionaries
    device_dicts = [row_to_dict(device) for device in devices]

    context = {}
    context['devices'] = device_dicts

    return render_template("devices_index.html", **context)

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

    flash("Successfully created device %s" % name)

    return redirect(url_for('device_bp.index'))

@device_bp.route('/devices/<device_id>', methods=['GET'])
def show(device_id):
    # Get the device
    device = Device.query.get(device_id)

    # Make sure the user is allowed to view this device
    if device is None or not can_view_device(session['username'], session['uuid'], device):
        return redirect(url_for('device_bp.index'))
   
    # Get the device context
    device_context = get_device_context(device)
    
    context = {}
    context['device'] = device_context
    return render_template("devices_show.html", **context)

@device_bp.route('/devices/<device_id>/edit', methods=['GET'])
def edit(device_id):
    device = Device.query.get(device_id)

    # Make sure the user is allowed to view this device
    if device is None or not can_view_device(session['username'], session['uuid'], device):
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

    # Make sure the user is allowed to view this device
    if device is None or not can_view_device(session['username'], session['uuid'], device):
        return redirect(url_for('device_bp.index'))

    # Retrieve the form values
    update_dict = {
        'name': request.form.get('name'),
        'description': request.form.get('description'),
        'device_owners_users': request.form.getlist('device_owners_users'),
        'device_owners_groups': request.form.getlist('device_owners_groups'),
        'accessible_by_users': request.form.getlist('accessible_by_users'),
        'accessible_by_groups': request.form.getlist('accessible_by_groups'),
    }
    
    # If no owners were selected, default to the current user
    if not update_dict['device_owners_users'] and not update_dict['device_owners_groups']:
        update_dict['device_owners_users'] = [session['uuid']]

    # Update the device
    update_row_from_dict(device, update_dict)
    db.session.commit()

    flash("Successfully updated device %s" % device.name)

    return redirect(url_for('device_bp.show', device_id=device_id))

@device_bp.route('/devices/<device_id>/delete', methods=['POST'])
def delete(device_id):
    device = Device.query.get(device_id)

    # Make sure the user is allowed to view this device
    if device is None or not can_view_device(session['username'], session['uuid'], device):
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
    if device is None or not can_view_device(session['username'], session['uuid'], device):
        return redirect(url_for('device_bp.index'))
    
    device.enabled = not device.enabled
    db.session.commit()

    action = "enabled" if device.enabled else "disabled"
    flash("Successfully %s device %s" % (action, device.name))

    return redirect(url_for('device_bp.index'))
