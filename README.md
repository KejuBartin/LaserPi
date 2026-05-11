# LaserPi
LaserPi is a software to turn a projector into a showlaser in combination with a hazer or a fog machine using a Raspberry Pi.

# IMPORTANT:
This does NOT work on Raspberry Pi OS Lite. You WILL get a black screen when the code is running. Raspberry Pi OS Desktop is REQUIRED in order for this software to work properly. You do not need to boot into the desktop environment, it can be disabled but it must be installed.

## Requirements
- `pygame` or `pygame-ce`
- `aalink`

## Control surface
- Open the built-in web UI from another device on the LAN to switch shapes, effects, palettes, BPM, and rotation speed.
- All live inputs update a shared state object, so BPM and OSC integration can hook into the same control path later.

## Additional information
LaserPi is currently under development and nowhere near finished.