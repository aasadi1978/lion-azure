"""
This module is the entry point to initialize Flask app

.. code-block:: python

    pr_user_sqldb_path = os_path.join(LION_HOME_PATH, 'sqldb')
    if not os_path.exists(pr_user_sqldb_path):
        mkdir(pr_user_sqldb_path)

    pr_lion_user_db = os_path.join(pr_user_sqldb_path, 'lion.db')
    if not os_path.exists(pr_lion_user_db):
        pr_lion_user_db_tmp = os_path.join(LION_SHARED_ASSETS_PATH, 'lion.db')
        copyfile(pr_lion_user_db_tmp, pr_lion_user_db)

    pr_lion_master_data_db = os_path.join(
        pr_user_sqldb_path, 'lion_shared_data.db')

    if not os_path.exists(pr_lion_master_data_db):
        pr_lion_master_data_db = os_path.join(
            LION_SHARED_ASSETS_PATH, 'lion_shared_data.db')


- **loc_params**: This table is generated automatically during optimization process which mainly contains number of employed and subcontractor drivers per Fedex facility
- **pickle_dumps**: Intermediate pick dumps to speedup data read such as runtimes and mileages
- **resources**: The list of drivers, both subco and employed, per location provided by user
- **time_stamp**: A table wherein timestamp of some files are stored to check various update requirements of clean up process
- **user_params**: A table containing user specific parameters


.. code-block:: sql

   CREATE TABLE users (
       user_id INT PRIMARY KEY
   );

The method docstring begins with a brief description of what the optimize_route method does.
:param network_data: and :type network_data: describe the parameter and its type.

"""
