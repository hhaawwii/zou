from zou.app.models.gaming import Game, GameScore, GameVariant
from zou.app import db
from zou.app.services import (
    persons_service,
)


def get_games():
    return list(map(lambda x: x.serialize(relations=True), Game.get_all()))


def get_game(criterions):
    if isinstance(criterions, dict):
        game = Game.get_by(**criterions)
    else:
        game = Game.get_by(id=criterions)

    return game.serialize(relations=True) if game else None


def create_game(name):
    game = get_game({"name": name})
    if not game:
        game = Game.create(name=name).serialize()

    return game


def get_game_variant_raw(criterions):
    if isinstance(criterions, dict):
        return GameVariant.get_by(**criterions)
    return GameVariant.get_by(id=criterions)


def get_game_variants(game):
    game = get_game(game)
    if not game:
        raise Exception("The given game does not exists")

    return list(
        map(
            lambda x: x.serialize(relations=True),
            GameVariant.get_all_by(game_id=game["id"]),
        )
    )


def get_game_variant(criterions):
    game_variant = get_game_variant_raw(criterions)
    return game_variant.serialize() if game_variant else None


def create_game_variant(game, price, name, title, color):
    game = get_game(game)
    if not game:
        raise Exception("The given game does not exists")

    return GameVariant.create(
        game_id=game["id"], price=price, name=name, title=title, color=color
    ).serialize()


def get_owned_game_variant(player):
    player = persons_service.get_person_raw(player)

    if not player:
        raise Exception("The given player does not exists")

    return list(
        map(lambda x: x.serialize(relations=True), player.game_variants)
    )


def buy_game_variant(variant):
    variant = get_game_variant_raw(variant)

    player = persons_service.get_person_by_email_raw(
        persons_service.get_jwt_identity()
    )

    if not variant or not player:
        raise Exception("The given variant or player does not exists")

    if player.coins < variant.price:
        raise Exception(
            "The player does not have enough money to buy this variant"
        )

    player.game_variants.append(variant)
    db.session.add(player)
    db.session.commit()
    player.update({"coins": player.coins - variant.price})
    return player.serialize(relations=True)


def create_score(game, points):
    game = get_game(game)
    player = persons_service.get_current_user()

    if game is None or player is None:
        raise Exception("The given game or player does not exists")

    return GameScore.create(
        game_id=game["id"],
        player_id=player["id"],
        points=points,
    ).serialize()


def filter_game_score(game_score):
    EXCLUDED_KEYS = ["game"]
    INCLUDED_PLAYER_KEYS = [
        "first_name",
        "last_name",
        "full_name",
        "id",
        "has_avatar",
    ]
    game_score = {
        key: value
        for key, value in game_score.items()
        if key not in EXCLUDED_KEYS
    }
    player = {
        key: value
        for key, value in game_score.get("player", {}).items()
        if key in INCLUDED_PLAYER_KEYS
    }
    game_score["player"] = player
    return game_score


def get_scores_by_game(game, player=None, page_size=None, page_index=0):
    criterions = {"game_id": get_game(game)["id"]}
    if player is not None:
        criterions["player_id"] = persons_service.get_person(player)["id"]

    if game is None:
        raise Exception("The given game does not exists")

    scores_query = GameScore.query.filter_by(**criterions).order_by(
        GameScore.points.desc()
    )
    if page_size is not None:
        scores_query = scores_query.limit(page_size).offset(
            page_size * page_index
        )

    return list(
        map(
            lambda x: filter_game_score(x.serialize()),
            scores_query.all(),
        )
    )


def get_scores_by_player(player=None, game=None, page_size=None, page_index=0):
    criterions = {"player_id": persons_service.get_current_user().id}
    if player is not None:
        criterions["player_id"] = persons_service.get_person(player)["id"]
    if game is not None:
        criterions["game_id"] = get_game(game)["id"]

    if player is None:
        raise Exception("The given player does not exists")

    scores_query = GameScore.query.filter_by(**criterions).order_by(
        GameScore.points.desc()
    )
    if page_size is not None:
        scores_query = scores_query.limit(page_size).offset(
            page_size * page_index
        )

    return list(
        map(
            lambda x: filter_game_score(x.serialize()),
            scores_query.all(),
        )
    )
