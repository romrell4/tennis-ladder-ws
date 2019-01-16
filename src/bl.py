from datetime import datetime

from domain import User, ServiceException, Match

class Manager:
    INVALID_RANKING_DISTANCE = 12

    def __init__(self, firebase_client, dao):
        self.firebase_client = firebase_client
        self.dao = dao
        self.user = None

    def validate_token(self, token):
        if token is None: return

        try:
            firebase_user = self.firebase_client.get_firebase_user(token)
            self.user = self.dao.get_user(firebase_user["user_id"])
            if self.user is None:
                self.user = User(firebase_user["user_id"], firebase_user["name"], firebase_user["email"], None, firebase_user.get("picture"))
                self.dao.create_user(self.user)
        except (KeyError, ValueError):
            pass

    def get_user(self, user_id):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 401)
        elif user_id is None:
            raise ServiceException("No user_id passed in", 400)

        if self.user.user_id != user_id:
            raise ServiceException("You are only allowed to get your own profile information", 403)

        return self.dao.get_user(user_id)

    def update_user(self, user_id, user):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 401)
        elif user_id is None:
            raise ServiceException("No user_id passed in", 400)
        elif user is None:
            raise ServiceException("No user passed in to update", 400)

        if self.user.user_id != user_id:
            raise ServiceException("You are only allowed to update your own profile information", 403)

        # Update the logged in user with all editable information
        if "name" in user: self.user.name = user.get("name")
        if "email" in user: self.user.email = user.get("email")
        if "phone_number" in user: self.user.phone_number = user.get("phone_number")
        if "photo_url" in user: self.user.photo_url = user.get("photo_url")

        self.dao.update_user(self.user)
        return self.dao.get_user(user_id)

    def get_ladders(self):
        return self.dao.get_ladders()

    def get_players(self, ladder_id):
        # The database handles all the sorting and derived fields
        return self.dao.get_players(ladder_id)

    def add_player_to_ladder(self, ladder_id, code):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 401)
        elif ladder_id is None:
            raise ServiceException("Null ladder_id param", 400)

        # Look up ladder
        if self.dao.get_ladder(ladder_id) is None:
            raise ServiceException("No ladder with id: '{}'".format(ladder_id), 404)

        # Look up ladder code
        real_code = self.dao.get_ladder_code(ladder_id)

        # If sure that if a code exists, that it matches
        if real_code is not None and real_code != code:
            raise ServiceException("The code provided does not match the code of the ladder. If you believe this in error, please contact the ladder's sponsor.", 400)

        # Create the new player, tying the user to the ladder
        self.dao.create_player(ladder_id, self.user.user_id)

        # Return the new list of players in that ladder (which should include the new player)
        return self.dao.get_players(ladder_id)

    def get_matches(self, ladder_id, user_id):
        # Get all the matches (which will only have user ids, not the full player)
        matches = self.dao.get_matches(ladder_id, user_id)

        # Attach winners and losers to the matches
        return self.transform_matches(matches, ladder_id)

    def report_match(self, ladder_id, match_dict):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 401)
        elif ladder_id is None:
            raise ServiceException("Null ladder_id param", 400)
        elif match_dict is None:
            raise ServiceException("Null match param", 400)

        # Look up ladder
        ladder = self.dao.get_ladder(ladder_id)
        if ladder is None:
            raise ServiceException("No ladder with id: '{}'".format(ladder_id), 404)

        # Deserialize and validate that the rest of the match is set up properly (valid set scores and players)
        match = Match.from_dict(match_dict)

        # Look up players in ladder
        winner = self.dao.get_player(ladder_id, match.winner_id)
        if winner is None:
            raise ServiceException("No user with id: '{}'".format(match.winner_id), 400)

        loser = self.dao.get_player(ladder_id, match.loser_id)
        if loser is None:
            raise ServiceException("No user with id: '{}'".format(match.loser_id), 400)

        if abs(winner.ranking - loser.ranking) > Manager.INVALID_RANKING_DISTANCE:
            raise ServiceException("Players are too far apart in the rankings to challenge one another", 400)

        # Update the scores of the players
        winner_score, loser_score = match.calculate_scores(winner.ranking, loser.ranking, ladder.distance_penalty_on)
        self.dao.update_score(match.winner_id, match.ladder_id, winner_score)
        self.dao.update_score(match.loser_id, match.ladder_id, loser_score)

        # Set match date to right now (to avoid issues with device times being changed)
        match.match_date = datetime.utcnow()

        # Save the match to the database (which will assign it a new match_id)
        match = self.dao.create_match(match)

        # Attach winners and losers to the match
        return self.transform_matches([match], ladder_id)[0]

    def transform_matches(self, matches, ladder_id):
        # Get all players in that ladder
        players = self.dao.get_players(ladder_id)

        # Create a map for quick and easy look up
        player_map = {}
        for player in players:
            player_map[player.user.user_id] = player

        # Attach the winners and losers to the match
        for match in matches:
            match.winner = player_map[match.winner_id]
            match.loser = player_map[match.loser_id]

        return matches
