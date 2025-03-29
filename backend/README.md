# PyDocAss Backend

This is the backend API for the Python Documentation Assistant. It's built with Python, Flask, and OpenAI's API.

## Directory Structure

- `src/`: Source code
  - `pydocass/`: Main package
    - `api/`: API endpoints
    - `core/`: Core functionality
    - `models/`: Data models
    - `services/`: Business logic
    - `utils/`: Utility functions
    - `components/`: Components used by the core functionality
    - `connection/`: Database and API connection utilities
- `tests/`: Test files
- `server/`: Server configuration
- `docs/`: Documentation

## Development

To run the backend in development mode:

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python -m server.app --port 4000
```

This will start the development server at http://localhost:4000.

## Testing

To run the tests:

```bash
python -m unittest discover tests
```

## TODO:
  - Reduce the number of comments
  - Embedded functions (functions inside function / method)
