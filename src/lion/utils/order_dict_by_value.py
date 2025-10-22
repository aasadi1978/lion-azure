from lion.logger.exception_logger import log_exception


def order_dict_by_value(dct, asc=False):
    try:
        return dict(sorted(dct.items(), key=lambda item: item[1], reverse=not asc))
    except Exception:
        log_exception(popup=False, remarks='The dict sorting failed!')
        return {}