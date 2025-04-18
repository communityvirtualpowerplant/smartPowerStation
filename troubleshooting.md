# Troubleshooting

restart bluetooth `sudo systemctl restart bluetooth`


This can reset bluetooth: (might be good to do periodically if running into errors...)
`sudo systemctl restart bluetooth`
`sudo hciconfig hci0 up`
`sudo rfkill unblock bluetooth`

## Error Logs

error logs from services can often be found here: `nano /var/log/syslog`

or 

`journalctl -u your-service-name.service`


## Check is a python program is running:
`ps aux | grep .py`

## Memory

`free -h`