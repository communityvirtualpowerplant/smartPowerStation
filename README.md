# Smart Power Station
Smart Power Station is an approach for turning a power station unit into a programmable behind-the-meter energy storage system

A power station is an all-in-one combination of charge controller, battery, and inverter.

This project combines a power station with smart relays and an automated transfer switch.

The basic idea is that devices are assigned to the given position (P1-4). Depending on the hardware used, P1 and P3 can be integrated in the power station. P4 depends on whether or not a solar panel is included in the system.

![image](https://github.com/communityvirtualpowerplant/smartPowerStation/blob/main/assets/smartPowerStation_April28_2025-Hardware.drawio.png)

It is intended to be paired with the Simple Demand Response project.

## Hardware

### Power Station

This project has been tested with Bluetti power stations, because the data can be accessed via bluetooth. At some point, once testing has been conducted, it will be expanded to include other power stations regardless of their level of data access.

### Smart Relays

This project has been tested with Shelly smart relays.

Depending on the wifi network, a cheaper version of this project can be built with Kasa relays.

### Automated Transfer Switch

This project has been tested with 2 automated transfer switches.

Xantrex 8080915 PROwatt SW Auto Transfer Switch
* https://xantrex.com/products/accessories/prowatt-sw-inline-transfer-relay/

Kisae Technology TS15A 15 Amp Transfer Switch
* https://www.amazon.com/KISAE-Technology-TS15A-Transfer-Switch/dp/B00IKVH9UK?pd_rd_w=WwAPt&content-id=amzn1.sym.528bfdfa-ea96-478b-a7d9-043e650836af&pf_rd_p=528bfdfa-ea96-478b-a7d9-043e650836af&pf_rd_r=7S8SP234TRCGHAMK5YH0&pd_rd_wg=m32Hv&pd_rd_r=89711aea-1535-480e-9d92-6e88c4f0dc17&pd_rd_i=B00IKVH9UK&psc=1&ref_=pd_basp_d_rpt_ba_s_2_t

### PV Power Sensors

If a solar panel is connected to the power station, an INA260 sensor can be used to measure PV power.

https://www.adafruit.com/product/4226

### Additional Components

* GFCI plug
* 14 AWG wire (this is limted
* Connectors
* Junction Box
  
## Software

### Data

Data is collected from each sensor position and stored locally. Data is shared based on user-preferences.

* Signals from the aggregator are sent via MQTT.
* Data is shared with the aggregator via HTTP.

### Controls

There are three modes
* upcoming event
* ongoing event
* normal/ post-event

In upcoming mode, the system ensures the battery is fully charged by the start of the event.
During an event, the system attempts to meet a given reduction goal based on user preferences.
Normal mode cycles the battery daily.

### UX

* Specify level of data sharing
* specifiy response preferences

## Demand Response Event Methods

Replacement
Shifting
Curtailment


# To Do

* Control specific states
* MQTT Handler
* Post data
* Event
	* PI control
	* Track avoided energy
	* Event goals
		* Align to estimated baseline
		* Minimize energy

## Later
* predict event based on temperature