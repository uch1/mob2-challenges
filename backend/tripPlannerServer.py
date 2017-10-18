from flask import Flask, request, make_response, jsonify
from flask_restful import Resource, Api
from pymongo import MongoClient
from utils.mongo_json_encoder import JSONEncoder
from bson.objectid import ObjectId
import bcrypt
from bson.json_util import dumps
import pdb
import json
from functools import wraps

app = Flask(__name__)
mongo = MongoClient('localhost', 27017)
app.db = mongo.trip_planner_development
api = Api(app)
app.bcrypt_rounds = 12

# authenticate decorator

def auth_validation(email, user_password):
    """This function is called to check if a username /
    password combination is valid.
    """

    user_collection = app.db.user
    encodedPassword = user_password.encode('utf-8')
    user = user_collection.find_one({"email": email})
    if user is None:
        return({"error": "email not found"}, 404, None)
    db_password = user['password']
    if bcrypt.hashpw(encodedPassword, db_password) == db_password:
        return True
    return False

def auth_function(f):
    def wrapper(*args, **kwargs):
        auth = request.authorization

        if not auth_validation(auth.username, auth.password):
            return ('Could not verify your access level for that URL.\n'
                    'You have to login with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required"'})
        return f(*args, **kwargs)
    return wrapper

## Write Resources here
class User(Resource):
    # for signup

    def post(self):
        # pdb.set_trace()
        new_user = request.json
        user_collection = app.db.user
        password = new_user.get('password')
        encodedPassword = password.encode('utf-8')
        hashed = bcrypt.hashpw(encodedPassword, bcrypt.gensalt(app.bcrypt_rounds))
        new_user['password'] = hashed
        print(hashed)
        if 'username' in new_user and 'email' in new_user and 'password' in new_user:
            result = user_collection.insert_one(new_user)
            new_user.pop('password')
            print('hash successed')
            return(new_user, 201, None)
        elif not 'username' in new_user:
            return({"error": "no username? you crazy"}, 404, None)
        elif not 'email' in new_user:
            return({"error": "no email? you crazy"}, 404, None)
        else:
            return("no sure why but you screwed up", 400, None)

    # def get(self):
    #     user_email = request.args.get('email')
    #     user_collection = app.db.user
    #     json_user = request.args
    #     jsonPassword = json_user.get('password')
    #     if user_email is None:
    #         return("no parameter in url", 404, None)
    #     else:
    #         user = user_collection.find_one({"email": user_email})
    #         # pdb.set_trace()
    #         if user is None:
    #             print('no user exists')
    #             return None
    #         else:
    #             encodedPassword = jsonPassword.encode('utf-8')
    #             # pdb.set_trace()
    #             if bcrypt.hashpw(encodedPassword, user['password']) == user['password']:
    #                 user.pop('password')
    #                 return(user, 200, None)
    #             else:
    #                 return('login failed', 404, None)


    @auth_function
    def get(self):
        user_collection = app.db.user
        auth = request.authorization
        user = user_collection.find_one({"email": auth.username})
        if user is None:
            print('no user exists')
            return("sorry not matched", 404, None)
        else:
            user.pop('password')
            json_user = json.loads(dumps(user))
            return (json_user, 200, None)


# # actually can only change username
    # def patch(self):
    #     user_collection = app.db.user
    #     user_email = request.args.get('email')
    #     user_name = request.args.get('username')
    #     user_collection = app.db.user
    #     if user_email == None:
    #         return ("no email in parameter", 404, None)
    #     else:
    #         user = user_collection.find_one({"email": user_email})
    #         user['email'] = user_email
    #         user_collection.save(user)
    #         return(user, 200, None)
    @auth_function
    def delete(self):
        user_collection = app.db.user
        user_email = request.authorization.email
        if user_email == None:
            return("no email", 404, None)
        else:
            user = user_collection.find_one({"email": user_email})
            pdb.set_trace()
            user_collection.remove(user)
            pdb.set_trace()
            return('the user has been deleted', 204, None)



class Trip(Resource):

    @auth_function
    def post(self):

        # pdb.set_trace()
        trip_collection = app.db.trips
        email = request.authorization.username

        user_collection = app.db.user
        user = user_collection.find_one({"email": email})

        new_trip = request.json
        # pdb.set_trace()
        new_trip["user_id"] = user["_id"]

        result = trip_collection.insert_one(new_trip)

        if result.inserted_id != None:
            return(new_trip, 201, None)
        else:
            return(None, 404, None)
        # if ('trip_name' not in new_trip):
        #     return(None, 404, None)
        # else:
        #     trip_collection.insert_one(new_trip)
        #     return(new_trip, 201, None)



    @auth_function
    def get(self):
        trip_collection = app.db.trips
        # find trip based on user_email

        email = request.authorization.username
        user_collection = app.db.user
        user = user_collection.find_one({"email": email})

        trips_result = []

        trips = trip_collection.find({"user_id": ObjectId(user["_id"])})

        for trip in trips:
            trips_result.append(trip)

        if trips_result is not None:
            return(trips_result, 200, None)
        else:
            return("no trip exist", 404, None)

    @auth_function
    def patch(self):
        trip_collection = app.db.trips
        update_trip = request.json
        if ('trip_name' in update_trip and 'destination' in update_trip and 'start_time' in update_trip):
            update_name = update_trip['trip_name']
            update_destination = update_trip['destination']
            update_start_time = update_trip['start_time']
            email = request.args.get("user_email")
            if email == None:
                return("error", 404, None)
            else:
                trip = trip_collection.find_one({"user_email": email})
                # pdb.set_trace()
                trip['trip_name'] = update_name
                trip['destination'] = update_destination
                trip['start_time'] = update_start_time
                trip_collection.save(trip)
                return('success', 200, None)
        else:
            print('hey dumdum you forgot to put info in frontend')

    @auth_function
    def delete(self):
        trip_collection = app.db.trips
        user_email = request.args.get('user_email')
        if user_email == None:
            return('error', 404, None)
        else:
            trip = trip_collection.find_one({"user_email": user_email})
            trip_collection.remove(trip)
            return(trip, 204, None)




## Add api routes here
api.add_resource(User, '/users')
api.add_resource(Trip, '/trips')
# '/user/<string:user_id>'
#this is part of json restful
#  Custom JSON serializer for flask_restful
#the application function is called first(before add route hits our function, decorator)
@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(JSONEncoder().encode(data), code)
    resp.headers.extend(headers or {})
    return resp

if __name__ == '__main__':
    # Turn this on in debug mode to get detailled information about request
    # related exceptions: http://flask.pocoo.org/docs/0.10/config/
    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    app.run(debug=True)