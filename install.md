# Installation Instructions

## Software

* create venv
* clone repo
* install packages `pip install -r requirements.txt`
* move config directory up one level
	* set user as config directory owner 
	* `sudo chown pi:pi config`
	* `sudo chown pi:pi config/config.json`
	* `sudo chown pi:pi config/devices.json`
* make the data directory one level up
	* `mkdir data`

### Automation
Make scripts executable
`chmod +x smartPowerStation/services/api.py`
`chmod +x smartPowerStation/services/ble_logger.py`

Copy service files
`sudo cp smartPowerStation/services/api.service /etc/systemd/system/api.service`
`sudo cp smartPowerStation/services/ble_logger.service /etc/systemd/system/ble_logger.service`

Reload and enable
`sudo systemctl daemon-reexec`
`sudo systemctl daemon-reload`
`sudo systemctl enable api.service`
`sudo systemctl start api.service`
`sudo systemctl enable ble_logger.service`
`sudo systemctl start ble_logger.service`

Check if its running
`sudo systemctl status api.service`
`sudo systemctl status ble_logger.service`

Set daily reboot
`sudo crontab -e`<br>
Add this line at the bottom of the file `0 3 * * * /sbin/reboot`

### Smart Power Station

### Bluetti

Clone the repository `git clone https://github.com/alexnathanson/bluetti_mqtt`

Navigate to the bluetti_mqtt directory and run `pip install .`

