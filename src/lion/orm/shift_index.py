from collections import defaultdict
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import re
from lion.create_flask_app.create_app import LION_FLASK_APP
from lion.logger.exception_logger import log_exception
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger  import log_exception
from lion.ui.ui_params import UI_PARAMS
from lion.utils.split_list import split_list
from lion.logger.status_logger import log_message
from cachetools import TTLCache

dct_cached_data = TTLCache(maxsize=100, ttl=900)


class ShiftIndex(LION_SQLALCHEMY_DB.Model):

    __bind_key__ = LION_FLASK_APP.config.get('LION_USER_SPECIFIED_BIND', 'local_schedule_db')
    __tablename__ = 'shift_index'

    shiftname = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.TEXT, nullable=False,
                          primary_key=True)

    ctrl_loc = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.String(150), nullable=False)
    idx = LION_SQLALCHEMY_DB.Column(LION_SQLALCHEMY_DB.Integer, nullable=False)

    def __init__(self, **attrs):
        self.shiftname = attrs.get('shiftname', '')
        self.ctrl_loc = attrs.get('ctrl_loc', '')
        self.idx = attrs.get('idx', 0)

    @classmethod
    def clear_all(cls):

        try:
            cls.query.delete()
            LION_SQLALCHEMY_DB.session.commit()

        except Exception:
            log_exception('clearing table failed!')

    @classmethod
    def refresh_indices(cls):

        try:

            ctrl_locs = sorted(
                list(set([loc for loc, in cls.query.with_entities(cls.ctrl_loc).all()])))

            soreted_shift_names = []

            for loc in ctrl_locs:

                objs = cls.query.filter(cls.ctrl_loc == loc).all()
                if objs:
                    shiftnames = [obj.shiftname.split('.')[1] for obj in objs]
                    soreted_shift_names.extend(
                        [f"{loc}.{x}" for x in sorted(shiftnames)])

            dct = dict((sname, idx)
                       for (idx, sname) in enumerate(soreted_shift_names))

            objs = cls.query.filter(
                cls.shiftname.in_(soreted_shift_names)).all()

            for obj in objs:
                obj.idx = dct[obj.shiftname]

            LION_SQLALCHEMY_DB.session.commit()

        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()

    @classmethod
    def update_shift_index(cls, shiftname='', ctrl_loc=''):

        try:
            if ctrl_loc == '':
                ctrl_loc = shiftname.split('.')[0]

            obj = cls.query.filter(cls.shiftname == shiftname).first()
            if not obj:

                max_idx = LION_SQLALCHEMY_DB.session.query(
                    LION_SQLALCHEMY_DB.func.max(cls.idx)).scalar() or 0

                new_obj = ShiftIndex(
                    shiftname=shiftname,
                    ctrl_loc=ctrl_loc,
                    idx=max_idx+1
                )

                LION_SQLALCHEMY_DB.session.add(new_obj)
                LION_SQLALCHEMY_DB.session.commit()

                cls.refresh_indices()

        except Exception as e:
            LION_SQLALCHEMY_DB.session.rollback()
            log_message(f"update_shift_index for {shiftname} failed! {str(e)}")

    @classmethod
    def to_dict(cls):
        """
        Returns a dict with shiftname as keys and idx as values.
        """
        try:
            objs = cls.query.all()
            if objs:
                _dct = {obj.shiftname: obj.idx for obj in objs}

                return dict(sorted(
                    _dct.items(), key=lambda x: x[1], reverse=True))
            
            return {}

        except Exception:
            log_exception(f"Failed to convert to dictionary")
            return {}

    @classmethod
    def get_dct_shift_ids_per_loc_page(cls, pagesize=15, 
                                       dct_shift_ids={}):
        """
        Returns a list of shifts controlled by ctrl_by
        """
        try:

            dct_loc_shift_ids = defaultdict(list)

            for shiftid in list(dct_shift_ids):
                dct_loc_shift_ids[dct_shift_ids[shiftid]
                                  ['controlled by']].append(shiftid)

            dct_loc_shift_ids_per_page = {}

            for ctrl_loc in list(dct_loc_shift_ids):

                sidsList = list(dct_loc_shift_ids[ctrl_loc])
                dct_loc_shift_ids_per_page[ctrl_loc] = cls.get_page_shifts(
                    dct_shift_ids={
                        sid: dct_shift_ids[sid] for sid in sidsList if sid in dct_shift_ids.keys()},
                    pagesize=pagesize)

            return dct_loc_shift_ids_per_page

        except Exception:
            log_exception()
            return {}

    @classmethod
    def get_page_shifts(cls, pagesize=15, dct_shift_ids={}):

        try:

            dct_page_shifts = {}
            if dct_shift_ids:

                if len(dct_shift_ids) <= pagesize:

                    dct_page_shifts[1] = list(dct_shift_ids)

                    return dct_page_shifts
                
                elif UI_PARAMS.SORT_BY_TOUR_LOCSTRING:
                    pages = split_list(input_list=list(dct_shift_ids), category_length=pagesize)
                else:

                    sorted_dct_shift_idx = cls.to_dict()
                    set_ids = set(dct_shift_ids)

                    dct_shift_id_idx = {
                        shiftid: sorted_dct_shift_idx.get(dct_shift_ids[shiftid]['shiftname'], 0) for shiftid in set_ids}

                    dct_shift_id_idx_sorted_by_idx = dict(sorted(dct_shift_id_idx.items(), key=lambda item: item[1],
                                                                reverse=False))

                    pages = split_list(input_list=list(dct_shift_id_idx_sorted_by_idx),
                                    category_length=pagesize)

                pagcnt = 0

                while pages:

                    list_idx = pages.pop(0)
                    pagcnt += 1
                    dct_page_shifts.update(
                        {pagcnt: list_idx})

                return dct_page_shifts
            
            else:
                raise Exception("dct_shift_ids is empty!")

        except Exception:
            log_exception(popup=False, remarks="get_page_shifts failed.")

        return {}

    @classmethod
    def get_shift_index(cls, shiftname):

        try:
            existing_obj: ShiftIndex = cls.query.filter(cls.shiftname == shiftname).first()

            if existing_obj is not None:
                return existing_obj.idx
            else:

                cls.update_shift_index(shiftname=shiftname)
                existing_obj = cls.query.filter_by(
                    shiftname=shiftname
                ).first()

                if existing_obj is not None:
                    return existing_obj.idx

        except Exception:
            return 0

    @classmethod
    def sorted(cls, dct_shifts={1001: 'AE4.S2', 1002: 'ADX.S3'}):
        """
        Sorting shift_ids based on the index logic desigend based on shiftname
        """

        try:

            objs = cls.query.filter(cls.shiftname.in_(set(dct_shifts.values()))).all()

            if objs:

                dct_idx = dict((obj.shiftname, obj.idx) for obj in objs)

                dct_shift_idx = {sid: dct_idx.get(
                    dct_shifts[sid], 0) for sid in dct_shifts.keys()}

                dct_shifts = dict(
                    sorted([(sid, idx) for sid, idx in dct_shift_idx.items()], key=lambda x: x[1], reverse=True))

                return list(dct_shifts.keys())

        except Exception:
            log_exception(popup=False, remarks='Sorting shifts failed!')

        return []

    @classmethod
    def sort_shifts(cls):

        def natural_key(text: str):
            # splits into [non-digits / digits] to sort numbers naturally
            return [int(tok) if tok.isdigit() else tok.lower() for tok in re.findall(r'\d+|\D+', text)]

        def sort_key(s: str):
            parts = s.split('.')
            first  = parts[0] if len(parts) > 0 else ''
            second = parts[1] if len(parts) > 1 else ''
            third  = parts[2] if len(parts) > 2 else ''
            # Sort primarily by first, then second, then third (all natural, case-insensitive)
            return (natural_key(first), natural_key(second), natural_key(third))

        shifts = [shift for shift, in cls.query.with_entities(cls.shiftname).all()]
        sorted_data = dict(sorted(list(set(shifts)), key=sort_key))
        dct_idx = dict((shift, idx + 1) for idx, shift in enumerate(sorted_data))

        t0 = datetime.now()
        try:
            objs: list[ShiftIndex] = cls.query.all()
            for obj in objs:
                obj.idx = dct_idx.get(obj.shiftname, obj.idx)
            LION_SQLALCHEMY_DB.session.commit()

            log_message(f"Shift sorting completed in {(datetime.now() - t0).total_seconds()} seconds.")
            return True

        except SQLAlchemyError as e:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception(popup=False, remarks=f'SQLAlchemyError: Sorting shifts failed! {str(e)}')

        except Exception:
            LION_SQLALCHEMY_DB.session.rollback()
            log_exception(popup=False, remarks='Sorting shifts failed!')

        return False
