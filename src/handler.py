import datetime
import json

from bl import Manager
from firebase_client import FirebaseClient
from da import Dao
from domain import ServiceException

def handle(event, _):
    return Handler.get_instance().handle(event)

class Handler:
    instance = None

    @staticmethod
    def get_instance():
        if Handler.instance is None:
            Handler.instance = Handler(Manager(FirebaseClient(), Dao()))
        return Handler.instance

    def __init__(self, manager):
        self.manager = manager

    def handle(self, event):
        try:
            if event is None or "resource" not in event or "httpMethod" not in event:
                raise ServiceException("Invalid request. No 'resource', or 'httpMethod' found in the event", 400)

            resource, method = event["resource"], event["httpMethod"]  # These will be used to specify which endpoint was being hit
            path_params = event.get("pathParameters", {}) if event.get("pathParameters") is not None else {}  # This will be used to get IDs and other parameters from the URL
            query_params = event.get("queryStringParameters", {}) if event.get("queryStringParameters") is not None else {}  # This will be used to get IDs and other parameters from the URL
            try:
                body = json.loads(event["body"])  # This will be used for most POSTs and PUTs
            except (TypeError, KeyError, ValueError):
                body = None

            self.manager.validate_token(self.get_token(event))

            if resource == "/users/{user_id}" and method == "GET":
                response_body = self.manager.get_user(path_params.get("user_id"))
            elif resource == "/users/{user_id}" and method == "PUT":
                response_body = self.manager.update_user(path_params.get("user_id"), body)
            elif resource == "/ladders" and method == "GET":
                response_body = self.manager.get_ladders()
            elif resource == "/ladders/{ladder_id}/players" and method == "GET":
                response_body = self.manager.get_players(int(path_params.get("ladder_id")))
            elif resource == "/ladders/{ladder_id}/players" and method == "POST":
                response_body = self.manager.add_player_to_ladder(int(path_params.get("ladder_id")), query_params.get("code"))
            elif resource == "/ladders/{ladder_id}/players/{user_id}" and method == "PUT":
                response_body = self.manager.update_player(int(path_params.get("ladder_id")), path_params.get("user_id"), body)
            elif resource == "/ladders/{ladder_id}/players/{user_id}/matches" and method == "GET":
                response_body = self.manager.get_matches(int(path_params.get("ladder_id")), path_params.get("user_id"))
            elif resource == "/ladders/{ladder_id}/matches" and method == "POST":
                response_body = self.manager.report_match(int(path_params.get("ladder_id")), body)
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

            return format_response(response_body)
        except ServiceException as e:
            return format_response({"error": e.error_message}, e.status_code)

    @staticmethod
    def get_token(event):
        # Lower case all the keys, then look for token
        return {k.lower(): v for k, v in event["headers"].items()}.get("x-firebase-token")

def format_response(body = None, status_code = 200):
    return {
        "statusCode": status_code,
        "body": json.dumps(body, default = default_serialize) if body is not None else None
    }

def default_serialize(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat() + "Z"
    elif isinstance(x, datetime.date):
        return x.isoformat()
    else:
        return x.__dict__
