from sqlalchemy import func
from lion.logger.exception_logger import log_exception
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.utils.utcnow import utcnow


class ShiftIdSequence(LION_SQLALCHEMY_DB.Model):
    __tablename__ = "shiftid_sequence"

    id = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.Integer,
        primary_key=True,
        autoincrement=True
    )
    created_at = LION_SQLALCHEMY_DB.Column(
        LION_SQLALCHEMY_DB.DateTime,
        default=utcnow(),
        nullable=False
    )

    @classmethod
    def get_next_shift_id(cls):
        """
        Inserts a new row into the shiftid_sequence table
        and returns the auto-generated unique scenario ID.
        """
        try:
            new_seq = cls()
            LION_SQLALCHEMY_DB.session.add(new_seq)
            LION_SQLALCHEMY_DB.session.flush()  # Ensures ID is generated immediately
            return new_seq.id

        except Exception as e:
            log_exception(
                popup=False,
                remarks=f"Failed to get next shift id: {e}"
            )
            return None
    
    @classmethod
    def reserve_mapped_shift_ids(cls, list_of_items: list):
        """
        Reserve globally unique sequence IDs for a given list of items such as list shiftnames, shiftids, IDs, etc.
        Returns a mapping {shift_id: unique_id}.
        """
        if not list_of_items:
            return {}

        dct_mapped_shift_id = {}

        try:
            # Pre-create all sequence objects
            new_seqs = [cls() for _ in list_of_items]
            LION_SQLALCHEMY_DB.session.add_all(new_seqs)
            LION_SQLALCHEMY_DB.session.flush()  # One flush for all inserts (faster)

            # Map shiftids to generated sequence IDs
            for sid, seq in zip(list_of_items, new_seqs):
                dct_mapped_shift_id[sid] = seq.id

            return dct_mapped_shift_id

        except Exception as e:
            log_exception(popup=False, remarks=f"Failed to reserve mapped shift IDs: {e}")
            LION_SQLALCHEMY_DB.session.rollback()
            return {}
    
    @classmethod
    def reset_max_shift_id(cls, max_shift_id: int = 0):
        """
        This method ensures that the next generated shift ID will be at least max_shift_id + 1
         to avoid conflicts with existing shift IDs.
        """

        if max_shift_id <= 0:
            return
        
        max_id = cls.query.with_entities(func.max(cls.id)).scalar() or 0
        if max_shift_id <= max_id:
            return

        # Insert a new entry with the specified max_shift_id
        try:
            new_seq = cls(id=max_shift_id)
            LION_SQLALCHEMY_DB.session.add(new_seq)
            LION_SQLALCHEMY_DB.session.flush()  # Ensures ID is generated immediately
            return new_seq.id

        except Exception as e:
            log_exception(
                popup=False,
                remarks=f"Failed to get next shift id: {e}"
            )
            return None
    