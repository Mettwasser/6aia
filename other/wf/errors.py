class APIError(Exception):
    pass


class NoSales(Exception):
    pass


class ModRankError(Exception):
    def __init__(self, mod_max_rank, url_name, *args: object) -> None:
        super().__init__(*args)
        self.mod_max_rank = mod_max_rank
        self.url_name = url_name
