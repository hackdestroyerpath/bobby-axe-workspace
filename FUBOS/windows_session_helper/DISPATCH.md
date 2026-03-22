# Command Dispatch Strategy

## First practical version
The helper sends commands only to session processes that it launched itself and still manages.

## Why
This is more reliable than trying to inject keystrokes into arbitrary external terminal windows by focus-stealing.

## Consequence
To send commands, the session should first be launched/reconnected from inside the helper.
