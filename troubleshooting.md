# Troubleshooting

restart bluetooth `sudo systemctl restart bluetooth`


This can reset bluetooth: (might be good to do periodically if running into errors...)
`sudo systemctl restart bluetooth`
`sudo hciconfig hci0 up`
`sudo rfkill unblock bluetooth`
