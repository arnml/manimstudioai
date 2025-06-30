# Integrating with Manim Studio AI Backend

This document provides instructions for a frontend application, such as one hosted on Bolt.new, to interact with the deployed Manim Studio AI backend services.

## API Base URL

All API endpoints are relative to the following base URL:

`https://manim-studio-backend-952720044146.us-central1.run.app`

## Endpoints

### 1. Health Check

- **Endpoint:** `/health`
- **Method:** `GET`
- **Description:** Verifies that the backend service is running.
- **Success Response (200 OK):**
  ```json
  {
    "status": "healthy",
    "service": "manim-studio-backend"
  }
  ```

### 2. Generate Manim Code

This endpoint accepts a text prompt and uses the Gemini AI model to generate Python code for a Manim animation.

- **Endpoint:** `/generate`
- **Method:** `POST`
- **Headers:**
  - `Content-Type`: `application/json`
- **Request Body:**
  ```json
  {
    "prompt": "A string describing the animation to be created."
  }
  ```
- **Example Request Body:**
  ```json
  {
    "prompt": "Create a simple animation of a square transforming into a circle."
  }
  ```
- **Success Response (200 OK):**
  The response will contain the generated Manim code.
  ```json
  {
    "code": "from manim import *\n\nclass SquareToCircle(Scene):\n    def construct(self):\n        square = Square()\n        circle = Circle()\n        self.play(Create(square))\n        self.play(Transform(square, circle))\n        self.play(FadeOut(square))"
  }
  ```
- **Error Response (422 Unprocessable Entity):**
  If the request body is invalid.
  ```json
  {
    "detail": [
      {
        "type": "missing",
        "loc": ["body", "prompt"],
        "msg": "Field required"
      }
    ]
  }
  ```

### Frontend JavaScript Example

Here is an example of how to call the `/generate` endpoint using the `fetch` API in JavaScript.

```javascript
async function generateAnimationCode(promptText) {
  const url = 'https://manim-studio-backend-952720044146.us-central1.run.app/generate';
  
  const payload = {
    prompt: promptText
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      // Handle HTTP errors
      const errorData = await response.json();
      console.error('Error response from server:', errorData);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Generated Code:', data.code);
    return data;
  } catch (error) {
    console.error('There was a problem with the fetch operation:', error);
  }
}

// Example usage:
generateAnimationCode('A red square rotating in the center of the screen.');
```

### WebSocket for Real-time Rendering

For a more interactive experience, the backend also provides a WebSocket connection to stream the results of code generation and video rendering. Refer to the `README.md` for more details on the WebSocket events.

```