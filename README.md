# LSSD Interrogation Log Parser

An application for parsing and analyzing logs, designed for internal use by Vibe RolePlay's LSSD.

## Features

- Parse and analyze interrogation logs.
- User-friendly GUI built with PyQt6.
- Configurable settings for log parsing.
- Logging and error handling.
- Unit tests for core functionality.

## Project Structure

```plaintext
.
├── build
│   └── lssd_log_parser
│       ├── base_library.zip          # Compressed library files for the application.
│       ├── localpycs                 # Compiled Python files for local execution.
│       ├── lssd_log_parser.pkg       # Packaged application file.
│       ├── PYZ-00.pyz                # Python archive containing the application code.
│       ├── warn-lssd_log_parser.txt  # Warning logs generated during the build process.
│       └── xref-lssd_log_parser.html # Cross-reference documentation for the build.
├── dist
│   ├── lssd_log_parser               # Directory containing the built application.
│   ├── lssd_log_parser.exe           # Windows executable for the application.
│   └── python-3.10.11-amd64.exe      # Python installer bundled with the application.
├── __init__.py                       # Initialization file for the project.
├── logs
│   └── app.log                       # Log file for application runtime events.
├── lssd_log_parser.spec              # PyInstaller specification file for building the application.
├── Makefile                          # Automation script for common tasks like running and testing.
├── poetry.lock                       # Lock file for managing dependencies with Poetry.
├── pyproject.toml                    # Configuration file for the project and dependencies.
├── README.md                         # Documentation file for the project.
├── requirements.txt                  # List of Python dependencies for the project.
├── resources
│   └── lssd_logo_bar.png             # Image resource used in the application.
├── src
│   ├── models                        # Directory containing data models and logic.
│   │   ├── __init__.py               # Initialization file for the models module.
│   │   ├── log_formatter.py          # Module for formatting log data.
│   │   ├── logger_config.py          # Module for configuring the application logger.
│   │   └── log_parser.py             # Core module for parsing interrogation logs.
│   └── views                         # Directory containing GUI components.
│       ├── __init__.py               # Initialization file for the views module.
│       ├── left_panel.py             # Module for the left panel of the GUI.
│       ├── main_window.py            # Module for the main application window.
│       ├── right_panel.py            # Module for the right panel of the GUI.
│       └── workspace.py              # Module for the workspace area of the GUI.
└── tests
    ├── __init__.py                   # Initialization file for the tests module.
    ├── sample_logs2.txt              # Sample log file for testing.
    ├── sample_logs.txt               # Another sample log file for testing.
    ├── test_log_formatter.py         # Unit tests for the log formatter module.
    └── test_log_parser.py            # Unit tests for the log parser module.
```


## Requirements

- Python >= 3.8
- Dependencies:
  - `pydantic`
  - `PyQt6`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/lssd_interview_parser_app.git
   cd lssd_interview_parser_app
    ```

2. Install the dependencies uding Poetry
    ```bash
    poetry install
    ```

3. Activate the virtual environment:
    ```bash
    poetry shell
    ```

## Usage
Run the application:
```bash
    make run
```

## Testing
Run the unit tests:
```bash
    make test
```

## License
This project is for internal use only and is not licensed for public distribution without permission.

