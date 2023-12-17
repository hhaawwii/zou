from sqlalchemy_utils import UUIDType

from zou.app import db
from zou.app.models.serializer import SerializerMixin
from zou.app.models.base import BaseMixin


class ValidationRecord(db.Model, BaseMixin, SerializerMixin):
    """
    The validation records helps keeping track of the progress of a shot.
    It saves the state of what is validated in the timeline or not
    """

    frame_set = db.Column(db.String(1200))
    total = db.Column(db.Integer, default=0)
    shot_id = db.Column(
        UUIDType(binary=False), db.ForeignKey("entity.id"), index=True
    )
    shot = db.relationship("Entity", back_populates="validation_history")

    def __repr__(self):
        return "<ValidationRecord %s>" % self.id