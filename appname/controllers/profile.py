from flask import Blueprint, session, request, jsonify, g, make_response, json

import os

from appname.models import db
from appname.models.user import User

profile = Blueprint('profile', __name__)

@profile.route("/api/profile/changePass", methods=["POST"])
def changePass():
    params = request.get_json()
    currentPass, newPass = params['currentPass'], params['newPass']
  
    user = User.query.filter_by(id=g.uid).first()

    if not user:
        return make_response(jsonify(
            message="User don't exist.",
            success=False
        ), 200)
  
    if user.check_password(currentPass):
        user.set_password(newPass)
        db.session.commit()
        return make_response(jsonify(
            message='Changed successfuly.',
            success=True
        ), 200)
        
    else:
        return make_response(jsonify(
            message='Current Password is wrong.',
            success=False
        ), 200)
        
@profile.route("/api/profile/updateMyInfo", methods=["POST"])
def updateMyInfo():
    params = request.get_json()
    email, fullName, phone1, phone2, city, state, zipCode, timeZone, picture = params['email'], params['fullName'], params['phone1'], params['phone2'], params['city'], params['state'], params['zipCode'], params['timeZone'], params['picture']
  
    user = User.query.filter_by(id=g.uid).first()

    if not user:
        return make_response(jsonify(
            message="User don't exist.",
            success=False
        ), 200)
  
    user.email = email
    user.full_name = fullName
    user.phone1 = phone1
    user.phone2 = phone2
    user.city = city
    user.state = state
    user.zipCode = zipCode
    user.timeZone = timeZone
    user.picture = picture
    db.session.commit()
    
    return make_response(jsonify(
        message='Updated successfuly.',
        success=True
    ), 200)
    
@profile.route("/api/profile/getMyInfo", methods=["POST"])
def getMyInfo():
    user = User.query.filter_by(id=g.uid).first()
    user_dict = {
        'email': user.email,
        'fullName': user.full_name,
        'phone1': user.phone1,
        'phone2': user.phone2,
        'city': user.city,
        'state': user.state,
        'zipCode': user.zipCode,
        'timeZone': user.timeZone,
        'picture': user.picture.tobytes().decode('utf-8'),
    }
    user_json = json.dumps(user_dict)
    return make_response(user_json, 200)