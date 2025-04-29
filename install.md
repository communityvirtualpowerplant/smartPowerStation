# Installation Instructions

## Software

### Configure OS

#### Raspi Config
* protect boot partition
* locales:
	* set en_US.utf8, timezone, wireless
* expand filesystem

#### Update
* `sudo apt-get update`
* `sudo apt-get upgrade`
* `sudo reboot`

### Install SPS
* clone repo `git clone https://github.com/communityvirtualpowerplant/smartPowerStation.git`
* create venv in SPS directory `python -m venv venv`
* clone bluetti repo into pi
	* `cd /home/pi`
	* `git clone https://github.com/alexnathanson/bluetti_mqtt.git`
	* Navigate to the bluetti_mqtt directory and run while in venv `pip install .` (not needed if directory is same as in requirements file)
* install packages `pip install -r requirements.txt`
* move config directory up one level
	* `cp -r config ../config`
* confirm config directly own is pi with `ls -l`. If not, set owner and group:
	* set user as config directory owner 
	* `sudo chown pi:pi config`
	* `sudo chown pi:pi config/config.json`
	* `sudo chown pi:pi config/devices.json`
	* `sudo chown pi:pi config/rules.json`
* make the data directory one level up
	* `mkdir data`

#### Configure SPS
* update config and rules files as needed
* Run ble_discover and check that devices file is formatted properly and all relevant devices were discovered
* create environmental variables file in SPS directory:
	* `nano .env` with `AIRTABLE_PARTICIPANTS=`

### Automation

Copy service files
`sudo cp smartPowerStation/services/api.service /etc/systemd/system/api.service`
`sudo cp smartPowerStation/services/device_manager.service /etc/systemd/system/device_manager.service`
`sudo cp smartPowerStation/services/sps_controls.service /etc/systemd/system/sps_controls.service`

Reload and enable
`sudo systemctl daemon-reexec`
`sudo systemctl daemon-reload`
`sudo systemctl enable api.service`
`sudo systemctl start api.service`
`sudo systemctl enable device_manager.service`
`sudo systemctl start device_manager.service`
`sudo systemctl enable sps_controls.service`
`sudo systemctl start sps_controls.service`

Check if its running
`sudo systemctl status api.service`
`sudo systemctl status ble_logger.service`

Set daily reboot
`sudo crontab -e`<br>
Add this line at the bottom of the file to restart the server at midnight `@midnight sudo reboot`

#### participation maintenance:

daily partition maitenance: `sudo tune2fs -c 1 /dev/mmcblk0p2`

### Smart Power Station


### Install troubleshooting:

Not necessary if owned and run by pi user, but worth checking: make scripts executable
`chmod +x smartPowerStation/services/api.py`
`chmod +x smartPowerStation/services/ble_logger.py`
`chmod +x smartPowerStation/services/sps_controls.py`