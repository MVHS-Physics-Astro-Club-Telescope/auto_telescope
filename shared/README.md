# Shared Subsystem README

# Overview
The Shared subsystem defines the communication contract between the Host computer and the Raspberry Pi. It ensures both sides agree on how data is structured, sent, and interpreted.

# Responsibilities

The Shared subsystem handles:
    - Command and data structure definitions
    - Message formatting and parsing
    - Communication protocols
    - Shared constants and enums

# Directory Expectations

This directory should contain:
    - Message schemas
    - Shared data models
    - Protocol definitions
    - Communication utilities

# Development Rules (VERY IMPORTANT)

Any change here requires updating both Host and Pi
Coordinate changes with all subsystem owners
Version interfaces carefully