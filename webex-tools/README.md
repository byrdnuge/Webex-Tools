# WebexTools CLI

A unified command-line interface for managing Cisco Webex devices and resources.

## Features

- **Device Management**: Activate, list, and manage Webex devices
- **Batch Operations**: Process multiple devices using CSV files
- **Rich Output**: Colorful and well-formatted terminal output
- **Data Validation**: Robust input validation using Pydantic models

## Installation

### Prerequisites

- Python 3.8 or higher
- Webex API access token

### Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/webex-tools.git
   cd webex-tools
   ```

2. Install using Poetry:
   ```bash
   poetry install
   ```

3. Set up your Webex API token:
   ```bash
   echo "WEBEX_ACCESS_TOKEN=your_token_here" > .env
   ```

## Usage

### Basic Commands

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

### CSV Format for Batch Operations

For batch device activation, create a CSV file with the following columns:

```csv
activation_code,display_name,place_id,tags
CODE1,Meeting Room 1,,floor1,building1
CODE2,Meeting Room 2,PLACE_ID_HERE,floor2,building1
```

## Development

### Project Structure

```
webex-tools/
├── src/
│   └── webex_tools/
│       ├── commands/       # CLI command implementations
│       ├── models/         # Pydantic data models
│       ├── utils/          # Utility functions
│       ├── __init__.py     # Package initialization
│       └── cli.py          # Main CLI entry point
├── tests/                  # Test suite
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

### Adding New Commands

1. Create a new command module in `src/webex_tools/commands/`
2. Define your command group and commands
3. Register your command group in `src/webex_tools/cli.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
