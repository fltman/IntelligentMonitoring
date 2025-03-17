# AI-Powered News and Podcast Platform

An intelligent platform that automatically tracks, processes, and transforms web content into engaging multimedia experiences including newsletters and AI-generated podcasts.

## Features

- 🔍 Automated web content tracking and processing
- 📰 AI-powered article summarization
- 📝 Dynamic newsletter generation
- 🎙️ AI podcast script generation
- 🗣️ Text-to-speech podcast creation using ElevenLabs
- 🎯 Interest-based content filtering
- 📊 Real-time processing status monitoring

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database
- OpenAI API key
- ElevenLabs API key

## Setup

1. Clone the repository
2. Install Python 3.11 if not already installed:
```bash
# The project will automatically install Python and required packages
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
DATABASE_URL=postgresql://user:password@host:port/dbname
OPENAI_API_KEY=your_openai_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

### Database Setup

The application will automatically create the necessary database tables on first run. Make sure your PostgreSQL database is accessible using the provided DATABASE_URL.

## Running the Application

1. Start the Flask server:
```bash
python server.py
```

2. Access the web interface at `http://localhost:5000`

## Usage

### 1. Settings Configuration

- Set interest and summary prompts for content filtering
- Configure newsletter template
- Enable/disable podcast generation
- Set podcast studio prompt
- Configure newsletter generation time

### 2. URL Management

- Add URLs to monitor
- Remove URLs from monitoring
- Manually trigger URL processing
- View processing status in real-time

### 3. Content Management

- View processed articles
- Browse generated newsletters
- Access podcast scripts
- Generate audio for podcast scripts

## API Endpoints

### Content Management
- `GET /api/articles` - Get recent articles
- `GET /api/newsletters` - Get generated newsletters
- `GET /api/podcasts` - Get podcast scripts

### URL Management
- `GET /api/urls` - List monitored URLs
- `POST /api/urls` - Add new URL
- `DELETE /api/urls/<url>` - Remove URL

### Processing
- `POST /api/process` - Trigger URL processing
- `GET /api/status` - Get processing status

### Settings
- `GET /api/settings` - Get current settings
- `POST /api/settings` - Update settings

### Audio Generation
- `POST /api/generate-audio` - Generate podcast audio

## Technical Details

- Flask-based backend with RESTful API
- Bootstrap-enhanced responsive frontend
- Markdown-supported newsletter viewer
- PostgreSQL database for persistent storage
- AI-driven content processing using OpenAI GPT-4
- ElevenLabs API for voice generation
- Real-time status updates
- Automated scheduling system

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request