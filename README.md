# home-auto

I was bored of apps that didn't work reliably, cloud systems that don't work without internet, or systems like HomeAsistant that are too complex (to me) to setup.

Built mostly in two evenings, so the code is not that great. I share it mainly for the Gnome extension code since I didn't find many examples.

This let's me:

- turn off the light of my office from a remote button on my couch
- turn off all the lights from another button
- turn off all the lights at 9AM (when I go out for work, the price of electricity is increasing!)
- control all the lights from a simple GNOME shell extension
- have also an HTTP API

This is composed of this hardware:

- 2x Shelly 2.5 to control office and bedroom lights
- 1x Shelly 1 Plus to control bathroom light (pay attention to the changed API on the new version that is not well documented)
- 1x Shelly i3 (3 input channels) for the 2 remote buttons
- a Raspberry Pi 3 that was collecting dust in a drawer

On the raspberry there is a MQTT server (Mosquitto server) and a Flask application that exposes the HTTP API, and does some stuff processing the inputs from the buttons and manages the schedule.

Then the GNOME shell extension code simply calls the HTTP API, polling it every 10 seconds to update the button state, and sending on/off commands.
