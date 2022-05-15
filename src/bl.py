from datetime import datetime
from typing import Tuple

from pytz import timezone

from domain import User, ServiceException, Match


class Manager:
    def validate_token(self, token): pass

    def get_user(self, user_id): raise NotImplementedError()

    def update_user(self, user_id, user): raise NotImplementedError()

    def get_ladders(self): raise NotImplementedError()

    def get_players(self, ladder_id): raise NotImplementedError()

    def add_player_to_ladder(self, ladder_id, code): raise NotImplementedError()

    def update_player_order(self, ladder_id, generate_borrowed_points, player_dicts): raise NotImplementedError()

    def update_player(self, ladder_id, user_id, player_dict): raise NotImplementedError()

    def get_matches(self, ladder_id, user_id): raise NotImplementedError()

    def report_match(self, ladder_id, match_dict): raise NotImplementedError()

    def update_match_scores(self, match_id, match_dict): raise NotImplementedError()

    def delete_match(self, match_id): raise NotImplementedError()

    def decrement_borrowed_points(self): raise NotImplementedError()


class ManagerImpl:
    INVALID_RANKING_DISTANCE = 15
    MAX_MATCHES_BETWEEN_PLAYERS = 5
    MAX_MATCHES_PER_DAY = 1

    def __init__(self, firebase_client, dao):
        self.firebase_client = firebase_client
        self.dao = dao
        self.user = None

    def validate_token(self, token):
        if token is None:
            return

        try:
            firebase_user = self.firebase_client.get_firebase_user(token)
            self.user = self.dao.get_user(firebase_user["user_id"])
            if self.user is None:
                print("Creating new user: ", firebase_user)
                self.user = User(
                    user_id=firebase_user["user_id"],
                    name=firebase_user.get("name", "Unknown"),
                    email=firebase_user["email"],
                    phone_number=None,
                    photo_url=firebase_user.get("picture") if firebase_user.get("picture") != "" else None,
                    availability_text=None,
                    admin=False
                )
                self.dao.create_user(self.user)
        except Exception as error:
            print("Token auth error: ", error)
            self.user = None

    def get_user(self, user_id):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 401)
        elif user_id is None:
            raise ServiceException("No user_id passed in", 400)

        if self.user.user_id != user_id and not self.dao.in_same_ladder(self.user.user_id, user_id):
            raise ServiceException("You are only allowed to access profile information for users who are playing in the same ladder as you", 403)

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
        self.user.name = user.get("name")
        self.user.email = user.get("email")
        self.user.phone_number = user.get("phone_number")
        self.user.photo_url = user.get("photo_url")
        self.user.availability_text = user.get("availability_text")

        self.dao.update_user(self.user)
        return self.dao.get_user(user_id)

    def get_ladders(self):
        ladders = self.dao.get_ladders()

        # If the user is logged in, tack on the information about which ladders they have joined and sort them at the top
        if self.user is not None:
            user_ladder_ids = self.dao.get_users_ladder_ids(self.user.user_id)
            my_ladders = []
            other_ladders = []
            for ladder in ladders:
                if ladder.ladder_id in user_ladder_ids:
                    ladder.logged_in_user_has_joined = True
                    my_ladders.append(ladder)
                else:
                    other_ladders.append(ladder)
            ladders = my_ladders + other_ladders
        return ladders

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

    def update_player_order(self, ladder_id, generate_borrowed_points: bool, player_dicts):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 401)
        elif not self.user.admin:
            raise ServiceException("Only admins can update player orders", 403)
        elif ladder_id is None:
            raise ServiceException("No ladder_id passed in", 400)
        elif player_dicts is None:
            raise ServiceException("No players passed in", 400)

        ladder = self.dao.get_ladder(ladder_id)
        if ladder is None:
            raise ServiceException(f"No ladder with ID: {ladder_id}", 404)
        elif ladder.is_open():
            raise ServiceException("You can only update player order before the ladder has started", 403)

        user_ids_with_order = [[player_dict["user"]["user_id"], i + 1] for i, player_dict in enumerate(reversed(player_dicts))]
        self.dao.update_player_order(ladder_id, user_ids_with_order)

        if generate_borrowed_points:
            user_ids_with_borrowed_points = [[user_id, order * ladder.weeks_for_borrowed_points] for user_id, order in user_ids_with_order]
            self.dao.update_all_borrowed_points(ladder_id, user_ids_with_borrowed_points)

        return self.dao.get_players(ladder_id)

    def update_player(self, ladder_id, user_id, player_dict):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 401)
        elif not self.user.admin:
            raise ServiceException("Only admins can update players", 403)
        elif ladder_id is None:
            raise ServiceException("No ladder_id passed in", 400)
        elif user_id is None:
            raise ServiceException("No user_id passed in", 400)
        elif player_dict is None:
            raise ServiceException("No player passed in", 400)

        ladder = self.dao.get_ladder(ladder_id)
        if ladder is None:
            raise ServiceException(f"No ladder with ID: {ladder_id}", 404)
        elif not ladder.is_open():
            raise ServiceException("You can only update borrowed points after the ladder has started", 403)

        new_borrowed_points = player_dict.get("borrowed_points")
        if new_borrowed_points is None:
            raise ServiceException("New player has no borrowed points", 400)

        other_players_borrowed_points = [player.borrowed_points for player in self.dao.get_players(ladder_id)]
        if new_borrowed_points not in other_players_borrowed_points:
            raise ServiceException("You must assign a value that is already assigned to another player in the ladder", 400)

        self.dao.update_borrowed_points(ladder_id, user_id, new_borrowed_points)
        return self.get_players(ladder_id)

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

        # Check that the ladder is currently active
        if not ladder.is_open():
            raise ServiceException("This ladder is not currently open. You can only report matches between the ladder's start and end dates", 400)

        # Deserialize and validate that the rest of the match is set up properly (valid set scores and players)
        match = match_from_dict(match_dict)

        # Set match date to right now (to avoid issues with device times being changed)
        match.match_date = datetime.now(timezone("US/Mountain"))

        # Look up players in ladder
        winner = self.dao.get_player(ladder_id, match.winner_id)
        if winner is None:
            raise ServiceException("No user with id: '{}'".format(match.winner_id), 400)

        loser = self.dao.get_player(ladder_id, match.loser_id)
        if loser is None:
            raise ServiceException("No user with id: '{}'".format(match.loser_id), 400)

        if ladder.distance_penalty_on and abs(winner.ranking - loser.ranking) > ManagerImpl.INVALID_RANKING_DISTANCE:
            raise ServiceException("Players are too far apart in the rankings to challenge one another", 400)

        # Get all matches for this ladder (to enforce some of the rules below)
        ladder_matches = self.dao.get_matches(ladder_id)

        # Find out if either player has already played a match today
        if len([m for m in ladder_matches if m.has_players(match.winner_id) and m.played_today()]) > 0:
            raise ServiceException("Reported winner has already played a match today. Only one match can be played each day.", 400)
        if len([m for m in ladder_matches if m.has_players(match.loser_id) and m.played_today()]) > 0:
            raise ServiceException("Reported loser has already played a match today. Only one match can be played each day.", 400)

        # Find out if the players have already played the maximum amount of times
        matches_between_players = [m for m in ladder_matches if m.has_players(match.winner_id, match.loser_id)]
        if len(matches_between_players) >= ManagerImpl.MAX_MATCHES_BETWEEN_PLAYERS:
            raise ServiceException("Players have already played {} times.".format(ManagerImpl.MAX_MATCHES_BETWEEN_PLAYERS), 400)

        # Update the scores of the players
        match.winner_points, match.loser_points = match.calculate_scores(winner.ranking, loser.ranking, ladder.distance_penalty_on)
        print("---MATCH_REPORTING--- {} ({}) vs {} ({}): {}-{}, {}-{}, {}-{}. Winner Score: {}. Loser Score: {}".format(
            winner.user.name, winner.ranking, loser.user.name, loser.ranking,
            match.winner_set1_score, match.loser_set1_score, match.winner_set2_score, match.loser_set2_score, match.winner_set3_score, match.loser_set3_score,
            match.winner_points, match.loser_points
        ))
        self.dao.update_earned_points(match.ladder_id, match.winner_id, match.winner_points)
        self.dao.update_earned_points(match.ladder_id, match.loser_id, match.loser_points)

        # Save the match to the database (which will assign it a new match_id)
        match = self.dao.create_match(match)

        # Attach winners and losers to the match
        return self.transform_matches([match], ladder_id)[0]

    def update_match_scores(self, match_id, match_dict):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 401)
        elif not self.user.admin:
            raise ServiceException("Only admins can update matches", 403)
        elif match_id is None:
            raise ServiceException("Null match_id param", 400)
        elif match_dict is None:
            raise ServiceException("Null match param", 400)

        original_match = self.dao.get_match(match_id)
        if original_match is None:
            raise ServiceException(f"No match with ID: {match_id}", 404)
        updated_match = match_from_dict(match_dict)

        winner_score_diff, loser_score_diff = self.get_score_diff(original_match, updated_match)

        original_match.winner_set1_score = updated_match.winner_set1_score
        original_match.loser_set1_score = updated_match.loser_set1_score
        original_match.winner_set2_score = updated_match.winner_set2_score
        original_match.loser_set2_score = updated_match.loser_set2_score
        original_match.winner_set3_score = updated_match.winner_set3_score
        original_match.loser_set3_score = updated_match.loser_set3_score

        # Make sure the winner doesn't drop below the min amount. If so, correct the diff
        new_winner_points = max(original_match.winner_points + winner_score_diff, Match.MIN_WINNER_POINTS)
        winner_score_diff = new_winner_points - original_match.winner_points
        original_match.winner_points += winner_score_diff
        original_match.loser_points += loser_score_diff

        self.dao.update_match(original_match)

        self.dao.update_earned_points(original_match.ladder_id, original_match.winner_id, winner_score_diff)
        self.dao.update_earned_points(original_match.ladder_id, original_match.loser_id, loser_score_diff)

        return self.transform_matches([original_match], original_match.ladder_id)[0]

    def delete_match(self, match_id):
        if self.user is None:
            raise ServiceException("Unable to authenticate", 401)
        elif not self.user.admin:
            raise ServiceException("Only admins can delete matches", 403)
        elif match_id is None:
            raise ServiceException("Null match_id param", 400)

        match = self.dao.get_match(match_id)

        if match is not None:
            self.dao.update_earned_points(match.ladder_id, match.winner_id, -match.winner_points)
            self.dao.update_earned_points(match.ladder_id, match.loser_id, -match.loser_points)

            self.dao.delete_match(match_id)

    def decrement_borrowed_points(self):
        for ladder in self.dao.get_ladders():
            # Make sure the ladder is open, and it's using borrowed points
            if ladder.is_open() and ladder.weeks_for_borrowed_points > 0:
                # // will divide and round down
                num_weeks_since_start = (datetime.now(timezone("US/Mountain")).date() - ladder.start_date).days // 7
                weeks_left_now = ladder.weeks_for_borrowed_points - num_weeks_since_start

                # Make sure it hasn't already been decremented this week
                if weeks_left_now != ladder.weeks_for_borrowed_points_left:
                    # Update all the points
                    self.dao.decrement_borrowed_points(ladder.ladder_id, ladder.weeks_for_borrowed_points_left, weeks_left_now)

                    # Update the value on the ladder
                    ladder.weeks_for_borrowed_points_left = weeks_left_now
                    self.dao.update_ladder(ladder)

    # Utils

    @staticmethod
    def get_score_diff(original: Match, new: Match) -> Tuple[int, int]:
        (new_winner_score, new_loser_score) = new.calculate_scores(None, None, False)
        (old_winner_score, old_loser_score) = original.calculate_scores(None, None, False)
        return new_winner_score - old_winner_score, new_loser_score - old_loser_score

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


def match_from_dict(match_dict):
    return Match(
        match_dict.get("match_id"),
        match_dict.get("ladder_id"),
        match_dict.get("match_date"),
        match_dict.get("winner", {}).get("user", {}).get("user_id"),
        match_dict.get("loser", {}).get("user", {}).get("user_id"),
        match_dict.get("winner_set1_score"),
        match_dict.get("loser_set1_score"),
        match_dict.get("winner_set2_score"),
        match_dict.get("loser_set2_score"),
        match_dict.get("winner_set3_score"),
        match_dict.get("loser_set3_score")
    ).validate()
