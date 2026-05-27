.. _`coordinates`:

Coordinates and time handling
=============================

Dimensional quanitities such as :dd:data_type:`AoS` and multi-dimensional
:ref:`data <data types>` nodes have associated coordinates. Coordinates can
refer to other data quantities in the IDS, which is indicated with the path to
the coordinate quantity. Alternatively, a coordinate can be a plain index, which
is indicated as ``1...N`` when the size of the coordinate is variable or -- for
example -- ``1...3`` when there is a strict number of items -- 3 in this case.

When the path to a coordinate goes through an array of structure and
the index of the array of structure is indicated as (:), it means that the coordinate 
node must have the same size for all indices of its ancestor array of structure.
Example: ``channel(i1)/camera(i2)/frame(:)/apparent_temperature`` in the camera_IR
IDS indicates that ``apparent_temperature`` has the same size for all indices of the 
``frame`` array of structure.

Note that time coordinates are special due to the time slice functionality
of the Access Layer. See the following section for more details.


.. _`time coordinates`:

Time coordinates and time handling
''''''''''''''''''''''''''''''''''

Some quantities (and array of structures) are time dependent.

This time-dependent coordinate is treated specially in the access layer, and it
depends on the value of ``ids_properties/homogeneous_time``. There are three
valid values for this property:

- ``0`` (heterogeneous time mode): time-dependent quantities in the IDS may have
  different time coordinates. The time coordinates are stored as indicated by
  the path in the documentation.
- ``1`` (homogeneous time mode): All time-dependent quantities in this IDS use
  the same time coordinate. This time coordinate is located in the root of the
  IDS, for example :dd:node:`core_profiles/time`. The time paths indicated in
  the documentation are unused in this case.
- ``2`` (time independent mode): The IDS stores no time-dependent data.

.. note::

    The Access Layer provides named constants for the allowed values:
    ``IDS_TIME_MODE_HETEROGENEOUS``, ``IDS_TIME_MODE_HOMOGENEOUS`` and
    ``IDS_TIME_MODE_INDEPENDENT``. See the Access Layer documentation for more
    details.

    .. todo:: link to AL docs
    
    Using these constants is preferred over the raw value: when reading code it
    is easier to understand :code:`ids.ids_properties.homogeneous_time =
    IDS_TIME_MODE_HOMOGENEOUS` then :code:`ids.ids_properties.homogeneous_time =
    1`.


Static, constant and dynamic nodes
----------------------------------

IDS nodes can be 

.. _`type-dynamic`:

Dynamic
    Dynamic quantities are time-dependent in the context of the IDS. They have a
    :ref:`time coordinate <time coordinates>`.

.. _`type-constant`:

Constant
    Constant quantities are not varying within the context of the IDS, such as the code
    that has produced the IDS.

.. _`type-static`:

Static
    Static quantities are also not varying, but likely to be constant over a wider
    context, such as the nominal coil positions during operation.


.. _`dd4-alternatives`:

Alternatives for a coordinate
'''''''''''''''''''''''''''''

Starting with Data Dictionary 4.0, a coordinate can indicate that other data
fields can be used as coordinate instead. For example,
:dd:node:`core_profiles/profiles_1d/grid/rho_tor_norm` indicates that (among
others) :dd:node:`core_profiles/profiles_1d/grid/rho_tor` can be used as an
alternative.

When filling any quantity that has ``rho_tor_norm`` as coordinate (for example
:dd:node:`core_profiles/profiles_1d/t_i_average`), you may choose to fill an
alternative coordinate instead, and leave ``rho_tor_norm`` empty.
