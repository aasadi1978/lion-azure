import logging
from pathlib import Path
from gurobipy import GRB, Model, GurobiError, gurobi as gb
from os import getenv


remarks = """

Issue I:
In the case of M&S expiration consult the ticket number #57851.
Make sure the right version of gurobi is installed.

import gurobipy as gp
print(gp.gurobi.version())

While gurobi_cl corresponds to version 10.0.1, you have version 10.0.3 of gurobipy 
installed into your Python environment. You can confirm this in Python as follows:
import gurobipy as gp

print(gp.gurobi.version())
 
To resolve the error, you can downgrade your gurobipy version to 10.0.1. If you use pip 
as a package manager, you can uninstall gurobipy version 10.0.3 and install gurobipy version 10.0.1 as follows:

python -m pip uninstall gurobipy
python -m pip install gurobipy


Issue II: Gurobi maintenance expired: In this case, log in Gurobi account and execute 

grbgetkey 72d254dc-xxxx-xxxx-xxxx-xxxxxxxxxx

The key could be updated every year.
_________________________________
"""


def verify_gurobi_installation():
    # Solve the following MIP:
    #  maximize
    #        x +   y + 2 z
    #  subject to
    #        x + 2 y + 3 z <= 4
    #        x +   y       >= 1
    #        x, y, z binary


    if not Path(getenv('GUROBI_HOME')).exists():
        logging.error("GUROBI_HOME path does not exist!")
        return False

    try:
        # Create a new model
        m = Model(name="TestMIP")

        # Create variables
        x = m.addVar(vtype='B', name="x")
        y = m.addVar(vtype='B', name="y")
        z = m.addVar(vtype='B', name="z")

        # Set objective function
        m.setObjective(x + y + 2 * z, GRB.MAXIMIZE)

        # Add constraints
        m.addConstr(x + 2 * y + 3 * z <= 4)
        m.addConstr(x + y >= 1)

        # Solve it!
        m.optimize()

        logging.info(f"Gurobi Test Model: {m.objVal}")
        logging.info(f"Gurobi Test Model Solution values: x={x.X}, y={y.X}, z={z.X}")

    except GurobiError as e:
        logging.error(f"Gurobi error: {str(e)}")
        return False

    except Exception as e:
        logging.error(f"Gurobi exception: {str(e)}")
        return False
    
    logging.info(f"Gurobi Test passed.")
    return True


def gb_version():
    try:
        return f'Gurobi {gb.version()}'
    except Exception:
        return 'No version'


if __name__ == '__main__':
    print(f"Gurobi is active: {verify_gurobi_installation()}")

