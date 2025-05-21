# Multi-Agent AI Workflow for Lead Processing

This project implements a multi-agent AI system for automating lead processing. It consists of two main AI agents that communicate through a shared data store:

1. **Voice AI Agent**: Contacts leads via phone to confirm their details and interest
2. **Data Entry Agent**: Automatically submits confirmed lead data to the LeadHoop portal

## Architecture Overview

![Architecture Diagram](docs/architecture.png)

### Key Components

- **Shared Data Store (PostgreSQL)**: Central database that serves as the communication hub between agents and tracks lead status
- **Voice AI Agent**: Uses Assistable.AI to make outbound calls and confirm lead information
- **Data Entry Agent**: Uses UI automation (Playwright) to enter confirmed lead data into the LeadHoop portal
- **CSV Processor**: Imports lead data from CSV files and exports processed data
- **AWS S3 Integration**: Uploads call recordings to the specified S3 bucket
- **Monitoring & Logging**: Comprehensive logging and monitoring system
- **REST API**: FastAPI-based endpoints for system monitoring and control

## Lead Workflow States

1. **Pending**: Initial state when a lead is imported from CSV
2. **Calling**: Voice AI Agent is currently calling the lead
3. **Confirmed**: Lead has confirmed their information and interest
4. **Entry In Progress**: Data Entry Agent is submitting to LeadHoop
5. **Entered**: Successfully submitted to LeadHoop
6. **Not Interested**: Lead confirmed they're not interested
7. **Call Failed**: Voice AI Agent couldn't reach the lead
8. **Entry Failed**: Data Entry Agent couldn't submit the lead data

## Setup Instructions

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Assistable.AI account credentials
- AWS S3 credentials for call recording uploads
- Access to LeadHoop portal

### Installation

#### Option 1: Manual Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/multi-agent-ai.git
   cd multi-agent-ai
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install Playwright browsers:
   ```
   playwright install
   ```

4. Create a `.env` file with the necessary credentials:
   ```
   # Database
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=lead_processing
   DB_USER=postgres
   DB_PASSWORD=your_password

   # Assistable.AI
   ASSISTABLE_API_KEY=your_api_key

   # AWS S3
   AWS_ACCESS_KEY=your_aws_access_key
   AWS_SECRET_KEY=your_aws_secret_key
   AWS_REGION=us-east-1
   AWS_FOLDER=

   # LeadHoop
   LEADHOOP_PORTAL_URL=https://ieim-portal.leadhoop.com/consumer/new/aSuRzy0E8XWWKeLJngoDiQ
   LEADHOOP_USERNAME=your_username
   LEADHOOP_PASSWORD=your_password
   ```

5. Initialize the database:
   ```
   python -m app.database.init_db
   ```

#### Option 2: Docker Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-organization/multi-agent-ai.git
   cd multi-agent-ai
   ```

2. Create a `.env` file with the necessary credentials:
   ```
   # Database
   DB_PASSWORD=your_secure_password

   # Assistable.AI
   ASSISTABLE_API_KEY=your_api_key

   # AWS S3
   AWS_ACCESS_KEY=your_aws_access_key
   AWS_SECRET_KEY=your_aws_secret_key
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=your_bucket_name

   # LeadHoop
   LEADHOOP_USERNAME=your_username
   LEADHOOP_PASSWORD=your_password
   ```

3. Build and start the containers:
   ```
   docker-compose up -d
   ```

4. Access the API at http://localhost:8000

5. To view logs:
   ```
   docker logs multiagent_app -f
   ```

6. To stop the containers:
   ```
   docker-compose down
   ```

### Running the Application

#### Manual Execution

1. Start the full application with API:
   ```
   python run.py --api
   ```

2. Run with custom batch sizes:
   ```
   python run.py --voice-batch 10 --entry-batch 5
   ```

3. Run API server only:
   ```
   python run.py --api-only
   ```

4. Reset database on startup:
   ```
   python run.py --reset-db
   ```

5. Run browsers in non-headless mode (useful for debugging):
   ```
   python run.py --no-headless
   ```

## API Endpoints

The system exposes the following REST API endpoints:

- `GET /api/leads`: List all leads with optional filtering
- `GET /api/leads/{lead_id}`: Get detailed information about a specific lead
- `PUT /api/leads/{lead_id}/status`: Update a lead's status
- `POST /api/csv/process`: Process a new CSV file for import
- `GET /api/status`: Get system status and statistics
- `POST /api/reset`: Reset the system (clears pending leads)

## Development

### Running Tests

```
pytest tests/
```

### Adding New Lead Fields

If new lead fields need to be added:

1. Update the database schema in `app/database/models.py`
2. Modify the CSV import/export logic in `app/utils/csv_processor.py`
3. Update the Voice AI Agent script in `app/agents/voice_agent.py`
4. Update the Data Entry Agent form mapping in `app/agents/data_entry_agent.py`
5. Run database migrations

### Project Structure

```
MultiAgentAI/
├── app/
│   ├── agents/               # AI agents for voice and data entry
│   ├── api/                  # FastAPI-based REST API
│   ├── config/               # Application configuration
│   ├── database/             # Database models and repository
│   ├── utils/                # Utility functions and classes
│   └── main.py               # Main application entry point
├── data/
│   ├── import/               # CSV files for import
│   └── export/               # Exported CSV files
├── logs/                     # Application logs
├── tests/                    # Unit and integration tests
├── .env                      # Environment variables
├── Dockerfile                # Docker configuration
├── docker-compose.yml        # Docker Compose services
├── requirements.txt          # Python dependencies
├── run.py                    # Script to run the application
└── README.md                 # This documentation
```

## License

Proprietary - All Rights Reserved 