# DIDComm Examples

This repository contains examples and implementations related to DIDComm (Decentralized Identifier Communication) messaging.

## Project Structure

```
/repos/DIDCommExamples
├── requirements.txt
├── router.py
├── threadrouting.py
└── .gitignore
```

### Key Files

- `requirements.txt`: Contains the project dependencies
- `router.py`: Implements the main routing logic for DIDComm messages
- `threadrouting.py`: Likely implements thread routing functionality for DIDComm

## Setup and Installation

1. Ensure you have Python 3.7+ installed on your system.

2. Clone this repository:
   ```
   git clone https://github.com/your-username/DIDCommExamples.git
   cd DIDCommExamples
   ```

3. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Code

The repository doesn't contain a main entry point or specific instructions for running the code. The `router.py` file contains a `MessageRouter` class that seems to be the core component for routing DIDComm messages.

To use this code in your project:

1. Import the necessary classes from `router.py`:
   ```python
   from router import MessageRouter, NamedFunctionHandler
   ```

2. Create an instance of `MessageRouter` with a scheduler:
   ```python
   scheduler = YourSchedulerImplementation()
   router = MessageRouter(scheduler)
   ```

3. Add routes and register handlers as needed:
   ```python
   @router.add_message_route("your_message_type")
   async def handle_message(msg, context):
       # Your message handling logic here
       pass
   ```

4. Use the `route_message` method to route incoming messages:
   ```python
   await router.route_message(your_message)
   ```

## Testing

There are no specific test files or instructions provided in the repository. It's recommended to create unit tests for the `MessageRouter` and `NamedFunctionHandler` classes to ensure proper functionality.

## Contributing

As this is an example repository, there are no specific contribution guidelines. However, if you'd like to improve or extend the examples, feel free to fork the repository and submit pull requests.

## License

No license information is provided in the repository. Please contact the repository owner for more information about usage and distribution rights.