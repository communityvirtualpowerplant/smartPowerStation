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

### Smart Power Station

### Bluetti

Clone the repository `git clone https://github.com/alexnathanson/bluetti_mqtt`

Navigate to the bluetti_mqtt directory and run `pip install .`

## Troubleshooting

error logs from services can often be found here: `nano /var/logs/syslog`