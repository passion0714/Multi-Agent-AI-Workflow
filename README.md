# Multi-Agent AI Workflow for Lead Processing

This system automates lead contact via voice calls and data entry into third-party portals. It utilizes multi-agent architecture with specialized components for voice calls, data entry automation, and API management.

## Project Overview

The Voice AI Agent system automates the process of contacting leads via voice calls, qualifying them, and then entering their information into a third-party portal (Lead Hoop). The system consists of two main agents:

1. **Voice Agent**: Makes outbound calls to leads, conducts conversations, and updates lead status based on call outcomes.
2. **Data Entry Agent**: For leads that have been successfully qualified (status: Confirmed), enters their data into the Lead Hoop portal using browser automation.

These agents are supported by a shared infrastructure including database models, API endpoints, configuration management, and utilities.

## Architecture

The system is organized into the following components:

```
.
├── api/                       # API server (FastAPI)
│   ├── routers/               # API route definitions
│   ├── middleware/            # API middleware
│   └── server.py              # API server initialization
├── data_entry_agent/          # Data Entry Agent
│   ├── agent.py               # Main agent logic
│   ├── ui_automation.py       # Browser automation for Lead Hoop
│   └── lead_hoop_mapper.py    # Maps lead data to form fields
├── shared/                    # Shared modules
│   ├── database/              # Database models and utilities
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── connection.py      # Database connection utilities
│   │   └── init_db.py         # Database initialization script
│   ├── config.py              # Configuration management
│   ├── logging_setup.py       # Logging configuration
│   └── utils.py               # Utility functions
├── voice_agent/               # Voice Agent
│   ├── agent.py               # Main agent logic
│   ├── call_handler.py        # Handles call flow and states
│   └── voice_api_client.py    # Client for the voice API
├── logs/                      # Log files
├── tests/                     # Test suite
├── .env.example               # Example environment variables
├── requirements.txt           # Python dependencies
├── run.py                     # Main entry point
└── README.md                  # Project documentation
```

## Features

- **Voice Agent**:
  - Makes outbound calls to leads
  - Conducts natural language conversations
  - Processes call outcomes and updates lead status
  - Schedules follow-up calls if needed

- **Data Entry Agent**:
  - Polls for leads with "Confirmed" status
  - Automates browser interaction with the Lead Hoop portal
  - Maps lead data to form fields
  - Handles error recovery and session management
  - Updates lead status after entry

- **API Server**:
  - Provides RESTful endpoints for lead management
  - Exposes agent control and monitoring endpoints
  - Enables integration with external systems

- **Shared Infrastructure**:
  - Database models with SQLAlchemy
  - Configuration management with environment variables
  - Structured logging
  - Utility functions

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL
- Node.js (for Playwright browser automation)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd VoiceAIagent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

5. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. Initialize the database:
   ```bash
   python -m shared.database.init_db --create --seed
   ```

## Usage

### Running the System

Use the main `run.py` script to start the system:

```bash
# Run the entire system
python run.py

# Run specific components
python run.py --api-only  # Run only the API server
python run.py --voice-agent  # Run only the Voice Agent
python run.py --data-entry-agent  # Run only the Data Entry Agent
```

### API Endpoints

The API server provides the following endpoints:

- `GET /api/leads` - List all leads
- `POST /api/leads` - Create a new lead
- `GET /api/leads/{id}` - Get lead details
- `PUT /api/leads/{id}` - Update a lead
- `POST /api/calls` - Initiate a new call
- `GET /api/calls/{id}` - Get call details
- `GET /api/health` - System health check
- `POST /api/agents/control` - Control agent behavior

## Development

### Project Structure

The project follows a modular architecture with clear separation of concerns:

- Each major component (Voice Agent, Data Entry Agent, API) is in its own package
- Shared code is in the `shared` package
- Configuration is centralized and loaded from environment variables
- Database models are defined with SQLAlchemy ORM

### Testing

Run tests with pytest:

```bash
pytest
```

For coverage report:

```bash
pytest --cov=.
```

### Adding a New Voice API Provider

To add support for a new voice API provider:

1. Add the provider's configuration in `shared/config.py`
2. Create a new client implementation in `voice_agent/voice_api_client.py`
3. Update the factory method to return the new client implementation

## Deployment

### Docker

The system can be deployed using Docker:

```bash
docker build -t voiceai-agent .
docker run -p 8000:8000 --env-file .env voiceai-agent
```

### Scaling

For production environments:

- Use a production-grade database server
- Deploy the API server with a proper WSGI/ASGI server like Gunicorn
- Consider using Kubernetes for orchestration
- Set up proper monitoring and logging

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

This project uses several open-source libraries:

- FastAPI for the API server
- SQLAlchemy for database ORM
- Playwright for browser automation
- Twilio/Deepgram for voice API integration 