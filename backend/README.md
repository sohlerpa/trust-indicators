# The backend for the project Trust Indicators

## Installation

install the requirements in the virtual environment in the backend folder with

```
pip install -e ".[dev]"
```

If you want to reinstall it, run ```pip uninstall -y trust-indicators-backend``` and and install it again after that.

## Architecture

`app` holds the server logic, `modules` holds the different modules for the single trust indicators.