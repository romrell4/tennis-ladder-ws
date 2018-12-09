import json

from bl import Manager
from da import Dao
from domain import ServiceException

def handle(event, context):
    # TODO: Pass in whatever data is needed to authenticate the user into the manager
    return Handler(Manager(Dao())).handle(event)

class Handler:
    def __init__(self, manager):
        self.manager = manager

    def handle(self, event):
        try:
            if event is None or "resource" not in event or "httpMethod" not in event:
                raise ServiceException("Invalid request. No 'resource', or 'httpMethod' found in the event", 400)

            resource, method = event["resource"], event["httpMethod"]  # These will be used to specify which endpoint was being hit
            path_parameters = event.get("pathParameters", {}) if event.get("pathParameters") is not None else {}  # This will be used to get IDs and other parameters from the URL
            try:
                body = json.loads(event["body"])  # This will be used for most POSTs and PUTs
            except (TypeError, KeyError, ValueError):
                body = None

            if resource == "/users" and method == "POST":
                response_body = self.manager.login()
            elif self.manager.user is None:
                # If this user isn't in our database, they are only allowed to use the login endpoint
                raise ServiceException("This user is not tracked in our database. The only allowed endpoint is /users POST to create an account.", 403)
            elif resource == "/ladders" and method == "GET":
                response_body = self.manager.get_ladders()
            elif resource == "/ladders/{ladder_id}/players" and method == "GET":
                response_body = self.manager.get_players(int(path_parameters.get("ladder_id")))
            elif resource == "/ladders/{ladder_id}/players/{player_id}/matches" and method == "GET":
                repsonse_body = self.manager.get_matches(int(path_parameters.get("ladder_id")), int(path_parameters.get("player_id")))
            elif resource == "/ladders/{ladder_id}/match" and method == "POST":
                response_body = self.manager.report_match(int(path_parameters.get("ladder_id")), body)
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

            return format_response(response_body)
        except ServiceException as e:
            return format_response({"error": e.error_message}, e.status_code)

def format_response(body = None, status_code = 200):
    return {
        "statusCode": status_code,
        "body": json.dumps(body, default = lambda x: x.__dict__) if body is not None else None
    }
