import structlog
import time

from flask import Blueprint, request, render_template, json
from roxas.util.ldap import ldap_get_user_by_ibutton, ldap_get_user_by_nfc
from roxas.util.utils import ldap_to_dict, is_accessible_by, generate_nfc_key

from roxas.models.models import Device, NFC
from roxas import db

logger = structlog.get_logger()

auth_bp = Blueprint('auth_bp', __name__)

def handle_response(can_access, message, nfc=None, returned_attributes=None):
    # Create the response data
    response = {}
    response['can_access'] = can_access
    response['message'] = message

    if nfc:
        # Generate the new rolling_key and update the nfc tag
        new_rolling_key = generate_nfc_key()
        nfc.next_rolling_key = new_rolling_key
        nfc.verified = False
        db.session.commit()

        response['new_rolling_key'] = new_rolling_key

    if returned_attributes:
        response['returned_attrs'] = returned_attributes

    return json.dumps(response)

@auth_bp.route('/ibutton/auth', methods=['POST'])
def auth_ibutton():
    # Get the request args
    d = request.json
    api_key = d.get('api_key')
    ibutton = d.get('ibutton')
    attrs = d.get('attrs')
    # Add some necessary attributes
    attrs += ['entryUUID', 'uid']

    response = {}
    response['has_access'] = False

    # Get the device that sent the request
    device = Device.query.filter_by(api_key=api_key).first()
    
    # If the device doesn't exist or it's not enabled, deny access
    if device is None:
        return handle_response(False, "Invalid API key for device.")
    if not device.enabled:
        return handle_response(False, "This device has been disabled.")

    # Get the user associated with this nfc tag
    user = ldap_get_user_by_ibutton(ibutton, attrs)

    # If this ibutton is not associated with any user, deny access
    if user is None:
        return handle_response(False, "This ibutton is not registered to a user.")

    # Get the attributes of the user that were requested
    returned_attributes = ldap_to_dict(user)

    # If the user cannot access this device, deny access 
    if not is_accessible_by(returned_attributes.get('username'), returned_attributes.get('entryUUID'), device):
        return handle_response(False, "This user does not have access to this device.", returned_attributes=returned_attributes)

    # Success
    return handle_response(True, "Successfully authenticated user.", returned_attributes=returned_attributes)

def validate_rolling_key(rolling_key, nfc):
    # If the nfc tag has been fully verified since the last authentication attempt
    if nfc.verified:
        # If the nfc's rolling_key isn't correct, someone cloned it - deny access
        print(rolling_key)
        print(nfc.current_rolling_key)
        if not rolling_key == nfc.current_rolling_key:
            #TODO LOG THIS CLONING AND MORE?
            return False
    # Else, not fully verified, there might have been a network issue
    else:
        # If the nfc's rolling_key is not the current one or next one, someone cloned it - deny access
        # Note: If it's the next one it's probably because verify() was nenver reached
        if not (rolling_key == nfc.current_rolling_key or rolling_key == nfc.next_rolling_key):
            # TODO LOG THIS CLONING AND MORE?
            return False

    return True

@auth_bp.route('/nfc/auth', methods=['POST'])
def auth_nfc():
    # Get the request args
    d = request.json
    secret_key = d.get('secret_key')
    api_key = d.get('api_key')
    serial_number = d.get('serial_number')
    rolling_key = d.get('rolling_key')
    attrs = d.get('attrs')
    # Add some necessary attributes
    attrs += ['entryUUID', 'uid']

    response = {}
    response['has_access'] = False

    # If the secret key is not correct, deny access
    if not secret_key:
        print("secret none")
        return handle_response(False, "Invalid secret key for request.")

    # Get the device that sent the request
    device = Device.query.filter_by(api_key=api_key).first()
    
    # If the device doesn't exist or it's not enabled, deny access
    if device is None:
        print("dev none")
        return handle_response(False, "Invalid API key for device.")
    if not device.enabled:
        print("dev disabled")
        return handle_response(False, "This device has been disabled.")

    # Get the nfc tag
    nfc = NFC.query.filter_by(serial_number=serial_number).first() 

    # If the nfc tag doesn't exist or it's not enabled, deny access
    if nfc is None: 
        print("nfc none")
        return handle_response(False, "Invalid serial number for NFC tag.")
    if not nfc.enabled:
        print("nfc disabled")
        return handle_response(False, "This NFC tag has been disabled.", nfc)

    # Get the user associated with this nfc tag
    user = ldap_get_user_by_nfc(serial_number, attrs)

    # If this nfc tag is not associated with any user, deny access
    if user is None:
        print("user none")
        return handle_response(False, "This NFC tag is not registered to a user.", nfc)

    # Get the attributes of the user that were requested
    returned_attributes = ldap_to_dict(user)

    # If the nfc tag's rolling_key is not correct, deny access
    if not validate_rolling_key(rolling_key, nfc):
        print("key none")
        return handle_response(False, "Invalid rolling key for NFC tag.", nfc, returned_attributes)

    # If the user cannot access this device, deny access 
    if not is_accessible_by(returned_attributes.get('username'), returned_attributes.get('entryUUID'), device):
        print("access none")
        return handle_response(False, "This user does not have access to this device.", nfc, returned_attributes)

    # Success
    return handle_response(True, "Successfully authenticated user.", nfc, returned_attributes)

@auth_bp.route('/nfc/verify', methods=['POST'])
def verify():
    print(request.json)

    # Get the request args
    d = request.json
    secret_key = d.get('secret_key')
    api_key = d.get('api_key')
    serial_number = d.get('serial_number')
    rolling_key = d.get('rolling_key')

    # If the secret key is not correct, do nothing
    if not secret_key:
        return "Invalid secret key"

    # Get the nfc tag
    nfc = NFC.query.filter_by(serial_number=serial_number).first() 

    # If the nfc tag doesn't exist or it's already verified, do nothing
    if nfc is None or nfc.verified:
        return "Invalid NFC"

    # If the nfc tag's rolling_key is the next rolling_key
    if rolling_key == nfc.next_rolling_key:
        # Update the nfc tag
        nfc.old_rolling_key = nfc.current_rolling_key
        nfc.current_rolling_key = nfc.next_rolling_key
    # If the nfc tag's rolling_key is the current one, there was probably
    # a problem with writing the new one to the nfc tag
    elif rolling_key == nfc.current_rolling_key:
        # Update the nfc tag
        nfc.old_rolling_key = nfc.current_rolling_key
    # Else, the key sent up is wrong, do nothing
    else:
        # TODO: Log
        return "Invalid rolling key"

    # Finish updating
    nfc.next_rolling_key = None
    nfc.verified = True
    db.session.commit()

    return "Successfully verified"
