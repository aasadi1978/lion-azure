WorkInProgress: Driver Scheduling - Exact method
===================================================

.. contents::
  :local:
  :depth: 2

.. warning::
    This is a work-in-progress document that presents an exact method for formulating driver scheduling for movements. Please note that this 
    document is still under development and is subject to change. The content provided does not guarantee its correctness.



Abstract
---------

In the logistics and transportation industry, efficiently assigning drivers to truck movements is a critical challenge that directly impacts operational 
costs and service quality. This document addresses the problem of optimal movement-driver assignment, where each movement involves a truck with a predefined 
departure time, origin, and destination. The objective is to minimize the number of drivers utilized, overall idle time, and empty mileage, while adhering 
to a set of business rules and constraints related to labor regulations. These constraints include limits on driving and working hours, mandatory return to the base location, and 
specific break requirements. To solve this problem, we employ a mixed-integer programming (MIP) approach solved using Gurobi optimization software. Our model 
incorporates various real-world constraints such as turn-around times, break schedules, and empty movements. The results demonstrate the effectiveness
of the proposed MIP model in optimizing driver schedules, thereby reducing operational inefficiencies and enhancing the overall performance of the transportation network.

**Keywords:** optimization, mixed integer programming, MIP, driver scheduling, Gurobi

Problem Statement
-----------------

Let a list :math:`M` of loaded movements be given. By definition, a movement refers to a truck with a predefined departure time, origin, and destination. This means that these attributes cannot be modified when modeling. The problem is to find the optimal movement-driver assignment. Every driver can drive multiple movements in one shift. The relationship between drivers and shifts is assumed to be 1-1.

Business Rules and Constraints
------------------------------

- Maximum legal driving time per shift is 9 hours.
- Maximum legal working time per shift is 12 hours.
- Before every departure, a *non-driving turn-around time* is allocated per location to allow the driver to complete paperwork and other tasks. This turn-around time typically lasts for 15 minutes. It is important to note that this time is considered as working time and is taken into account when calculating *period of availability* (POA) of the driver at that location.
- Upon arrival at a location, a *driving turn-around time* is allocated to allow the driver to fully stop. This turn-around time typically lasts for 10 minutes and is considered part of the driver's driving time.
- The last two bullet points are considered constraints for the model, indicating that the driver has to wait at least 25 minutes between two consecutive movements. This 25 minutes is called *turn-around time*.
- Every driver has to come back to his base location after his shift. If the destination of the last movement is not the base location, the driver has to drive empty back to his base location.
- Every shift starts at the driver's base location. This means that if the first loaded movement of a shift is not from the driver's base location, he has to drive empty to the origin of the first movement.
- Each shift begins and ends with a 30-minute debriefing period.
- If it is cost-efficient, empty movements can be added to extend the shift of a driver. This means that once a driver arrives at the destination of a loaded movement, he can drive empty to the location of the next loaded movement.

Model
-------

Sets
----

- :math:`M`: Set of movements
- :math:`M^\prime`: Set of empty movements
- :math:`L`: Set of locations
- :math:`S`: Set of shifts. We can assume that the number of shifts does not exceed the number of loaded movements, i.e., :math:`|S| \leq |M|`

Parameters
----------

- :math:`t_m^{dep}`: Departure time of movement :math:`m`
- :math:`o_m`: Origin location of movement :math:`m`
- :math:`d_m`: Destination location of movement :math:`m`
- :math:`t_{m}^{drive}`: Driving time for movement :math:`m`
- :math:`c_m`: Cost of movement :math:`m`
- :math:`t_{loc}^{poa}`: Non-driving turn-around time (15 minutes)
- :math:`t_{loc}^{driving}`: Driving turn-around time (10 minutes)
- :math:`c_{ij}^{empty}`: Cost of driving empty from location :math:`i` to location :math:`j`
- :math:`t_{ij}^{empty}`: Driving time for empty movement from location :math:`i` to location :math:`j`
- :math:`n_l`: Number of available drivers at location :math:`l`


Decision Variables
------------------

- :math:`x_{lm}`: Binary variable equal to 1 if a driver at location :math:`l` is assigned to movement :math:`m`
- :math:`x_{m}`: Binary variable equal to 1 if loaded movement :math:`m` is scheduled, otherwise 0
- :math:`y_{lij}`: Binary variable equal to 1 if a driver at location :math:`l` drives empty from location :math:`i` to location :math:`j`
- :math:`s_{ij}`: Binary variable equal to 1 if shift :math:`i` departs from location :math:`j`, 0 otherwise
- :math:`S_j`: Binary variable equal to 1 if shift :math:`j` is utilized, 0 otherwise
- :math:`t_{shift}^{start_l}`: Continuous variable representing the start time of the shift for a driver at location :math:`l`
- :math:`t_{shift}^{end_l}`: Continuous variable representing the end time of the shift for a driver at location :math:`l`
- :math:`t_{empty}^{start_lij}`: Continuous variable representing the start time of the empty movement for a driver at location :math:`l` from location :math:`i` to location :math:`j`
- :math:`t_{empty}^{end_lij}`: Continuous variable representing the end time of the empty movement for a driver at location :math:`l` from location :math:`i` to location :math:`j`
- :math:`u_l`: Binary variable equal to 1 if a driver at location :math:`l` is utilized in any shift, 0 otherwise

Objective Function
------------------

Minimize the total number of utilized drivers, overall idle time, and empty mileages:

