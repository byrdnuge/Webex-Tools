# WebexTools

WebexTools is a collection of scripts and tools designed to interact with Webex API or perform related tasks.

## Getting Started

Follow these instructions to set up the project in your local environment:

### Prerequisites

Before you can set up this project, ensure you have the following installed on your system:

- Python 3.8 or higher
- Git

You can check by running:
```bash
python --version
git --version
```

> **Note:** If you don't have Python installed, you can download it [here](https://www.python.org/downloads/).

### Clone the Repository

Clone the project by running:
```bash
git clone https://github.com/YOUR_USERNAME/WebexTools.git
cd WebexTools
```

### Install Dependencies

Install all required dependencies using `pip`:
```bash
pip install -r requirements.txt
```

> **Note:** Make sure to create a Python virtual environment before installing dependencies:
> ```bash
> python -m venv venv
> source venv/bin/activate   # On macOS/Linux
> venv\Scripts\activate      # On Windows
> ```

### Environment Variables

This project uses several environment variables to function. To make this easy, a file named `.env.example` is included in the repository. Follow these steps:

1. Copy `.env.example` into `.env`:
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file in a text editor and customize the values based on your setup.

For example:
```env
WEBEX_API_TOKEN=your_webex_api_token_here
ANOTHER_ENV_VARIABLE=value
```

### Running the Scripts

Once the environment variables are set up and dependencies are installed, you can run the scripts like this:

```bash
python your_script.py
```

## File Structure

Here's a quick overview of the project structure:
WebexTools/ ├── scripts/ # Folder with scripts ├── .env.example # Template for environment variables ├── requirements.txt # Python dependencies ├── README.md # This documentation


## Contribution

Feel free to fork this repository and create pull requests! For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.