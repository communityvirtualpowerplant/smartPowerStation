# Controls

## Automation

Control of the Smart Power Station is determined by the following rules:

* battery shouldn't be depleted below 20%
* battery should be cycled daily
* if an event is upcoming, battery should be at 100%
 
This is facilitated with the following methods:
* data logging happens every 3 minutes

### During an event

PI Control to Reach Goal
* 

### Immediately after an event

* if flex capacity is still available after the event, ease back on to grid power

## Data

* Track energy by hour
* Estimate real-time flexible capacity

## Communication


# Connection Modes
Note that if PV is present, it is always connected to battery (pos 4) .

Mode 1:
* Grid connected to load (pos 1) and battery (pos 2).
Mode 2:
* Grid connected to load (pos 1) only.
Mode 3:
* Grid connect to battery (pos 2). Battery connected to load. (pos 3)
Mode 4:
* Grid connected to battery (pos 2) only.
Mode 5:
* Battery connecyed to load (pos 3) only.