.. math::

    \min \sum_{l \in L} u_l + \alpha \sum_{l \in L} \left( t_{shift}^{end_l} - t_{shift}^{start_l} - \sum_{m \in M} t_{m}^{drive} x_{lm} - \sum_{i \in L} \sum_{j \in L} t_{ij}^{empty} y_{lij} \right) + \beta \sum_{l \in L} \sum_{i \in L} \sum_{j \in L} c_{ij}^{empty} y_{lij}

where :math:`\alpha` and :math:`\beta` are weighting factors to balance the importance of idle time and empty mileage.

Constraints
-----------

Movement Assignment
~~~~~~~~~~~~~~~~~~~

Each movement must be assigned to exactly one shift:

.. math::

    \sum_{j \in S} x_{mj} \leq x_m, \quad \forall m \in M

If a movement is assigned to a shift, the shift must be utilized:

.. math::

    \sum_{m \in M} x_{mj} = S_j, \quad \forall j \in S

If a shift is utilized, the shift must be assigned to at least one driver location:

.. math::

    \sum_{l \in L} s_{lj} = S_j, \quad \forall j \in S


Shift Duration
~~~~~~~~~~~~~~

Ensure the shift duration does not exceed 12 hours:

.. math::

    S_{j}^{end} - S_{j}^{start} \leq 12, \quad \forall j \in S

Driving Time
~~~~~~~~~~~~

Total driving time within a shift must not exceed 9 hours:

.. math::

    \sum_{m \in M} t_{m}^{drive} x_{mj} + \sum_{i \in L} \sum_{j \in L} t_{ij}^{empty} y_{lij} \leq 9, \quad \forall j \in S

Working Time
~~~~~~~~~~~~

Total working time (including non-driving turn-around time) within a shift must not exceed 12 hours:

.. math::

    \sum_{m \in M} (t_{m}^{drive} + t_{loc}^{poa}) x_{lm} + \sum_{i \in L} \sum_{j \in L} (t_{ij}^{empty} + t_{loc}^{poa}) y_{lij} \leq 12, \quad \forall l \in L

Base Location
~~~~~~~~~~~~~

Ensure that each shift starts and ends at the driver's base location:

.. math::

    t_{shift}^{start_l} = t_{m}^{dep} - (t_{m}^{drive} + t_{loc}^{poa} + t_{loc}^{driving}), \quad \forall l \in L \text{ if the first movement } m \text{ is not from base location}

.. math::

    t_{shift}^{end_l} = t_{m}^{dep} + t_{m}^{drive} + t_{loc}^{poa} + t_{loc}^{driving}, \quad \forall l \in L \text{ if the last movement } m \text{ is not to base location}

Turn-Around Time
~~~~~~~~~~~~~~~~

Enforce a minimum turn-around time of 25 minutes between consecutive movements:

.. math::

    t_{m}^{dep} - (t_{m'}^{dep} + t_{m'}^{drive} + t_{loc}^{driving}) \geq 25, \quad \forall l \in L, \forall m, m' \in M \text{ where } x_{lm} = 1 \text{ and } x_{lm'} = 1

Empty Movements
~~~~~~~~~~~~~~~

Generate and schedule empty movements if cost-efficient:

.. math::

    t_{empty}^{start_lij} = t_{m}^{dep} + t_{m}^{drive} + t_{loc}^{driving}, \quad \forall l \in L, \forall m \in M \text{ if } y_{lij} = 1 \text{ and } d_m = i

.. math::

    t_{empty}^{end_lij} = t_{empty}^{start_lij} + t_{ij}^{empty}, \quad \forall l \in L, \forall i, j \in L \text{ if } y_{lij} = 1

Driver Utilization
~~~~~~~~~~~~~~~~~~

Link driver utilization to the assignment of movements:

.. math::

    u_l \geq x_{lm}, \quad \forall l \in L, \forall m \in M

Driver Availability
~~~~~~~~~~~~~~~~~~~

Ensure the number of utilized drivers does not exceed the available drivers at each location:

.. math::

    \sum_{m \in M} x_{lm} \leq n_l, \quad \forall l \in L


Gurobi
-------

.. code-block:: python

    import gurobipy as gp
    from gurobipy import GRB

    # Create a new model
    model = gp.Model("SequentialMovements")

    # Example sets and parameters (replace with actual data)
    L = ["l1", "l2"]  # Locations
    M = ["m1", "m2", "m3"]  # Movements
    origins = {"m1": "loc1", "m2": "loc2", "m3": "loc3"}  # Movement origins
    destinations = {"m1": "loc2", "m2": "loc3", "m3": "loc1"}  # Movement destinations

    # Decision variables
    x = model.addVars(L, M, vtype=GRB.BINARY, name="x")
    z = model.addVars(L, M, M, vtype=GRB.BINARY, name="z")

    # Big-M value (should be large enough to enforce the constraint, replace with an appropriate value)
    M_value = 10000

    # Adding the sequential movement constraints
    for l in L:
        for m in M:
            for m_prime in M:
                if m != m_prime:
                    # z[l, m, m'] can only be 1 if both x[l, m] and x[l, m'] are 1
                    model.addConstr(z[l, m, m_prime] <= x[l, m], name=f"z_x1_{l}_{m}_{m_prime}")
                    model.addConstr(z[l, m, m_prime] <= x[l, m_prime], name=f"z_x2_{l}_{m}_{m_prime}")
                    model.addConstr(z[l, m, m_prime] >= x[l, m] + x[l, m_prime] - 1, name=f"z_x3_{l}_{m}_{m_prime}")
                    
                    # Big-M constraints to enforce the origin-destination constraint
                    model.addConstr((origins[m_prime] == destinations[m]) * z[l, m, m_prime] <= M_value, name=f"od_{l}_{m}_{m_prime}")

    # Add other constraints and objective as needed

    # Optimize the model
    model.optimize()
