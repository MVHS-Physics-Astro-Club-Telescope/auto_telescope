# Shared Subsystem README

# Overview
The Shared subsystem defines the communication contract between the Host computer and the Raspberry Pi.
It ensures that both sides agree on how data is structured, sent, and interpreted. This includes all command types, state feedback, error codes, and protocol rules.
All communication between Host and Pi must reference this directory. It acts as the single source of truth for message formats and constants.

# Responsibilities
The Shared subsystem is responsible for:
Command definitions: Standard structures for Host → Pi commands (move, focus, stop, etc.)
State definitions: Standard structures for Pi → Host feedback (position, focus, camera info, status)
Message formatting and parsing: Serialization/deserialization for TCP communication
Communication protocols: Port numbers, maximum message sizes, and validation rules
Shared constants and enums: Error codes, command types, status codes

# Directory Expectations
This directory should include:
Message schemas / data models
Protocol definitions
Helper utilities for validation, serialization, and deserialization
Shared constants / enumerations
Important: No hardware-specific logic or direct communication handling should exist outside of helpers. Shared only defines contracts and helpers for using them.

# Development Rules (VERY IMPORTANT)
Any change requires coordination
Both Host and Pi must be updated to reflect any changes in message structures, enums, or constants.
Version interfaces carefully
Keep track of versions to avoid breaking communication.
Add deprecation notes if older fields are removed.
Do not implement system logic here
Shared only defines messages, constants, enums, and protocol helpers.

# Directory Structure

commands/
    Contains definitions of all Host → Pi commands, such as movement, focus adjustments, and emergency stop commands.
state/
    Contains definitions of all Pi → Host feedback, including telescope position, focus data, camera data, and status information.
errors/
    Contains standardized error codes and descriptions shared between Host and Pi.
protocols/
    Contains helpers for TCP communication, including message serialization, deserialization, validation, and protocol constants.
enums/
    Contains enumerations for command types, status codes, and other shared constants to avoid “magic strings.”

# Notes on Usage
Always import definitions from Shared in both Host and Pi to ensure consistency.
Do not hardcode strings or constants from Shared in other code — always reference Shared files.
Protocol helpers (serialization, validation) are provided to simplify TCP communication.
Any update to message fields or enums must trigger updates in both subsystems.