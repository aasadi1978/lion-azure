import logging
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.optimization.opt_params import OPT_PARAMS
from lion.orm.changeover import Changeover
from lion.orm.shift_movement_entry import ShiftMovementEntry
from sqlalchemy import and_
from lion.logger.exception_logger import log_exception


def purge_invalid_changeover_ids():
   """
   Excludes specific changeover movements from the database based on a predefined set of movement IDs.
   This function performs the following actions:

   1. Deletes entries from the LocalChangeOversId table where the movement_id is not in the set of excluded movements defined 
      by OPT_PARAMS.SETOF_EXCLUDED_MOVEMENTS_FROM_OPT.
   2. Commits the transaction to the database.
   3. Deletes entries from the LocalMovements table where the movement_id is not in the set of excluded movements and the tu_dest 
      field is not empty.
   4. Commits the transaction to the database.

   Note:

   - The function relies on the OPT_PARAMS global configuration for the set of movement IDs to exclude.
   - Both deletions are committed separately.

   """

   try:

      Changeover.query.filter(
         ~Changeover.movement_id.in_(OPT_PARAMS.SETOF_EXCLUDED_MOVEMENTS_FROM_OPT)).delete()
      LION_SQLALCHEMY_DB.session.commit()

      ShiftMovementEntry.query.filter(
         and_(~ShiftMovementEntry.movement_id.in_(OPT_PARAMS.SETOF_EXCLUDED_MOVEMENTS_FROM_OPT),
               ShiftMovementEntry.tu_dest != '')).delete()

      LION_SQLALCHEMY_DB.session.commit()

   except Exception as e:
      logging.error(str(e))
      log_exception(f"cleaning up changeovers failed!")