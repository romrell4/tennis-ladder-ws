class Manager:
    def __init__(self, dao):
        self.user = None
        self.dao = dao

    def login(self):
        pass

    def get_ladders(self):
        pass

    def get_players(self, ladder_id):
        pass

    def get_matches(self, ladder_id, player_id):
        pass

    def report_match(self, ladder_id, match):
        # TODO: Mark
        pass