.. _search_portal:

SearchPortal
=============

.. imagepath:: /search-portal-2.png
   :width: 940
   :height: 120

.. Scenario-Dropdown
.. --------------------
.. .. imagepath:: /scn-dropdown.png
..    :width: 940
..    :height: 300

.. On click, the list of all scenarios available in *LION_HOME\\Scenarios* will be displayed. User can select a scenario to import in the app.
.. These scenarios, with extension of *.lion* can be distributed with a user with LION app installed. The *.lion* file must be located in user's
.. *LION_HOME\\Scenarios* to be able to see in the scenario drop-down list.

MasterPlan-Dropdown
--------------------
.. imagepath:: /master-plan-dropdown.png
   :width: 940
   :height: 300

On click, the list of all master plans available in *LION_SHARED_DIR\\MasterPlanFiles* will be displayed, sorted based of creation timestamp. 
These master plans is visible for all users, and no distribution is required. The final driver plan is generated using master plan which 
is shared with stations, hubs and other stakeholders, including ROCS team.

Shift string-Dropdown
---------------------
.. imagepath:: /shift-string-dropdown.png
   :width: 940
   :height: 300

A list of movements and corresponding shifts are available to select from in the case user is interested in a subset of the schedule
running certain lane, managed by certain location, etc. Type your keyword in the search bar and then select from the proposed options
within the drop-down list. The press *Load data* to load underlying shifts

Movement bucket-Dropdown
------------------------
**Pending Movements for Scheduling**: 

In the scheduling process, you may encounter movements that haven't been planned yet. These movements are 
accessible for manual intervention in the *Movements Bucket* dropdown list. Once a movement is selected, it will be transferred to the "Movement Dump" 
area.

**Key Points**:

- *Unique Identification*: Each movement in LION is associated with a distinct digital movement ID.
- *Movement Management*: Transferring a movement to the Movement Dump area will remove it from the list of unplanned movements.

.. - *Scheduling and Replication*: After scheduling a movement, you have the option to use :ref:`apply_weekly_changes` function.
..    This allows you to replicate the schedule for the remainder of the week. However, it's important to note that replication is based on the 
..    shift ID. Consequently, if there's a shift on the target day with the same name but different movement configurations, it will be replaced 
..    by the new shift along with its movements.

Please ensure careful handling of movements to maintain an efficient and error-free scheduling process.

Changeovers-Dropdown
----------------------
List of changeovers available in the selected wekkday. After selection of a changeover from the list, the underlying shifts 
carrying the selected changeover will be loaded by pushing the button *Load data*. 

Load data-button
------------------
This button loads the schedule based on the filters set by user. To provide user with flexibility in filtering data, user has to manually
set and clear undesired filters before loading data (pushing *Load data* button).

My basket-button
------------------
This button can be used to collect a list of shifts for processing. User can hold ``CTRL`` key and select the shifts to be processed.

.. imagepath:: /ctrl-selected-shifts.png
   :width: 940
   :height: 300

Once done with selection, this button can be pressed to send the selected shifts into the basket. If there are already shifts in the 
basket, the total number shifts in basket will be displayed on the button (In the example above, although four shifts are selected, 
but we see five on the button as there was already a shift in the basket).

**NOTE**: If no shift is selected by user, and the button is pressed, all of the shifts on the current page will be added to the basket

Load basket-button
------------------
Once user was done with adding shifts to the basket, this button can be used to load all shifts in the basket.

Empty basket-button
-------------------
Delete all shifts from the basket. Please note that no shift or movement will be deleted from the schedule.

Utilisation-Slider
-------------------
.. imagepath:: /utilisation-slider.png
   :width: 940
   :height: 300

This slider can be used to set filter on the shifts with a certain range of utilisation. By definition, *Utilisation* is the total loaded movements driving time
divided by the entire shift. For example, the shift *AE4.S9* belew, has only one loaded movement from *EMA* to *LHR* which is 2 hours and 40 minutes driving time.
Considering that the total shift is 12 hours, the utilisation of *AE4.S9* will then be ``22%``.

.. imagepath:: /utilisation-example.png
   :width: 940
   :height: 300

.. _runtimes_scn_dropdown:

Runtimes Data Set
-------------------
Given the presence of multiple mileage and runtime scenarios influenced by various parameters, including maximum speed, the user has the option to select a specific scenario for analysis and scheduling. This enables the 
examination of the effects related to the chosen scenario. For instance, by recreating a schedule assuming a maximum speed of 44 mph, the user can assess its impact on the 
required number of drivers and the overall network cost.