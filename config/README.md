# Config Files

## config.json

## devices.json

Position 1: Grid to Load<br>
Position 2: Grid to Battery<br>
Position 3: Battery to Grid<br>
Position 4: PV to Battery

## rules.json

### Connection Modes
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
* Battery connected to load (pos 3) only.
Mode 6:
* All off.
