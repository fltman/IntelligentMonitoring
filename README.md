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

## Prompt Configuration

The application uses several AI prompts for different purposes. Here's how to configure each type:

### 1. Interest Prompt

Used to filter articles based on relevance. The prompt should describe the topics and themes of interest.

Example:
```
Focus on articles related to:
- Artificial Intelligence and Machine Learning
- Tech industry news and innovations
- Startup ecosystem and funding
- Developer tools and platforms

Exclude:
- General consumer tech reviews
- Gaming news
- Personal tech blogs
```

### 2. Summary Prompt

Defines how articles should be summarized. Include specific instructions about length, style, and focus.

Example:
```
Create a concise summary that:
- Captures the main argument or finding
- Includes key statistics or data points
- Highlights industry implications
- Keeps length between 2-3 paragraphs
- Uses professional, objective tone
- Avoids technical jargon
```

### 3. Newsletter Template

Template for generating newsletters. Use markdown formatting and placeholders for dynamic content.

Example:
```markdown
# Tech Insights Weekly
${date}

## Top Stories This Week

${articles_summary}

## Industry Analysis

${analysis}

## Quick Takes
${quick_takes}

---
*Curated by AI, reviewed by humans. Stay informed!*
```

### 4. Podcast Studio Prompt

Defines the podcast format and dialog structure with specific speakers and their voice IDs. Must use exact JSON format.

Example:
```json
create a podcast and return a json in this format. The dialog is an example, create a new one. 

{
  "podcast": {
    "title": "TechTalk Weekly",
    "episode": "42",
    "theme": "The Future of AI in Daily Life",
    "hosts": [
      {
        "name": "Alice Johnson",
        "role": "Host",
        "bio": "Tech journalist with 10 years of experience in AI research.",
        "elevenlabs_voice_id": "8N2ng9i2uiUWqstgmWlH"
      },
      {
        "name": "Bob Smith",
        "role": "Co-Host",
        "bio": "Software engineer and AI ethics advocate.",
        "elevenlabs_voice_id": "XpZeqQTuSFEd29ztEE53"
      }
    ],
    "dialog": [
      {
        "speaker": "Alice Johnson",
        "text": "Welcome back to TechTalk Weekly! This is Alice, and today we're diving into the future of AI in our daily lives. Joining me as always is my co-host, Bob. How are you, Bob?"
      },
      {
        "speaker": "Bob Smith",
        "text": "Hey Alice! I'm excited about this one. AI is already everywhere, but what's next?"
      },
      {
        "speaker": "Alice Johnson",
        "text": "Exactly! We've got smart assistants, self-driving cars, and even AI-generated art. But what happens when AI becomes even more integrated into our decision-making?"
      },
      {
        "speaker": "Bob Smith",
        "text": "That's the big question. Will it empower us, or will it take over jobs and make key decisions for us?"
      },
      {
        "speaker": "Alice Johnson",
        "text": "We'll explore that and more in today's episode. Let's get started!"
      }
    ]
  }
}
```

Important notes:
1. The JSON structure must be exactly as shown above
2. Each host must have a unique `elevenlabs_voice_id`
3. Speaker names in dialog must match exactly with host names
4. Dialog should flow naturally as a conversation

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