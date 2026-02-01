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
//TODO//