from pandas import DataFrame
from lion.logger.exception_logger import log_exception


from os import path as os_path


def df2xml(df=None, filename='', Path=None):

    if df is None:
        df = DataFrame()

    # DataFrame.to_xml(path_or_buffer=None, index=True, root_name='data',
    # row_name='row', na_rep=None, attr_cols=None, elem_cols=None,
    # namespaces=None, prefix=None, encoding='utf-8', xml_declaration=True,
    # pretty_print=True, parser='lxml', stylesheet=None, compression='infer',
    # storage_options=None)

    try:
        if Path is None:
            raise ValueError('Please specify a path!')

        if filename[-4:].lower() != '.xml':
            filename = filename + '.xml'

        filepath = os_path.join(Path, filename)
        df.to_xml(filepath, index=False, root_name="createTours")

    except Exception:
        log_exception(popup=True, remarks='Export as xml failed!')