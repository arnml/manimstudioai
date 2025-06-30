# Manim Studio AI

A modern, AI-powered platform for creating mathematical animations using Manim.

![Manim Studio AI](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

- **🤖 AI-Powered Generation**: Generate Manim code using Google Gemini AI
- **🎬 Real-time Preview**: Instant video rendering and preview
- **☁️ Cloud-Ready**: Designed for Google Cloud Platform deployment
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
    │         │             │         │
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
   # No environment variables needed for local development
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Backend: http://localhost:8000
   - Manim Worker: http://localhost:8001

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
├── .github/
│   └��─ workflows/        # GitHub Actions CI/CD
└── docker-compose.yml    # Local development setup
```

## ☁️ Cloud Deployment

### Google Cloud Platform

1. **Prerequisites**
   - GCP account with billing enabled
   - `gcloud` CLI installed and configured
   - Docker installed

2. **Enable APIs**
   ```bash
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com containerregistry.googleapis.com --project=YOUR_PROJECT_ID
   ```

3. **Create Gemini API Key Secret**
   ```bash
   echo "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=- --project=YOUR_PROJECT_ID --replication-policy=automatic
   ```

4. **Grant Permissions**
   Get the current IAM policy and save it to a file:
   ```bash
   gcloud projects get-iam-policy YOUR_PROJECT_ID --format=json > iam-policy.json
   ```
   Add the following bindings to the `iam-policy.json` file:
   ```json
   {
     "members": [
       "user:YOUR_EMAIL"
     ],
     "role": "roles/cloudbuild.builds.editor"
   },
   {
     "members": [
       "serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com"
     ],
     "role": "roles/secretmanager.secretAccessor"
   }
   ```
   Set the new IAM policy:
   ```bash
   gcloud projects set-iam-policy YOUR_PROJECT_ID iam-policy.json
   ```

5. **Build and Deploy Manim Worker**
   ```bash
   gcloud builds submit ./manim-worker --tag gcr.io/YOUR_PROJECT_ID/manim-studio-worker:latest --project=YOUR_PROJECT_ID
   ```
   Create a `manim-worker-deploy.yaml` file with the following content, replacing `YOUR_PROJECT_ID`:
   ```yaml
   apiVersion: serving.knative.dev/v1
   kind: Service
   metadata:
     name: manim-studio-worker
   spec:
     template:
       metadata:
         annotations:
           run.googleapis.com/ingress: internal
       spec:
         containers:
         - image: gcr.io/YOUR_PROJECT_ID/manim-studio-worker:latest
   ```
   Deploy the service:
   ```bash
   gcloud run services replace manim-worker-deploy.yaml --project=YOUR_PROJECT_ID --region=us-central1
   ```

6. **Build and Deploy Backend**
   ```bash
   gcloud builds submit ./backend --tag gcr.io/YOUR_PROJECT_ID/manim-studio-backend:latest --project=YOUR_PROJECT_ID
   ```
   Create a `backend-deploy.yaml` file with the following content, replacing `YOUR_PROJECT_ID` and `YOUR_MANIM_WORKER_URL`:
   ```yaml
   apiVersion: serving.knative.dev/v1
   kind: Service
   metadata:
     name: manim-studio-backend
   spec:
     template:
       spec:
         containers:
         - image: gcr.io/YOUR_PROJECT_ID/manim-studio-backend:latest
           env:
           - name: GEMINI_API_KEY
             valueFrom:
               secretKeyRef:
                 key: latest
                 name: gemini-api-key
           - name: MANIM_WORKER_URL
             value: "YOUR_MANIM_WORKER_URL"
   ```
   Deploy the service:
   ```bash
   gcloud run services replace backend-deploy.yaml --project=YOUR_PROJECT_ID --region=us-central1
   ```

## 🛠️ API Reference

### Backend Endpoints

The backend is deployed to a public URL on Cloud Run. You can use this URL to interact with the API from your frontend application.

```
GET  /health                    # Health check
POST /generate                  # Generate code with AI
POST /render-code              # Render code directly
GET  /media/videos/{path:path} # Serve video files
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

---

<div align="center">
  <strong>Built with ❤️ for the mathematical animation community</strong>
</div>
