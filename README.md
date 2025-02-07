# YT ThumbSense 👍👎

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-enabled-blue.svg)](https://www.docker.com/)

An AI-powered YouTube API that predicts likes/dislikes ratios through comment sentiment analysis.

## 🚀 Features

- Analyzes comment sentiment using NLP (Vader Sentiment)
- Supports multiple languages through LibreTranslate
- Scalable architecture with Redis queue and MongoDB
- Asynchronous task processing with background workers
- REST API with FastAPI and automatic OpenAPI documentation
- Docker containerization for easy deployment
- Comprehensive test suite with unit and integration tests

## 🛠️ Prerequisites

- Docker and Docker Compose
- Python 3.13+
- PDM (Python dependency manager)
- MongoDB 6.0+
- Redis 7.0+

## 🏗️ Installation

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/yt-thumbsense.git
cd yt-thumbsense
```

2. Create a `.env` file with required environment variables (see Configuration section)

3. Start the services:
```bash
docker compose up -d
```

The API will be available at `http://localhost:9090`

### Manual Installation

1. Install dependencies:
```bash
pdm install
```

2. Set up environment variables in your `.env` file or export them:

## ⚙️ Configuration

The following environment variables are required:

```bash
# MongoDB Configuration
MONGODB_URI="mongodb://localhost:27017"
MONGODB_DB="yt_thumbsense"

# Redis Configuration
REDIS_URL="redis://localhost:6379"

# Translation Service
LIBRETRANSLATE_URL="http://localhost:5000/"

# Processing Configuration
MAX_COMMENTS_PER_VIDEO=1000
```

3. Run the services:

```bash
# Start API server
pdm run uvicorn yt_thumbsense.main:app --host 0.0.0.0 --port 9090

# Start worker (in a separate terminal)
pdm run python -m yt_thumbsense.worker
```

## 📚 API Documentation

Once running, visit:
- Swagger UI: `http://localhost:9090/docs`
- ReDoc: `http://localhost:9090/redoc`

## 🧪 Testing

Run all tests:
```bash
pdm run pytest
```

Run specific test suites:
```bash
# Unit tests only
pdm run pytest tests/unit

# Integration tests
pdm run pytest tests/integration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Before submitting:
- Ensure all tests pass
- Add tests for new features
- Update documentation
- Follow the existing code style

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [VADER Sentiment](https://github.com/cjhutto/vaderSentiment) for sentiment analysis
- [LibreTranslate](https://github.com/LibreTranslate/LibreTranslate) for translation services
