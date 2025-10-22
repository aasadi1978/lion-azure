from pandas import DataFrame
from copy import deepcopy


def secure_copy(obj):
    try:

        if isinstance(obj, (int, float)):
            return obj * 1

        if isinstance(obj, dict):
            if any(isinstance(v, (dict, list, set, tuple)) for v in obj.values()):
                return deepcopy(obj)
            return obj.copy()

        elif isinstance(obj, list):
            if any(isinstance(v, (dict, list, set, tuple)) for v in obj):
                return deepcopy(obj)
            return obj.copy()

        elif isinstance(obj, set):
            # sets shouldn't contain mutables like lists, so shallow is usually safe
            return obj.copy()

        elif isinstance(obj, tuple):
            if any(isinstance(v, (dict, list, set, tuple)) for v in obj):
                return deepcopy(obj)
            return obj  # immutable, shallow is fine

        elif isinstance(obj, DataFrame):
            return obj.copy()  # Already deep copy of data

        else:
            # For other classes: assume deepcopy is safest
            return deepcopy(obj)


    except Exception:
        return None