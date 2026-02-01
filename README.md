# Autonomous Tracking and Capturing Telescope

# Overview

This project focuses on designing and building a fully autonomous telescope from individual components, rather than using a prebuilt system. The telescope is capable of automatically focusing, moving, and tracking celestial bodies with minimal human input.

The system is divided into three major subsystems:
    Mechanical – Physical structure, mounts, and motion mechanisms
    Electrical – Motors, sensors, and wiring
    Software – Control logic, communication, and automation
    The software stack uses Java (host-side control) and Python (Raspberry Pi integration). Reliable communication across all subsystems is essential to ensure accurate tracking and movement.

# Architecture

The telescope operates using a host computer ↔ Raspberry Pi architecture:
    - The host computer performs high-level calculations such as positioning, tracking adjustments, and focus control.
    - The Raspberry Pi interfaces directly with motors and sensors.
    - A shared communication layer defines how data and commands are exchanged between the host and the Pi.

This architecture allows decision-making to remain centralized while hardware control stays close to the electronics.

# Repository Structure

Docs/     → Documentation for changes, merges, and design decisions  
Host/     → High-level control logic (movement, tracking, focus decisions)  
Pi/       → Hardware integration and motor/sensor control  
Shared/   → Communication protocol between Host and Raspberry Pi  

# Setup

Prerequisites: 

- Java JDK
- Python 3.11
- Supported operating system (macOS, Linux, or Windows)
- Raspberry Pi (for hardware deployment)