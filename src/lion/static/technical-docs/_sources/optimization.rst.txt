Driver Scheduling MIP Formulation
==================================

.. contents::
  :local:
  :depth: 2


.. **Mathematical Module:** https://chatgpt.com/share/2928440c-cd43-4b70-9e2c-af91c38679bf
.. _BFS: https://en.wikipedia.org/wiki/Breadth-first_search

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

Problem statement
-----------------

Let a list :math:`M` of loaded movements be given. By definition, a movement refers to a truck with a predefined departure time, origin and 
destination. This means that these attributes cannot be modified when modeling. The problem is to find the optimal movement-driver assignment.
Every driver can drive multiple movement in one shift. The relationship between drivers and shifts is assumed to be 1-1. 

.. _Business_rules_and_constraints:

- **Business rules and constraints:**

  - Maximum legal driving time per shift is 9 hours.
  - Maximum legal working time per shift is 12 hours.
  - Before every departure, a *non-driving turn-around time* is allocated per location to allow the driver to complete paperwork and other 
    tasks. This turn-around time typically lasts for 15 minutes. It is important to note that this time is considered as working time and is 
    taken into account when calculating *period of availablity* (POA) of the driver on that location.
  - Upon arrival at a location, a *driving turn-around time* is allocated to allow the driver to fully stop. 
    This turn-around time typically lasts for 10 minutes and is considered as part of the driver's driving time.
  - The last two bullet points are considered as constraints for the model which indicates that the driver has to wait at 
    least 25 minutes between two consecutive movements. This 25 minutes is called *turn-around time*
  - Every driver has to come back to his base location after his shift. If the destination of the last movement is not the base location, the driver 
    has to drive empty back to his base location.
  - Every shift starts at driver's base location. This means that if the first loaded movement of a shift is not from driver's base location, he has to drive 
    empty to the origin of the first movement.
  - Each shift begins and ends with a 30-minute debriefing period. This time is considered as working time and included in the calculation of the 
    required working time for breaks.
  - If it is cost efficient, empty movements can be added to extend the shift of a driver. This means that, once driver arrived at the destination of a 
    loaded movement, he can drive an empty to the location of the next loaded movement.
  - According to labor regulations, a 60-minute break must be taken by the driver every 4.5 hours of driving. This means that if a driver drives two 
    consecutive movements and the total driving time, including the driving turn-around time (10 minutes), exceeds 4.5 hours, the driver must take a break 
    between the two movements.
  - According to labor regulations, a 30-minute break must be taken by the driver every 6 hours of working time, unless he has already taken a 60-minute break. 
    This means that if a driver works for 6 hours without taking a 60-minute break, he has to take a 30-minute break. This break can be taken at any location 
    and is considered as working time.
  - If break is required, it has to be provided at a location. This means that the driver cannot take a break on the road and the transfer time 
    between two consecutive movements should be long enough to provide the break, i.e., 60 minutes for driving break and 25 minutes *turn-around time*.

- **Objective:**
  The objective is to run all loaded movements such that the total number of utilized drivers and empty mileages are minimized.

Out of scope
---------------
- **Double-man shifts:** This model assumes that each driver drives alone. Otherwise, majority of the labor regulations are not applicable.
- **Non-Articulated Truck vehicles:** It is assumed that all movements are Artic movement and shifts cannot be splitted into two vehicle types.
- **Fixed shifts:** Any shift fixed by the user


Sets and Indices
-----------------
- :math:`M`: Set of loaded movements
- :math:`D`: Set of driver (base) locations
- :math:`S`: Set of all (feasible) shifts construced using combinations of loaded and empty movements. 
  
