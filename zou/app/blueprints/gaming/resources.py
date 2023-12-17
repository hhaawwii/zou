from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required

from zou.app.models.gaming import Game, GameVariant, GameScore
from zou.app.mixin import ArgsMixin
from zou.app.utils import permissions
from zou.app.services import gaming_service
from zou.app.blueprints.crud.base import BaseModelResource


class FreeBaseModelResource(BaseModelResource):
    def check_read_permissions(self, instance):
        return True


class GameResource(BaseModelResource, ArgsMixin):
    def __init__(self):
        BaseModelResource.__init__(self, Game)


class GamesResource(Resource, ArgsMixin):
    def get(self):
        return gaming_service.get_games()

    @jwt_required
    def post(self):
        permissions.check_admin_permissions()
        (name) = self.get_arguments()
        return gaming_service.create_game(name)

    def get_arguments(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        args = parser.parse_args()

        return (args["name"],)


class GameVariantResource(FreeBaseModelResource, ArgsMixin):
    def __init__(self):
        FreeBaseModelResource.__init__(self, GameVariant)

    @jwt_required
    def post(self, instance_id):

        return gaming_service.buy_game_variant(instance_id)


class GameVariantsResource(Resource, ArgsMixin):
    def get(self, instance_id):
        return gaming_service.get_game_variants(instance_id)

    @jwt_required
    def post(self, instance_id):
        (name, price, title, color) = self.get_argument()
        return gaming_service.create_game_variant(
            instance_id, price, name, title, color
        )

    def get_argument(self):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str)
        parser.add_argument("title", type=str)
        parser.add_argument("price", type=int)
        parser.add_argument("color", type=str)
        args = parser.parse_args()

        return (args["name"], args["price"], args["title"], args["color"])


class GameScoreResource(FreeBaseModelResource, ArgsMixin):
    def __init__(self):
        FreeBaseModelResource.__init__(self, GameScore)


class GameScoresResource(Resource, ArgsMixin):
    def get(self, instance_id):
        (page_size, page_index) = self.get_pagination_argument()
        return gaming_service.get_scores_by_game(
            instance_id, None, page_size, page_index
        )

    @jwt_required
    def post(self, instance_id):
        (points) = self.get_points_argument()
        return gaming_service.create_score(instance_id, points)

    def get_points_argument(self):
        parser = reqparse.RequestParser()
        parser.add_argument("points", type=int)
        args = parser.parse_args()

        return (args["points"],)

    def get_pagination_argument(self):
        parser = reqparse.RequestParser()
        parser.add_argument("page_size", type=int)
        parser.add_argument("page_index", type=int, default=0)
        args = parser.parse_args()

        return args["page_size"], args["page_index"]