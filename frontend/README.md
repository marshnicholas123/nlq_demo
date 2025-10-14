# Text2SQL Demo Frontend

A Next.js frontend application for comparing different Text2SQL service approaches.

## Features

- **Service Comparison**: Run the same query through multiple Text2SQL services simultaneously
- **Service Toggle**: Select which services to run (Simple, Advanced, Chat, Agentic)
- **Session Management**: Maintain conversation context for Chat and Agentic services
- **Follow-up Queries**: Support for conversational follow-ups with stateful services
- **Results Visualization**: Side-by-side comparison of SQL queries, execution results, and metadata
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Services

1. **Simple** - Basic schema-based SQL generation
2. **Advanced** - Hybrid retrieval with BM25 + Vector search
3. **Chat** - Conversational with history management
4. **Agentic** - LangGraph-based agent with tools and reflection

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Usage

1. **Select Services**: Choose which Text2SQL services to run using the checkboxes
2. **Enter Query**: Type a natural language question about nuclear power plants
3. **Execute**: Check "Execute SQL queries" if you want to run the queries and see results
4. **Run**: Click "Run Query" to execute across all selected services
5. **Compare**: View side-by-side results with SQL, data tables, and metadata
6. **Follow-up**: For Chat/Agentic services, ask follow-up questions in the same session

## Session Management

- Chat and Agentic services maintain conversation history via session ID
- Use "New Session" to start a fresh conversation
- Use "Clear History" to reset the conversation without changing session ID

## Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Tech Stack

- **Framework**: Next.js 14
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State**: React Hooks
- **Forms**: React Hook Form
- **UUID**: uuid library

## Project Structure

```
frontend/
├── src/
│   ├── components/        # React components
│   │   ├── QueryInput.tsx
│   │   ├── ServiceToggle.tsx
│   │   ├── ServiceResultCard.tsx
│   │   └── SessionManager.tsx
│   ├── pages/            # Next.js pages
│   │   ├── index.tsx     # Main demo page
│   │   ├── _app.tsx
│   │   └── _document.tsx
│   ├── api/              # API client
│   │   └── text2sql.ts
│   ├── types/            # TypeScript types
│   │   └── text2sql.ts
│   ├── utils/            # Utility functions
│   │   └── formatting.ts
│   └── styles/           # Global styles
│       └── globals.css
├── public/               # Static assets
├── package.json
└── tsconfig.json
```
