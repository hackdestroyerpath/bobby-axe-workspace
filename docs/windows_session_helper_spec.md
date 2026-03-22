# Windows Session Helper Spec

## Status
Step 1 of 17.

## Goal
Build a Windows GUI helper for the Boss to manage multiple command/SSH sessions from one application.

The application should let the user:
- maintain several session windows/profiles
- see whether each session is active or inactive
- reconnect inactive sessions
- edit the launch command for each session
- choose one target session
- send a command from one shared input field into the selected session

---

## Core product idea
One desktop app acts as a control panel over several shell/SSH session windows.

The GUI is the operator surface.
The underlying terminals remain the execution surface.

---

## Initial product scope
### Required
- session list
- per-session status
- connect/reconnect
- edit session launch command
- choose target session
- one shared command input
- send command to selected session

### Strongly desired
- visible active/inactive state
- convenient switching between sessions
- independent session cards/rows
- safe re-open of dead sessions

### Not required for first working version
- deep terminal emulation inside the GUI
- full PTY rendering
- transcript persistence beyond basic operator needs
- remote orchestration server

---

## Recommended technical direction
### GUI
- Python
- `PySide6`

Reason:
- strong Windows desktop support
- straightforward packaging later
- flexible widgets/layouts

### Session control model
- launch session windows through Windows shell / PowerShell commands
- keep session profiles in local config
- maintain per-session process metadata where possible

### Packaging
- deliver first as Python app
- optionally package later as `.exe` with PyInstaller

---

## Main UI structure
### Left/primary panel
- session list / session cards
- session name
- status
- connect/reconnect button
- edit button

### Main action area
- selected session indicator
- shared command input field
- `Send` button

### Optional extras later
- last activity
- open window button
- quick duplicate session

---

## Acceptance for Step 1
Step 1 is complete when the product spec and technical direction are fixed enough to start implementation of the real Windows helper.
