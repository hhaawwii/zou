from sqlalchemy_utils import UUIDType
from zou.app import db
from zou.app.models.base import BaseMixin
from zou.app.models.person import game_variant_link
from zou.app.models.serializer import SerializerMixin


class Game(db.Model, BaseMixin, SerializerMixin):

    name = db.Column(db.String(80))
    scores = db.relationship("GameScore", back_populates="game")
    variants = db.relationship("GameVariant", back_populates="game")

    def __repr__(self):
        return "<Game %s>" % self.id


class GameVariant(db.Model, BaseMixin, SerializerMixin):

    name = db.Column(db.String(80))
    color = db.Column(db.String(7))
    badge = db.Column(db.String(10))
    title = db.Column(db.String(80))
    price = db.Column(db.Integer, default=0, nullable=False)
    game_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("game.id"), index=True
    )
    preview_file_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("preview_file.id")
    )
    game = db.relationship("Game", back_populates="variants")
    owners = db.relationship(
        "Person", secondary=game_variant_link, back_populates="game_variants"
    )

    def __repr__(self):
        return "<GameVariant %s>" % self.id


class GameScore(db.Model, BaseMixin, SerializerMixin):

    points = db.Column(db.Integer, default=0, nullable=False)
    player_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("person.id"), index=True
    )
    player = db.relationship("Person", back_populates="scores")
    game_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("game.id"), index=True
    )
    game = db.relationship("Game", back_populates="scores")

    def __repr__(self):
        return "<GameScore %s>" % self.id