.. Note::

  The set :math:`S` is constructed as follows:

  * *Regionize loaded movements:* The best approach to label loaded movements is optimize the full set of movements without adding
    empty movements. This is because the number of loaded movements is usually much smaller than the number of potential empty movements. However,
    the optimization can be executed using small :ref:`modelig parameters <modeling_params>`, e.g., :math:`MaxDownTimeHours=3` and :math:`MaxEmtyHours=3`.
  
  * Once categorization is complete, the set of feasible shifts can be constructed. The set of feasible shifts is the set of all 
    combinations of loaded and empty movements that satisfy the :ref:`business rules related constraints <Business_rules_and_constraints>`. 
    To generate feasible shifts with combinations of loaded and empty movements, the following steps are taken:
    
  * For each category, i.e., driver location:
  
    * generate all empty movements departing from destination location of each loaded movement, 
      departing after 25 minutes and 85 minutes after arrival time of the loaded movement. The number of generated empty movements can be 
      managed using :ref:`modelig parameters <modeling_params>`.

    * Once all loaded and empty movements are generated, a *connection tree* is constructed. The connection tree is a graph, denoted 
      as :math:`G(V, E)`, where :math:`V` is the set of all movements and :math:`E` is the set of connections between movements. A connection 
      between two movements exists if the destination of one movement is the origin of another movement, and the downtime between these movements falls within a 
      user-defined duration. The weight of a connection is determined by the downtime between the movements plus the driving time of the second 
      movement. It is important to note that two empty movements cannot be connected.

    * The connection tree is used to generate all feasible shifts. To this end, we use  *breath first search* (`BFS`_) algorithm to traverse the connection tree. The BFS algorithm starts from a loaded movement and explores all possible paths to construct feasible shifts. When evaluating each shift
      for feasibility, overall cost is calculated by summing the cost of assigning a driver to the shift, i.e., fixed cost, and overall 
      mileage cost. We do not take into account idle time as it is considered as period of availablity which is used to execute other 
      tasks. All genenrated feasible shifts are stored in :math:`S`. 



Parameters
----------

- **Labour Regulations Parameters:**

  - Maximum legal driving time per shift: 9 hours
  - Maximum legal working time per shift: 12 hours

- **Location Parameters:**

  - :math:`d_j`: Number of employed drivers at driver location :math:`j \in D`
  - :math:`D_{j}`: Maximum number of drivers at driver location :math:`j \in D`
  - :math:`c_{ij}`: The variable cost associated with assigning a driver from location :math:`i \in D` to execute shift :math:`j \in S`. Precisely speaking,
    this is the cost of deadheading per shift
  - :math:`C_{i}`: The fix cost associated with hiring an employed driver at location :math:`i \in D` 
  - :math:`C^\prime_{i}`: The fix cost associated with hiring an subcontractor driver at location :math:`i \in D` 

  .. Note:: The number of employed drivers at each location is a parameter that can be used when utilizing all employed drivers is mandatory.
            Any extra drivers at a location can be covered by subcontractors.

.. _modeling_params:

- **Modeling parameters:**

  - :math:`MaxDownTimeHours`: Maximum downtime between consecutive movements, excluding turn-around time: e.g., 3 hours
  - :math:`MaxEmtyHours`:Maximum duration of empty movements, excluding driving turn-around time: e.g., 3 hours

Decision Variables
------------------

- :math:`m_i`: Binary variable indicating whether the loaded movement :math:`i \in M` is scheduled or not.
  
  .. Note:: Ideally, all loaded movements should be scheduled; however, due to constraints, some movements may not be scheduled. This makse
            the problem a *bi-objective* optimization problem, i.e., first maximize the total number scheduled loaded movements, and then minimize the total number 
            of utilized drivers, etc.

- :math:`s_j`: Binary variable indicating whether shift :math:`j \in S` is utilized or not.
- :math:`x_{ij}`: Binary variable indicating whether a driver from location :math:`i \in D` drives the shift :math:`j \in S`.
- :math:`s_{ij}`: Binary variable indicating whether the loaded movement :math:`i \in M` is scheduled in the shift :math:`j \in S`.
- :math:`\epsilon_{i}`: Non-negative Integer variable indicating the number of employed drivers at location :math:`i \in D`.
- :math:`\beta_{i}`: Non-negative Integer variable indicating the number of contractor drivers at location :math:`i \in D`.

  .. Note:: The number of employed drivers at each location is a parameter that can be used when utilizing all employed drivers is mandatory.
            Any extra drivers at a location can be covered by subcontractors.

