# Multi-Agent AI Workflow UI

This is the user interface for the Multi-Agent AI Workflow for Lead Processing system. It's built with Next.js and Material UI.

## Features

- Dashboard with real-time system statistics and visualizations
- Lead management with filtering and detailed views
- CSV import/export functionality
- System settings configuration
- Agent status monitoring

## Technologies Used

- Next.js 14 (App Router)
- TypeScript
- Material UI v5
- Recharts for data visualization
- Axios for API communication
- Notistack for notifications

## Getting Started

### Prerequisites

- Node.js 18.17.0 or later
- npm or yarn
- Backend API server running (see the main project README)

### Installation

1. Clone the repository (if not already part of the main project)
2. Navigate to the UI directory:
   ```
   cd ui
   ```
3. Install dependencies:
   ```
   npm install
   ```
   or
   ```
   yarn install
   ```

### Configuration

Create a `.env.local` file in the root of the UI directory with the following variables:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

Adjust the URL according to your backend API server.

### Development

Run the development server:

```bash
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

### Building for Production

```bash
npm run build
# or
yarn build
```

To start the production server:

```bash
npm run start
# or
yarn start
```

## Folder Structure

```
ui/
├── public/                # Static files
├── src/
│   ├── app/               # App router pages
│   ├── components/        # Reusable components
│   ├── context/           # Context providers
│   ├── hooks/             # Custom hooks
│   ├── styles/            # Global styles
│   ├── types/             # TypeScript types
│   └── utils/             # Utility functions
├── .env.local             # Environment variables (create this)
├── .gitignore
├── next.config.js
├── package.json
├── README.md
└── tsconfig.json
```

## Integration with Backend

This UI is designed to work with the Multi-Agent AI Workflow backend. It communicates with the backend API to:

1. Fetch and display leads data
2. Import and export CSV files
3. Monitor agent status
4. Manage system settings

Make sure the backend API is running before starting the UI development server.

## License

Proprietary - All Rights Reserved 