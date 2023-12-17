from flask import Blueprint
from zou.app.utils.api import configure_api_from_blueprint

from .resources import (
    GamesResource,
    GameResource,
    GameScoresResource,
    GameScoreResource,
    GameVariantsResource,
    GameVariantResource,
)


routes = [
    ("/data/games", GamesResource),
    ("/data/games/<instance_id>", GameResource),
    ("/data/games/<instance_id>/game_variants", GameVariantsResource),
    ("/data/game_variants/<instance_id>", GameVariantResource),
    ("/data/games/<instance_id>/game_scores/", GameScoresResource),
    ("/data/game_scores/<instance_id>", GameScoreResource),
]

blueprint = Blueprint("gaming", "gaming")
api = configure_api_from_blueprint(blueprint, routes)