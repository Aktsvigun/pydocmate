# PyDocAss - Python Documentation Assistant

This repository contains a web application that helps developers document Python code with the assistance of AI.

## Project Structure

The project is organized into the following directories:

### Frontend
- `frontend/`: Contains the Next.js frontend application
  - `components/`: React components
  - `pages/`: Next.js pages
  - `styles/`: Global styles and theme
  - `public/`: Static assets
  - `utils/`: Utility functions
  - `types/`: TypeScript type definitions
  - `hooks/`: Custom React hooks
  - `services/`: API services and data fetching
  - `config/`: Frontend configuration files

### Backend
- `backend/`: Contains the Python backend application
  - `src/`: Source code
    - `pydocass/`: Main package
      - `api/`: API endpoints
      - `core/`: Core functionality
      - `models/`: Data models
      - `services/`: Business logic
      - `utils/`: Utility functions
  - `tests/`: Test files
  - `server/`: Server configuration
  - `docs/`: Documentation

### Infrastructure
- `docker/`: Docker configuration files
  - `frontend/`: Frontend Docker files
  - `backend/`: Backend Docker files
- `scripts/`: Utility scripts

## Getting Started

### Running the Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running the Backend

```bash
cd backend
pip install -r requirements.txt
python -m pydocass
```

### Running with Docker

```bash
docker-compose up -d
```

## Contributing

Please see the [CONTRIBUTING.md](CONTRIBUTING.md) file for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 