Mixed integer programming model
-------------------------------

.. math::
   \begin{aligned}
   \text{maximize} \quad & \sum_{i \in M} m_i \\[10pt]
   \text{minimize} \quad & \sum_{i \in D} (C_{i}\epsilon_{i} + C^\prime_{i}\beta_{i}) + \sum_{i \in D,\, j \in S} c_{ij}x_{ij}
   \end{aligned}
   :label: objective_functions


**Subject to**

  .. math::
    \sum_{j \in S} s_{ij} = m_i, \quad \forall i \in M
    :label: mov_constraint

  .. math::
    \sum_{j \in S} x_{ij} = \epsilon_{i} + \beta_{i}, \quad \forall i \in D
    :label: employed_employed_subco_drivers_per_loc
  
  .. math::
    \epsilon_{i} \leq d_{i}, \quad \forall i \in D
    :label: max_employed_drivers_per_loc

  .. math::
    \sum_{i \in D} x_{ij} = s_j, \quad \forall j \in S
    :label: shift_utilized_by_one_driver

  .. math::
    X_i, \, S_j, \, m_i, \, x_{ij}, \, s_{ij} \in \{0, 1\}, \quad \epsilon, \beta \in \mathbb{Z}^{+}

The objective function :eq:`objective_functions` is designed to optimize two objectives: maximizing the total number of scheduled movements 
and (then) minimizing the total number of utilized drivers and empty mileages. The constraint :eq:`mov_constraint` ensures that every movement is assigned to exactly one shift. In constraint :eq:`max_drivers_count`, 
it is ensured that the total number of shifts assigned to each driver location does not exceed the number of drivers. 

The constraint :eq:`shift_utilized_by_one_driver` ensures that if a driver is assigned to a shift, then the shift is utilized by one driver only. 

.. Note::
  This constraint is optional and can be used to ensure that all employed drivers are utilized. If including this constraint makes the 
  model infeasible, sensitivity analysis techniques will be authomatically applied to identify which location(s) 
  should have this constraint relaxed.

In order to ensure that all employed drivers are utilized, the equations :eq:`employed_employed_subco_drivers_per_loc` and :eq:`max_employed_drivers_per_loc` can 
be merged into the following constraints:

  .. math::
    \sum_{j \in S} x_{ij} = d_i + \beta_{i}, \quad \forall i \in D
    :label: employed_drivers_per_loc

To constrain the total number of drivers per location, the following constraint is added:

  .. math::
    \epsilon_{i} + \beta_{i} \leq D_i, \quad \forall i \in D
    :label: max_drivers_count

In the case, it is desirable to enforce the module to utilize all employed drivers, the equation :eq:`max_drivers_count` can be replaced with the following constraint:

  .. math::
    \beta_{i} \geq D_i - d_i, \quad \forall i \in D
    :label: max_drivers_count_I


.. Note::
  The constraints :eq:`employed_drivers_per_loc` and :eq:`max_drivers_count` are optional and can be used to enforce a hard constraint on the total number of (
  employed or total) drivers per location. If including these constraints makes the model infeasible, sensitivity analysis techniques will be authomatically 
  applied to identify which location(s) should have this constraint relaxed.


.. Finally, the constraint :eq:`max_moves_scheduled` ensures that the total number of scheduled movements is maximized. This constraint was added as
.. not all loaded movements could be scheduled under the specified constraints and parameters and forcing all loaded movements to be scheduled could make the model infeasible.
.. To overcome, this issue, the objective function was modified to maximize the total number of scheduled movements before minimizing the total number
.. of drivers utilized.


