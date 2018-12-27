from domain import User, ServiceException, Match

class Manager:
    def __init__(self, firebase_client, dao):
        self.firebase_client = firebase_client
        self.dao = dao
        self.user = None

    def validate_token(self, token):
        if token is None: return

        try:
            firebase_user = self.firebase_client.get_firebase_user(token)
            self.user = User(firebase_user["user_id"], firebase_user["name"], firebase_user["email"], firebase_user["picture"])
            if self.dao.get_user(self.user.user_id) is None:
                self.dao.create_user(self.user)
        except (KeyError, ValueError):
            pass

    def get_ladders(self):
        return self.dao.get_ladders()

    def get_players(self, ladder_id):
        # The database handles all the sorting and derived fields
        return self.dao.get_players(ladder_id)

    def get_matches(self, ladder_id, user_id):
        # Get all the matches (which will only have user ids, not the full player)
        matches = self.dao.get_matches(ladder_id, user_id)

        # Get all players in that ladder
        players = self.dao.get_players(ladder_id)

        # Create a map for quick and easy look up
        player_map = {}
        for player in players:
            player_map[player.user_id] = player

        # Attach the winners and losers to the match
        for match in matches:
            match.winner = player_map[match.winner_id]
            match.loser = player_map[match.loser_id]

        return matches

    def report_match(self, ladder_id, match_dict):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 403)
        elif ladder_id is None:
            raise ServiceException("Null ladder_id param", 400)
        elif match_dict is None:
            raise ServiceException("Null match param", 400)

        # Look up ladder
        ladder = self.dao.get_ladder(ladder_id)
        if ladder is None:
            raise ServiceException("No ladder with id: '{}'".format(ladder_id), 404)

        match = Match.from_dict(match_dict)

        # Validate that the rest of the match is set up properly (valid set scores and players)
        match.validate()

        # Look up players in ladder
        winner = self.dao.get_player(ladder_id, match.winner_id)
        if winner is None:
            raise ServiceException("No user with id: '{}'".format(match.winner_id), 400)

        loser = self.dao.get_player(ladder_id, match.loser_id)
        if loser is None:
            raise ServiceException("No user with id: '{}'".format(match.loser_id), 400)

        print(winner)
        print(loser)

        # TODO: Mark
        # TODO: Set match date to right now (to avoid issues with device times being changed)
        self.dao.create_match(match)
        return match
