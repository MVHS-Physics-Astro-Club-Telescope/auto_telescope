# Host Subsystem README

# Overview

The Host subsystem is responsible for all high-level decision making in the autonomous telescope system. It runs on the host computer and determines how the telescope should move, focus, and track celestial objects based on incoming data.
This subsystem does not directly control hardware. Instead, it computes commands and sends them to the Raspberry Pi via the Shared communication layer.

# Responsibilities

The Host subsystem handles:
    - Target selection and tracking logic
    - Position, velocity, and focus calculations
    - Error correction and adjustment logic
    - Sending structured commands to the Pi
    - Receiving sensor/state feedback from the Pi
    - Auto-focus correction logic

# Development Notes

Always keep Host logic hardware-agnostic
Do not hardcode Pi-specific values
Changes here often affect system-wide behavior

# Directory Structure
main.py
    Initializes all modules
    Launches threads for UI, tracking loop, autofocus, and communication
    Coordinates safe shutdown and error handling

config/
    Holds constants and tuning parameters, both general and UI-specific

ui/
    Handles manual/auto input
    Updates the display in real-time
    Reads input from keyboard or mouse

control/
    Core algorithms for tracking and focus
    Computes corrections based on Pi state and camera feedback
    Works entirely hardware-agnostic

comms/
    Interfaces with Pi via Shared definitions
    Ensures all commands and feedback are valid
    Acts as the “messenger” between Host and Pi

state/
    Keeps full telescope state
    Logs movements, commands, and errors for debugging
    
simulation/
    Allows testing of control and focus algorithms without connecting the Pi
    Provides mock targets and camera frames
    
utils/
    General-purpose helpers
    Logging, math, threading utilities