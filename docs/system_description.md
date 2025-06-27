# Project: Manim Studio AI

**Manim Studio AI** is a web-based application that empowers users to create mathematical animations with Manim by simply providing a descriptive prompt. Leveraging the power of Google's Gemini SDK, the application generates the necessary Python code, renders it into a video, and displays the result in a clean, elegant interface. The system is designed to be interactive, streaming code generation and rendering progress to the user in real-time. In the event of an error, the system provides clear feedback and offers the user the ability to either refine their prompt or attempt an automated fix.

## System Description

The application follows a containerized, microservices-oriented architecture orchestrated with Docker Compose. This design ensures a clear separation of concerns, scalability, and ease of development. The user interacts with a modern, single-page application (SPA) built with Vite and React. When a user submits a prompt, it is sent to a Python backend API. This backend service then communicates with the Gemini API to generate the Manim Python code.

Upon receiving the code, the backend initiates a rendering job in a dedicated Manim worker container. This worker executes the Python code in a sandboxed environment. The frontend is updated in real-time with the status of the code generation and rendering process via WebSockets. If the rendering is successful, the path to the generated video is sent to the frontend for display. If the code execution results in an error, the error message is streamed back to the user interface, prompting them for the next action.

## System Components

The system is comprised of three core Docker containers managed by a `docker-compose.yml` file:

* **`frontend` (Vite/React):** This container runs the user-facing application. It's built with Vite for a fast development experience and React with Shadcn for a simple, elegant UI. It communicates with the `backend` via HTTP requests for initial prompt submission and a WebSocket connection for real-time updates.

* **`backend` (Python/FastAPI):** This service acts as the central hub of the application. It's a Python application built with the FastAPI framework. Its responsibilities include:
    * Receiving prompts from the `frontend`.
    * Interacting with the Google Gemini SDK to generate Manim code.
    * Initiating rendering tasks in the `manim-worker`.
    * Serving the final video files.
    * Managing WebSocket connections for real-time communication with the `frontend`.

* **`manim-worker` (Python/Manim):** This container is based on the official `manimcommunity/manim` Docker image. It has a single responsibility: to receive Python code from the `backend`, execute it using Manim to render a video, and report back the success or failure of the operation. It will have a shared volume with the `backend` to store the generated video files.

## Tech Stack

| Component      | Technology                                                                                                  | Description                                                                                             |
| :------------- | :---------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------ |
| **Frontend** | [Vite](https://vitejs.dev/), [React](https://reactjs.org/), [Shadcn/ui](https://ui.shadcn.com/), [Tailwind CSS](https://tailwindcss.com/), [Socket.IO Client](https://socket.io/docs/v4/client-installation/) | A modern, fast, and aesthetically pleasing user interface.                                              |
| **Backend** | [Python](https://www.python.org/), [FastAPI](https://fastapi.tiangolo.com/), [Google Gemini SDK](https://ai.google.dev/docs/sdk_setup), [Socket.IO](https://python-socketio.readthedocs.io/en/latest/) | A high-performance asynchronous backend for handling API requests and real-time communication.          |
| **Rendering** | [Manim](https://www.manim.community/)                                                                         | The core engine for creating mathematical animations.                                                   |
| **Containerization** | [Docker](https://www.docker.com/), [Docker Compose](https://docs.docker.com/compose/)                                | For creating a reproducible and isolated development and production environment.                      |

## Security

The primary security consideration is the management of the Google Gemini API key. To ensure this secret is not exposed on the client-side, the following approach will be used:

* **Environment Variables:** The Gemini API key will be stored as an environment variable within the `backend` service's container.
* **`.env` File:** In the development environment, a `.env` file will be used to load the API key into the Docker Compose configuration for the `backend` service. This file will be included in the project's `.gitignore` to prevent it from being committed to version control.
* **Production Deployment:** For a production environment, secrets would be managed through the hosting platform's secret management system (e.g., Docker Secrets, AWS Secrets Manager, Google Secret Manager). The Vite frontend will **not** have direct access to the Gemini API key; all interactions with the Gemini API will be proxied through the secure `backend` service.

## UI Interface

The user interface will be minimalist and elegant, drawing inspiration from the clean, focused design of VS Code, Claude, and ChatGPT.

The main screen will feature a prominent, centered text area where the user can input their prompt. Below the prompt input, a "Generate" button will initiate the process.

As the system processes the request, the UI will provide real-time feedback. The code generated by Gemini will be displayed in a formatted code block with syntax highlighting, streaming in as it's generated. A status indicator will show the current stage of the process (e.g., "Generating Code...", "Rendering Video...").

Once the video is rendered, it will be displayed prominently for the user to play. In case of an error, the video player area will instead show a formatted error message, along with two options for the user: "Update Prompt" which allows them to edit their original prompt, and "Try to Fix" which would send a request to the backend to attempt an automated fix using the Gemini model.