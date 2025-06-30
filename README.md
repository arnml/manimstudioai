# Manim Studio AI

A modern, AI-powered platform for creating mathematical animations using Manim.

![Manim Studio AI](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

- **🤖 AI-Powered Generation**: Generate Manim code using Google Gemini AI
- **🎬 Real-time Preview**: Instant video rendering and preview
- **☁️ Cloud-Ready**: Single container deployment to Google Cloud Platform
- **🔄 WebSocket Support**: Real-time updates via Socket.IO
- **📱 REST API**: Complete HTTP API for integration

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│                                     │
│         Unified Container           │
│                                     │
│  ┌─────────────┐  ┌─────────────┐   │
│  │   FastAPI   │  │    Manim    │   │
│  │   Backend   │  │   Renderer  │   │
│  │             │  │             │   │
│  └─────────────┘  └─────────────┘   │
│                                     │
│  ┌─────────────┐  ┌─────────────┐   │
│  │  Gemini AI  │  │ Socket.IO   │   │
│  │ Integration │  │  WebSocket  │   │
│  └─────────────┘  └─────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker
- Google Cloud SDK (for cloud deployment)
- Gemini API Key (optional, demo mode available)

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/manim-studio-ai.git
   cd manim-studio-ai
   ```

2. **Build and run with Docker**
   ```bash
   docker build -t manim-studio .
   docker run -p 8080:8080 -e GEMINI_API_KEY="your_api_key_here" manim-studio
   ```

3. **Access the application**
   - API: http://localhost:8080
   - Health Check: http://localhost:8080/health
   - API Documentation: http://localhost:8080/docs

## 📦 Project Structure

```
manim-studio-ai/
├── main.py                 # Unified FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── prompt.json            # Configuration file
└── README.md              # Complete documentation
```

## 🛠️ API Reference

### Core Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "manim-studio-unified"
}
```

#### Generate Animation from Prompt
```http
POST /generate
Content-Type: application/json

{
  "prompt": "Create a rotating square that changes color"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Code generation started"
}
```

#### Render Code Directly
```http
POST /render-code
Content-Type: application/json

{
  "code": "from manim import *\n\nclass MyScene(Scene):\n    def construct(self):\n        circle = Circle()\n        self.play(Create(circle))"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Code rendering started"
}
```

#### Serve Generated Videos
```http
GET /media/videos/{scene_id}/{quality}/{filename}.mp4
```

**Example:**
```http
GET /media/videos/scene_abc123/720p30/MyScene.mp4
```

### WebSocket Events (Socket.IO)

The application provides real-time communication through Socket.IO WebSockets for live updates during code generation and video rendering.

#### Connection
Connect to Socket.IO at the root URL:
```javascript
import { io } from 'socket.io-client';

const socket = io('https://your-service-url');

socket.on('connect', () => {
  console.log('Connected to Manim Studio AI');
});
```

#### Client Events
- **`connect`**: Establish WebSocket connection
- **`disconnect`**: Handle disconnection

#### Server Events

The server emits events throughout the animation generation process:

##### 1. Code Generation Complete
**Event:** `code_generated`
**When:** After AI generates Manim code from user prompt
**Purpose:** Shows the generated code for transparency and debugging
```json
{
  "code": "from manim import *\n\nclass GeneratedScene(Scene):\n    def construct(self):\n        square = Square(color=BLUE)\n        self.play(Create(square))\n        self.play(square.animate.rotate(PI/4))\n        self.wait(1)"
}
```

##### 2. Video Rendering Complete
**Event:** `video_rendered`
**When:** After Manim successfully renders the video
**Purpose:** Provides the video URL for immediate playback
```json
{
  "video_path": "media/videos/scene_abc123/720p30/GeneratedScene.mp4",
  "render_id": "abc123"
}
```

##### 3. Rendering Error
**Event:** `render_error`
**When:** If code generation or video rendering fails
**Purpose:** Error handling and user feedback
```json
{
  "error": "Manim rendering failed: syntax error in code"
}
```

#### Complete Frontend Integration Example

```javascript
import { io } from 'socket.io-client';

class ManimStudioClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
    this.socket = io(baseUrl);
    this.setupEventListeners();
  }

  setupEventListeners() {
    this.socket.on('connect', () => {
      console.log('Connected to Manim Studio AI');
    });

    this.socket.on('code_generated', (data) => {
      console.log('Generated code:', data.code);
      // Display code in UI
      document.getElementById('generated-code').textContent = data.code;
    });

    this.socket.on('video_rendered', (data) => {
      console.log('Video ready:', data.video_path);
      // Show video in UI
      const videoUrl = `${this.baseUrl}/${data.video_path}`;
      document.getElementById('video-player').src = videoUrl;
    });

    this.socket.on('render_error', (data) => {
      console.error('Rendering failed:', data.error);
      // Show error message
      document.getElementById('error-message').textContent = data.error;
    });

    this.socket.on('disconnect', () => {
      console.log('Disconnected from server');
    });
  }

  async generateAnimation(prompt) {
    try {
      const response = await fetch(`${this.baseUrl}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt })
      });
      
      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Failed to generate animation:', error);
    }
  }

  async renderCode(code) {
    try {
      const response = await fetch(`${this.baseUrl}/render-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code })
      });
      
      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Failed to render code:', error);
    }
  }
}

// Usage
const client = new ManimStudioClient('https://your-service-url');

// Generate from prompt
client.generateAnimation('Create a bouncing ball animation');

// Or render custom code
const customCode = `
from manim import *

class MyAnimation(Scene):
    def construct(self):
        circle = Circle(color=RED)
        self.play(Create(circle))
        self.play(circle.animate.shift(UP))
        self.wait(1)
`;
client.renderCode(customCode);
```

#### WebSocket Flow

1. **User submits prompt** → `POST /generate` or `POST /render-code`
2. **Server responds** → `{"status": "success", "message": "Code generation started"}`
3. **Code generated** → `code_generated` event emitted
4. **Video rendering starts** → Internal Manim process
5. **Video complete** → `video_rendered` event emitted with video URL
6. **Client displays video** → Stream from `/media/videos/...` endpoint

This real-time approach provides immediate feedback and a smooth user experience during the animation generation process.

## ☁️ Cloud Deployment

### Google Cloud Platform

#### Prerequisites
1. GCP account with billing enabled
2. `gcloud` CLI installed and configured
3. Enable required APIs:
   ```bash
   gcloud services enable cloudbuild.googleapis.com run.googleapis.com secretmanager.googleapis.com
   ```

#### Manual Deployment Steps

1. **Set your project ID**

   **Linux/macOS:**
   ```bash
   export PROJECT_ID="your-gcp-project-id"
   gcloud config set project $PROJECT_ID
   ```

   **Windows (Command Prompt):**
   ```cmd
   set PROJECT_ID=your-gcp-project-id
   gcloud config set project %PROJECT_ID%
   ```

   **Windows (PowerShell):**
   ```powershell
   $PROJECT_ID="your-gcp-project-id"
   gcloud config set project $PROJECT_ID
   ```

2. **Create Gemini API Key Secret** (optional)

   **Linux/macOS:**
   ```bash
   echo "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
   ```

   **Windows (Command Prompt):**
   ```cmd
   echo YOUR_GEMINI_API_KEY | gcloud secrets create gemini-api-key --data-file=-
   ```

   **Windows (PowerShell):**
   ```powershell
   "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
   ```

3. **Build and push container image**

   **Linux/macOS:**
   ```bash
   gcloud builds submit . --tag gcr.io/$PROJECT_ID/manim-studio-ai-backend:latest
   ```

   **Windows (Command Prompt):**
   ```cmd
   gcloud builds submit . --tag gcr.io/%PROJECT_ID%/manim-studio-ai-backend:latest
   ```

   **Windows (PowerShell):**
   ```powershell
   gcloud builds submit . --tag gcr.io/$PROJECT_ID/manim-studio-ai-backend:latest
   ```

4. **Deploy to Cloud Run**

   **Linux/macOS:**
   ```bash
   gcloud run deploy manim-studio-ai-backend \
     --image gcr.io/$PROJECT_ID/manim-studio-ai-backend:latest \
     --region=us-central1 \
     --allow-unauthenticated \
     --set-env-vars="GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)" \
     --memory=4Gi \
     --cpu=4 \
     --timeout=600 \
     --concurrency=10 \
     --max-instances=10
   ```

   **Windows (Command Prompt):**
   ```cmd
   gcloud run deploy manim-studio-ai-backend ^
     --image gcr.io/%PROJECT_ID%/manim-studio-ai-backend:latest ^
     --region=us-central1 ^
     --allow-unauthenticated ^
     --memory=4Gi ^
     --cpu=4 ^
     --timeout=600 ^
     --concurrency=10 ^
     --max-instances=10
   
   rem Set environment variable separately if using secrets
   gcloud run services update manim-studio-ai-backend ^
     --region=us-central1 ^
     --set-env-vars="GEMINI_API_KEY=%GEMINI_API_KEY%"
   ```

   **Windows (PowerShell):**
   ```powershell
   gcloud run deploy manim-studio-ai-backend `
     --image gcr.io/$PROJECT_ID/manim-studio-ai-backend:latest `
     --region=us-central1 `
     --allow-unauthenticated `
     --memory=4Gi `
     --cpu=4 `
     --timeout=600 `
     --concurrency=10 `
     --max-instances=10
   
   # Set environment variable separately if using secrets
   $GEMINI_KEY = gcloud secrets versions access latest --secret=gemini-api-key
   gcloud run services update manim-studio-ai-backend `
     --region=us-central1 `
     --set-env-vars="GEMINI_API_KEY=$GEMINI_KEY"
   ```

5. **Get service URL**

   **Linux/macOS:**
   ```bash
   gcloud run services describe manim-studio-ai-backend --region=us-central1 --format="value(status.url)"
   ```

   **Windows (Command Prompt):**
   ```cmd
   gcloud run services describe manim-studio-ai-backend --region=us-central1 --format="value(status.url)"
   ```

   **Windows (PowerShell):**
   ```powershell
   gcloud run services describe manim-studio-ai-backend --region=us-central1 --format="value(status.url)"
   ```


## 🧪 Testing the API

### Using cURL

1. **Test health endpoint**
   ```bash
   curl https://your-service-url/health
   ```

2. **Generate animation from prompt**
   ```bash
   curl -X POST https://your-service-url/generate \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Create a bouncing ball animation"}'
   ```

3. **Render custom code**
   ```bash
   curl -X POST https://your-service-url/render-code \
     -H "Content-Type: application/json" \
     -d '{
       "code": "from manim import *\n\nclass TestScene(Scene):\n    def construct(self):\n        text = Text(\"Hello Manim!\")\n        self.play(Write(text))\n        self.wait(2)"
     }'
   ```

### Using Python

```python
import requests
import json

# API endpoint
url = "https://your-service-url"

# Generate animation
response = requests.post(f"{url}/generate", 
    json={"prompt": "Create a rotating triangle"},
    headers={"Content-Type": "application/json"}
)
print(response.json())

# Render custom code
code = """
from manim import *

class MyAnimation(Scene):
    def construct(self):
        circle = Circle(color=BLUE)
        self.play(Create(circle))
        self.play(circle.animate.set_color(RED))
        self.wait(1)
"""

response = requests.post(f"{url}/render-code",
    json={"code": code},
    headers={"Content-Type": "application/json"}
)
print(response.json())
```

## 🔧 Configuration

### Environment Variables

- **`GEMINI_API_KEY`**: Google Gemini API key for AI code generation
  - If not provided or invalid, the service runs in demo mode
  - Demo mode generates sample animations instead of using AI

### Resource Limits

The default Cloud Run configuration includes:
- **CPU**: 2-4 cores
- **Memory**: 2-4 GiB  
- **Timeout**: 600 seconds
- **Concurrency**: 10 requests per instance
- **Auto-scaling**: 0-10 instances

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
- Test both local Docker and Cloud Run deployments

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Manim Community](https://www.manim.community/) for the amazing animation library
- [Google Gemini](https://ai.google.dev/) for AI code generation
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework

## 🔍 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   docker stop $(docker ps -q --filter "publish=8000")
   ```

2. **Video rendering fails**
   - Check that the Manim code syntax is correct
   - Ensure sufficient memory allocation
   - Check container logs: `docker logs <container-id>`

3. **Gemini API errors**
   - Verify API key is valid
   - Check quota limits
   - Service will fall back to demo mode automatically

4. **Cloud Run deployment issues**
   - Ensure all required APIs are enabled
   - Check IAM permissions
   - Verify project ID in configuration files

5. **Build warnings about PATH**
   - Warnings about scripts not being on PATH during `gcloud builds submit` are harmless
   - These are automatically handled in the container environment
   - The build will complete successfully despite these warnings

6. **Cloud Run port configuration**
   - Cloud Run requires containers to listen on the PORT environment variable (typically 8080)
   - If you get "container failed to start" errors, ensure your container uses the correct port
   - The Dockerfile automatically handles this with `${PORT:-8080}`

---

<div align="center">
  <strong>Built with ❤️ for the mathematical animation community</strong>
</div>