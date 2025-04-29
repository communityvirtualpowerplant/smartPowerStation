# Troubleshooting

restart bluetooth `sudo systemctl restart bluetooth`


This can reset bluetooth: (might be good to do periodically if running into errors...)
`sudo systemctl restart bluetooth`
`sudo hciconfig hci0 up`
`sudo rfkill unblock bluetooth`

## Error Logs

error logs from services can often be found here: `nano /var/log/syslog`

or 
all: `journalctl -u your-service-name.service -f`<br>
recent: `journalctl -u your-service-name.service -f`<br>
5 minutes:`journalctl -u sps_controls.service --since "5 minutes ago"`<br>
live: `journalctl -f`

Add `,flush=True` to force print to troubleshoot

## Check is a python program is running:
`ps aux | grep .py`

## Memory

`free -h`

service usage: `systemd-cgtop`

per core usage: `mpstat -P ALL 1`


## run fsck run on reboot:
should already be installed during install: `sudo tune2fs -c 1 /dev/mmcblk0p2`


### kill the process

`ps aux | grep .py`<br>
force kill: `kill -9 PROCESS_ID#`
