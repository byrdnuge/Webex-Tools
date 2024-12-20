# WebexTools

WebexTools is a collection of Python-based scripts designed to interact with the Webex API. These scripts allow automation of tasks such as device activation, phone number lookup, workspace management, and resource testing.

## Overview

This project provides scripts that simplify Webex API operations and help manage large-scale Webex environments efficiently. Below is a breakdown of the available scripts and their respective functionalities:

### Available Scripts

#### 1. `number-lookup.py`

- **Purpose**: Allows you to search for a specific phone number or extension across all organizations accessible to the Webex API token.
- **Highlights**:
  - Retrieves and scans all organizations.
  - Uses multi-threading to perform faster searches.
  - Provides detailed results, such as the owning organization, location, and phone number details.

- **Usage**:
  Run the script and enter a phone number or extension to search:
  ```bash
  python scripts/number-lookup.py
  ```

#### 2. `rename-workspace.py`

- **Purpose**: Facilitates the renaming of Webex workspaces based on a CSV file with old and new names.
- **Highlights**:
  - Fetches workspace details by name.
  - Renames the workspace in Webex using the provided data.

- **Usage**:
  Ensure your input CSV file (e.g., `workspaces.csv`) is properly formatted with `old_name,new_name`. Then, run:
  ```bash
  python scripts/rename-workspace.py
  ```

#### 3. `activate-room-device.py`

- **Purpose**: Activates Webex devices (e.g., DeskPro) using their IP address and an activation code.
- **Highlights**:
  - Sends activation requests to devices over HTTPS.
  - Uses device credentials for authentication.

- **Usage**:
  For bulk activation, create a CSV file (e.g., `device_activation.csv`) with `ip,activation_code`. Then, execute:
  ```bash
  python scripts/activate-room-device.py
  ```

#### 4. `create-meeting-device.py`

- **Purpose**: Automates the creation of workspaces and assigns a Webex device to each workspace.
- **Highlights**:
  - Creates Webex workspaces with attributes like capacity, calling, and calendar settings.
  - Assigns devices to workspaces and generates activation codes.
  - Reads input details from a CSV file and writes results (e.g., activation codes) to an output file.

- **Usage**:
  Format the input CSV (e.g., `deviceinputmeet.csv`) with workspace details. Run the script:
  ```bash
  python scripts/create-meeting-device.py
  ```

#### 5. `create-flex-device-space.py`

- **Purpose**: Creates workspaces for "hotdesking" or "flexible" setups and optionally assigns devices to these spaces.
- **Highlights**:
  - Ensures compatibility between workspace settings like calendar and hotdesking.
  - Generates activation codes upon successful setup.

- **Usage**:
  Provide workspace configuration in a CSV (e.g., `deviceinput2.csv`) and run:
  ```bash
  python scripts/create-flex-device-space.py
  ```

#### 6. `activate_devices_from_csv.py`

- **Purpose**: Activates Webex devices for a list of users provided via email addresses in a CSV file.
- **Highlights**:
  - Fetches Webex `personId` for user emails.
  - Generates activation codes and logs success or errors to an output file.

- **Usage**:
  Prepare an input CSV (e.g., `people_list.csv`) with a column named `email`. Then, execute:
  ```bash
  python scripts/activate_devices_from_csv.py
  ```

#### 7. `test.py`

- **Purpose**: A utility script for testing Webex API endpoints and token access.
- **Highlights**:
  - Verifies access to Webex organizations, locations, and other resources.
  - Logs API responses for debugging.

- **Usage**:
  Run the script to detect issues or validate token access:
  ```bash
  python scripts/test.py
  ```

#### 8. `test_device.py`

- **Purpose**: Contains unit tests for validating Webex device-related functionalities.
- **Highlights**:
  - Tests device listing and workspace-device relationships.
  - Ensures device assignments and API integrations work as expected.

- **Usage**:
  Run the tests with:
  ```bash
  python -m unittest scripts/test_device.py
  ```

---

## Getting Started

### Prerequisites

Ensure the following are installed:

- Python 3.8 or higher
- Git (optional, for cloning the repo)

You can check versions by running:
```bash
python --version
git --version
```

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/WebexTools.git
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
   - Add your Webex API token and other required variables in the `.env` file:
     ```plaintext
     WEBEX_ACCESS_TOKEN=your_token_here
     ```

4. **Input Files**:
   - For scripts requiring CSV inputs, ensure your files are in the appropriate `input/` directory or edit the script paths accordingly.

---

## File Structure
