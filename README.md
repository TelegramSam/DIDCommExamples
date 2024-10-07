# DIDCommExamples

This repository contains examples related to DIDComm (Decentralized Identifier Communication).

## Project Structure

- `router.py`: Contains routing logic for DIDComm messages, including the `NamedFunctionHandler` class for handling named functions.
- `threadrouting.py`: Implements thread routing for DIDComm messages.
- `requirements.txt`: Lists the Python dependencies for this project.

## Development

This project uses Python. Make sure to set up a virtual environment before working on the code:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Code

To run the router example:

```
python3 router.py
```

Note: `threadrouting.py` may take longer to execute or might be waiting for input.

## Contributing

Please ensure that any contributions are appropriate for Python projects and consider cross-platform compatibility.

When making changes, make sure to test your code by running the relevant Python files and update the documentation as necessary.