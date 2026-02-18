# Autonomous Tracking and Capturing Telescope

## Overview

This project designs and builds a fully autonomous telescope from individual components, rather than using a prebuilt system. The telescope automatically focuses, moves, and tracks celestial bodies with minimal human input.

The system is divided into three major subsystems:

- **Mechanical** -- Physical structure, mounts, and motion mechanisms
- **Electrical** -- Motors, sensors, and wiring
- **Software** -- Control logic, communication, and automation

The software stack is pure Python. The host computer handles high-level decision-making (celestial math, tracking, autofocus) while the Raspberry Pi controls hardware (motors, sensors, GPIO). A shared protocol layer defines the communication contract between the two.

## Architecture

The telescope operates using a **Host computer <-> Raspberry Pi** architecture:

- The **Host** performs high-level calculations: celestial coordinate resolution (via astropy/astroquery), tracking adjustments (PID control), and autofocus control.
- The **Raspberry Pi** interfaces directly with stepper motors and sensors, executing movement commands with safety checks.
- A **shared** communication layer defines commands, state, and the TCP protocol used to exchange data between Host and Pi.

Commands flow **Host -> Pi**. State feedback flows **Pi -> Host**. Both sides use the shared protocol definitions.

```
┌─────────────────────┐         TCP          ┌──────────────────────┐
│       Host          │  ──── commands ────>  │     Raspberry Pi     │
│                     │                       │                      │
│  - Celestial math   │  <── state reports ── │  - Motor control     │
│  - Tracking (PID)   │                       │  - GPIO / sensors    │
│  - Autofocus        │                       │  - Safety manager    │
│  - CLI interface    │                       │  - Focus controller  │
└─────────────────────┘                       └──────────────────────┘
              │                                         │
              └──────── shared/ protocol layer ─────────┘
```

## Repository Structure

```
auto_telescope/
├── host/                  # Host computer -- high-level control
│   ├── main.py            # TCP server, CLI entry point
│   ├── config/            # Constants, UI params
│   ├── control/           # Tracking, PID, autofocus, celestial resolution
│   ├── comms/             # TCP sender/receiver to Pi
│   ├── state/             # Telescope state store, session logs
│   ├── ui/                # CLI interface, display formatting
│   ├── simulation/        # Testing without hardware
│   └── utils/             # Logger, math, threading helpers
├── pi/                    # Raspberry Pi -- hardware control
│   ├── main.py            # Hardware init, 50Hz dispatch loop
│   ├── config/            # Constants, GPIO pin mappings
│   ├── control/           # Motor controller, focus, safety manager
│   ├── hardware/          # GPIO setup, motor driver, sensors
│   ├── comms/             # TCP client, message parser
│   ├── state/             # Position tracking, error state
│   └── utils/             # Logger, timer, debug
├── shared/                # Communication contract (Host <-> Pi)
│   ├── commands/          # Move, Focus, Stop command definitions
│   ├── enums/             # CommandType, StatusCode
│   ├── errors/            # ErrorCode definitions
│   ├── protocols/         # TCP protocol (4-byte length-prefixed JSON), validator
│   └── state/             # TelescopeState, CameraState
├── tests/                 # Test suite (328 tests)
│   ├── host/              # Host unit tests (148)
│   ├── pi/                # Pi unit tests (86)
│   ├── shared/            # Shared unit tests (69)
│   └── integration/       # End-to-end Host<->Pi tests (25)
├── docs/                  # Architecture docs, progress log
├── .github/workflows/     # CI pipeline
└── requirements.txt       # astropy, astroquery, pytest
```

## Setup

### Prerequisites

- Python 3.9+
- Raspberry Pi (for hardware deployment; mock hardware available for development)

### Installation

```bash
git clone https://github.com/MVHS-Physics-Astro-Club-Telescope/auto_telescope.git
cd auto_telescope
pip install -r requirements.txt
```

### Running

**Host (with simulation mode -- no Pi needed):**
```bash
export PYTHONPATH=$PWD:$PYTHONPATH
python3 -m host.main --simulate
```

**Host (connecting to a real Pi):**
```bash
python3 -m host.main --host 0.0.0.0 --port 5050
```

**Pi (with mock hardware -- no GPIO needed):**
```bash
python3 pi/main.py --mock --host <host-ip>
```

**Pi (with real hardware):**
```bash
python3 pi/main.py --host <host-ip>
```

### Running Tests

```bash
export PYTHONPATH=$PWD:$PYTHONPATH
pytest tests/ -v
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.9+ |
| Celestial math | astropy, astroquery (SIMBAD, JPL Horizons) |
| Hardware I/O | RPi.GPIO (on Pi only) |
| Communication | TCP sockets (4-byte length-prefixed JSON) |
| Testing | pytest (328 tests) |
| CI | GitHub Actions (Python 3.9, 3.10) |
