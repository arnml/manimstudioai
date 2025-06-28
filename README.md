# Manim Studio AI

A modern, AI-powered platform for creating mathematical animations using Manim.

![Manim Studio AI](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

- **🤖 AI-Powered Generation**: Generate Manim code using Google Gemini AI
- **🎬 Real-time Preview**: Instant video rendering and preview
- **☁️ Cloud-Ready**: Designed for Google Cloud Platform deployment
- **💳 Monetization Ready**: Credits system with Stripe integration
- **🔐 Secure Authentication**: Supabase authentication and user management
- **🔄 CI/CD Pipeline**: Automated testing and deployment with GitHub Actions

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │
│     Backend     │────│  Manim Worker   │
│   (FastAPI)     │    │   (FastAPI)     │
│                 │    │                 │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       │
    ┌────▼────┐             ┌────▼────┐
    │         │             │         │
    │ Gemini  │             │  Manim  │
    │   AI    │             │ Library │
    │         │             ���         │
    └─────────┘             └─────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Google Cloud SDK (for deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/manim-studio-ai.git
   cd manim-studio-ai
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Backend: http://localhost:8000
   - Manim Worker: http://localhost:8001

### Environment Variables

Create a `.env` file in the root directory:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key

# Optional (for production features)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
```

## 📦 Project Structure

```
manim-studio-ai/
├── backend/                 # FastAPI backend service
│   ├── main.py             # Main application file
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Docker configuration
├── manim-worker/          # Manim rendering service
│   ├── main.py           # Worker application
│   ├── requirements.txt  # Python dependencies
│   └── Dockerfile        # Docker configuration
├── docs/                  # Documentation
│   └── payment-integration-plan.md
├── .github/
│   └── workflows/        # GitHub Actions CI/CD
├── docker-compose.yml    # Local development setup
└── deploy.sh            # GCP deployment script
```

## ☁️ Cloud Deployment

### Google Cloud Platform

1. **Prerequisites**
   - GCP account with billing enabled
   - `gcloud` CLI installed and configured
   - Docker installed

2. **Deploy to Cloud Run**
   ```bash
   ./deploy.sh YOUR_PROJECT_ID us-central1
   ```

3. **Set up secrets**
   ```bash
   # Create secrets in Google Secret Manager
   echo "your-gemini-api-key" | gcloud secrets create gemini-api-key --data-file=-
   echo "your-supabase-url" | gcloud secrets create supabase-url --data-file=-
   # ... etc for other secrets
   ```

### Manual Cloud Run Deployment

```bash
# Build and push images
gcloud builds submit ./backend --tag gcr.io/YOUR_PROJECT/manim-studio-backend
gcloud builds submit ./manim-worker --tag gcr.io/YOUR_PROJECT/manim-studio-worker

# Deploy services
gcloud run deploy manim-studio-backend --image gcr.io/YOUR_PROJECT/manim-studio-backend --region us-central1
gcloud run deploy manim-studio-worker --image gcr.io/YOUR_PROJECT/manim-studio-worker --region us-central1
```

## 🔧 Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:socket_app --reload --host 0.0.0.0 --port 8000
```

### Manim Worker Development

```bash
cd manim-worker
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

## 🧪 Testing

### Run All Tests
```bash
# Backend tests
cd backend && python -m pytest

# Lint and format
cd backend && black . && flake8 .
```

### GitHub Actions

The project includes comprehensive CI/CD pipelines:

- **Pull Request Testing**: Runs tests, linting, and security checks
- **Deployment**: Automatically deploys to GCP on main branch pushes
- **Security Scanning**: Weekly vulnerability and dependency checks

## 💰 Monetization

The platform includes a complete credits-based monetization system:

### Credit Costs
- **Basic Generation**: 5 credits
- **Premium Generation**: 10 credits  
- **Video Rendering**: 3 credits
- **Code Editing**: 1 credit

### Credit Packages
- **Starter**: 100 credits for $9.99
- **Pro**: 500 credits for $39.99
- **Enterprise**: 1000 credits for $69.99

### Payment Integration

See [Payment Integration Plan](docs/payment-integration-plan.md) for detailed setup instructions for Supabase authentication and Stripe payments.

## 📊 Usage Analytics

Track user behavior and system performance:

- User authentication and session management
- Credit usage and transaction history
- Rendering performance metrics
- Error tracking and monitoring

## 🔒 Security

- **Authentication**: Supabase JWT-based authentication
- **Authorization**: Row-level security policies
- **Input Validation**: Comprehensive request validation
- **Secret Management**: Google Secret Manager integration
- **Container Security**: Non-root containers and security scanning

## 🛠️ API Reference

### Backend Endpoints

```
GET  /health                    # Health check
POST /generate                  # Generate code with AI
POST /render-code              # Render code directly
GET  /media/videos/{path:path} # Serve video files

# Authentication required endpoints
GET  /user/credits             # Get user credit balance
POST /user/purchase            # Purchase credits
GET  /user/usage               # Get usage history
```

### WebSocket Events

This API is for client integration.

```javascript
// Client to server
socket.emit('generate', { prompt: 'animation description' })

// Server to client  
socket.on('code_generated', { code: 'python code...' })
socket.on('video_rendered', { video_path: 'path/to/video.mp4' })
socket.on('render_error', { error: 'error message' })
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Write tests for new features
- Update documentation for API changes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Manim Community](https://www.manim.community/) for the amazing animation library
- [Google Gemini](https://ai.google.dev/) for AI code generation
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Supabase](https://supabase.com/) for authentication and database
- [Stripe](https://stripe.com/) for payment processing

## 📞 Support

- Create an issue for bug reports or feature requests
- Join our [Discord community](https://discord.gg/your-server) for discussions
- Check the [documentation](docs/) for detailed guides

## 🗺️ Roadmap

- [ ] Advanced AI prompting with examples
- [ ] Export to multiple formats (GIF, WebM, etc.)
- [ ] Template library and sharing
- [ ] Advanced analytics dashboard

---

<div align="center">
  <strong>Built with ❤️ for the mathematical animation community</strong>
</div>