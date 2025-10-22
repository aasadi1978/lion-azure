from lion.logger.exception_logger import log_exception


from math import ceil


def roundup_to_nearest_5(x, base=5):

    if x is not None:
        try:
            val = ceil(float(x)/base) * base
        except Exception:
            log_exception(popup=False)
            val = 0

        return base if val <= base else val

    return x