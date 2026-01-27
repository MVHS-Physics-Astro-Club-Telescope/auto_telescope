# Autonomous Tracking and Capturing Telescope

# Overview

This project is focused on creating a functional telescope by hand that can be adjusted to see celestial bodies and stars far away from our planet. We are limiting ourselves to utilize actual parts rather than prebuilt-telescopes. There are three subsections to the project: Electrical, Mechanical, & Software; Note that Software will be utilizing two coding languages (Java & Python). 

The telescope should autonomously focusing, moving, and tracking on celestial bodies and objects within range and will need minimal human assistance. For this, we will need proper communication across all 3 subsections in order to make sure that the telescope can accurately move based on the commands dictated by the sensors.

# Architecture

Data Flow and Control Flow --> Shared file dictates the flow of these things alongside the overall communication between the Raspberry Pi and the host computer

# Repository Structure

Docs --> Structured documentation on each change/merge in the main branch (more detailed than this file)
Host --> High level computations (i.e. how much to focus, move, or overall adjust the telescope is done in this file)
Pi --> Software-Electronic integration, creating functionality between the electrical components and software commands to create truly autonomous movement based on Host file decision making
Shared --> How data is sent from the host computer to the Pi, communicator between both the computer and the Pi.

# Setup

How to start using or contributing:

Prerequisites: 

Java JDK package
Python 3.11
Working OS