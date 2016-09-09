import structlog

from flask import Blueprint, request, render_template, redirect, url_for
from sqlalchemy import cast, String
from sqlalchemy.dialects.postgresql import ARRAY

from roxas.models.models import Device
from roxas.util.utils import generate_api_key, row_to_dict
from roxas import db

logger = structlog.get_logger()

device_bp = Blueprint('device_bp', __name__)

@device_bp.route('/devices', methods=['GET'])
def index():
    user = 'uid=bencentra'
    # Also check in groups -> get the list of groups that this user is in from ldap and see if they have any in common - set(a).isdisjoint(b) -> True if none in common
    user_groups = ['cn=eboard']
    user_groups.append(user)
    
    # By default it uses text[], so explicity cast to a varchar[]
    user_groups = cast(user_groups, ARRAY(String()))

    # Get the devices where there are device_owners in common
    devices = Device.query.filter(Device.device_owners.overlap(user_groups)).all()

    # Create the list of devices
    device_dicts = [row_to_dict(device) for device in devices]
    
    print(devices)
    print(device_dicts)

    return render_template("devices_index.html")

@device_bp.route('/devices', methods=['POST'])
def create():
    name = request.form.get('name')
    description = request.form.get('description')
    device_owners = request.form.getlist('device_owners')
    allowed_users = request.form.getlist('allowed_users')
    required_attributes = request.form.get('required_attributes')
    #TODO: Parse required_attributes and conver to a list of strings
    
    # If no owners were selected, default to the current user
    if not device_owners:
        device_owners=['uid=tcohen']
        #TODO: REMOVE
        device_owners.append('cn=eboard')
        device_owners.append('cn=rtp')
   
    # Generate an api_key for the device
    api_key = generate_api_key(device_owners[0])

    device = Device(name, description, api_key, device_owners, allowed_users, required_attributes)
    db.session.add(device)
    db.session.commit()

    return redirect(url_for('device_bp.index'))

@device_bp.route('/devices/new', methods=['GET'])
def new():
    template_args = {}
    return render_template("devices_new.html", **template_args)

@device_bp.route('/devices/<device_id>', methods=['GET'])
def show(device_id):
    return render_template("devices_show.html")

@device_bp.route('/devices/<device_id>', methods=['PATCH, PUT'])
def update(device_id):
    return "update %s" % device_id

@device_bp.route('/devices/<device_id>', methods=['DELETE'])
def delete(device_id):
    return "delete %s" % device_id
