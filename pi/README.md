# Pi Subsystem README

# Overview

The Pi subsystem runs on the Raspberry Pi and is responsible for direct hardware control. It executes commands received from the Host and translates them into motor movements, sensor reads, and physical actions.
This subsystem acts as the bridge between software and electronics.

# Responsibilities

The Pi subsystem handles:
    - Motor control (movement and focus)
    - Sensor data acquisition
    - Real-time hardware interaction
    - Executing commands from the Host
    - Sending feedback/state data back to the Host

# Directory Structure

main.py: 
    - System entry point
    - Starts the Pi program
    - Initializes hardware
    - Runs the main control loop
    - Connects comms → control → hardware

config/:
Contains values that never change at runtime:
    - GPIO pins
    - Motor IDs
    - Angle limits
    - Speed limits
    - Loop rates

comms/:
Contains values that never change at runtime:
    - GPIO pins
    - Motor IDs
    - Angle limits
    - Speed limits
    - Loop rates

control/:
    - The execution brain of the Pi
    - Translates commands → actions
    - Enforces safety limits
    - Coordinates multiple motors

hardware/:
This is the only place that touches pins.
    - Lowest-level hardware access
    - Motor drivers
    - Sensors
    - GPIO setup

state/:
    - Tracks current system status
    - Telescope position
    - Motion state
    - Error conditions

    Used for:
        - Feedback to Host
        - Safety checks

utils/:
Reusable helpers:
    - Logging
    - Timing utilities
    - Debug helpers