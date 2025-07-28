# WebexTools

WebexTools is a toolkit for managing Cisco Webex devices and resources. It provides automation for tasks such as device activation, workspace management, and phone number lookup.

## Project Evolution

WebexTools is evolving from a collection of individual Python scripts to a unified CLI tool. This README covers both approaches:

1. **Original Scripts**: Individual Python scripts for specific tasks (located in the `scripts/` directory)
2. **New CLI Tool**: A unified command-line interface with a consistent structure (located in the `webex-tools/` directory but still under development )

## Features

- **Device Management**: Activate, list, and manage Webex devices
- **Workspace Management**: Create, configure, and rename Webex workspaces
- **User & Number Lookup**: Find users and phone numbers across organizations
- **Batch Operations**: Process multiple items using CSV files
- **Rich Output**: Colorful and well-formatted terminal output
- **Data Validation**: Robust input validation using Pydantic models

## Installation

### Prerequisites

- Python 3.8 or higher
- Git (optional, for cloning the repo)
- Webex API access token

You can check versions by running:
```bash
python --version
git --version
```

### Option 1: Using the Original Scripts

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/byrdnuge/WebexTools.git
   cd WebexTools
   ```

2. **Set Up Dependencies**:
   Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On macOS/Linux
   .venv\Scripts\activate     # On Windows
   ```

   Install required libraries:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Add your Webex API token in the `.env` file:
     ```plaintext
     WEBEX_ACCESS_TOKEN=your_token_here
     ```

### Option 2: Using the New CLI Tool

1. **Clone the Repository** (if not already done):
   ```bash
   git clone https://github.com/byrdnuge/WebexTools.git
   cd WebexTools
   ```

2. **Install using Poetry**:
   ```bash
   cd webex-tools
   poetry install
   ```

3. **Set Up Environment Variables**:
   - Create a `.env` file in the project root:
     ```bash
     echo "WEBEX_ACCESS_TOKEN=your_token_here" > .env
     ```

## Usage

### Original Scripts

The original scripts are located in the `scripts/` directory and can be run directly with Python:

#### Device Activation

```bash
# Activate a single device
python scripts/activate-room-device.py

# Activate devices for multiple users from a CSV file
python scripts/activate_devices_from_csv.py
```

#### Workspace Management

```bash
# Create meeting room workspaces and assign devices
python scripts/create-meeting-device.py

# Create flexible/hotdesking workspaces
python scripts/create-flex-device-space.py

# Rename workspaces based on a CSV file
python scripts/rename-workspace.py
```

#### Lookup Functionality

```bash
# Look up phone numbers across organizations
python scripts/number-lookup.py

# Look up user information
python scripts/UserLookup.py
```

#### Testing

```bash
# Test API connectivity
python scripts/test.py

# Run device-related unit tests
python -m unittest scripts/test_device.py
```

### New CLI Tool

The new CLI tool provides a unified interface with consistent command structure:

```bash
# Show help
webex --help

# List devices
webex devices list

# Activate a device
webex devices activate ACTIVATION_CODE "Device Display Name"

# Activate multiple devices from a CSV file
webex devices activate-batch devices.csv
```

#### CSV Format for Batch Operations

For batch device activation, create a CSV file with the following columns:

```csv
activation_code,display_name,place_id,tags
CODE1,Meeting Room 1,,floor1,building1
CODE2,Meeting Room 2,PLACE_ID_HERE,floor2,building1
```

## Project Structure

```
WebexTools/
├── scripts/                  # Original individual scripts
│   ├── activate_devices_from_csv.py
│   ├── activate-room-device.py
│   ├── create-flex-device-space.py
│   ├── create-meeting-device.py
│   ├── number-lookup.py
│   ├── rename-workspace.py
│   ├── test.py
│   └── UserLookup.py
│
├── webex-tools/              # New CLI tool
│   ├── src/
│   │   └── webex_tools/
│   │       ├── commands/     # CLI command implementations
│   │       ├── models/       # Pydantic data models
│   │       ├── utils/        # Utility functions
│   │       ├── __init__.py   # Package initialization
│   │       └── cli.py        # Main CLI entry point
│   ├── tests/                # Test suite
│   ├── pyproject.toml        # Project configuration
│   └── README.md             # CLI-specific documentation
│
├── .env.example              # Example environment variables
├── requirements.txt          # Dependencies for original scripts
└── README.md                 # This file
```

## Command Structure (CLI Tool)

The CLI tool follows this hierarchical structure:

```
webex-tools
├── devices
│   ├── activate
│   ├── activate-batch
│   └── list
├── workspaces (coming soon)
│   ├── create
│   └── rename
├── users (coming soon)
│   ├── lookup
│   └── number-lookup
└── legal-hold (future)
    └── process-export
```

## Development

### Adding New Commands to the CLI Tool

1. Create a new command module in `webex-tools/src/webex_tools/commands/`
2. Define your command group and commands using rich-click decorators
3. Register your command group in `webex-tools/src/webex_tools/cli.py`
4. Add appropriate Pydantic models in `webex-tools/src/webex_tools/models/`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
