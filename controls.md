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