import os
import google.generativeai as genai
import socketio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_app = socketio.ASGIApp(sio, app)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class Prompt(BaseModel):
    prompt: str

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "manim-studio-backend"}

async def proxy_video_from_worker(worker_path: str, filename: str) -> StreamingResponse:
    """Helper function to proxy video content from manim-worker"""
    try:
        video_url = f"http://manim-worker:8001/{worker_path}"
        async with httpx.AsyncClient() as client:
            response = await client.get(video_url)
            response.raise_for_status()
            
            return StreamingResponse(
                iter([response.content]), 
                media_type="video/mp4",
                headers={"Content-Disposition": f"inline; filename={filename}"}
            )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=404, detail=f"Video not found: {str(e)}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

@app.get("/media/videos/{path:path}")
async def serve_video(path: str):
    """Unified endpoint to serve all video types from manim-worker"""
    # Extract filename from path
    filename = path.split("/")[-1]
    worker_path = f"video/{path}"
    return await proxy_video_from_worker(worker_path, filename)

def create_enhanced_manim_prompt(user_prompt: str) -> str:
    """Create an enhanced prompt for better Manim code generation"""
    return f"""Generate professional Manim Python code for: "{user_prompt}"

Requirements:
- Use proper spacing, positioning, and scene composition
- Include smooth animations with appropriate timing (use self.wait() between major actions)
- Position elements thoughtfully to avoid overlap
- Use colors effectively (BLUE, RED, GREEN, YELLOW, PURPLE, etc.)
- Include realistic animation durations (2-4 seconds total)
- Use Manim best practices for visual appeal
- Make animations smooth with Create(), Write(), Transform(), or FadeIn()/FadeOut()
- Position text and objects with proper margins (.to_edge(), .shift(), .next_to())
- If creating multiple objects, arrange them nicely in the scene

Output only the Python code, no explanations or markdown formatting.

Example structure:
```python
from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Your code here with proper spacing and timing
        pass
```

Generate for: {user_prompt}"""

def generate_demo_code(user_prompt: str) -> str:
    """Generate demo Manim code with better structure"""
    return f'''from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Generated animation for: {user_prompt}
        title = Text("{user_prompt[:40]}", font_size=36)
        title.to_edge(UP, buff=0.5)
        
        # Create main content with proper spacing
        circle = Circle(radius=1.5, color=BLUE, fill_opacity=0.3)
        circle.shift(LEFT * 2)
        
        square = Square(side_length=2, color=RED, fill_opacity=0.3)
        square.shift(RIGHT * 2)
        
        # Animate with proper timing
        self.play(Write(title), run_time=1.5)
        self.wait(0.5)
        
        self.play(
            Create(circle),
            Create(square),
            run_time=2
        )
        self.wait(0.5)
        
        # Transform colors smoothly
        self.play(
            circle.animate.set_color(GREEN),
            square.animate.set_color(YELLOW),
            run_time=1.5
        )
        self.wait(1)'''

def clean_gemini_response(raw_code: str) -> str:
    """Clean up markdown formatting from Gemini response"""
    code = raw_code.strip()
    
    # Remove leading markdown
    if code.startswith('```python'):
        code = code[9:].strip()
    elif code.startswith('```'):
        code = code[3:].strip()
    
    # Remove trailing markdown
    if code.endswith('```'):
        code = code[:-3].strip()
    
    # Remove any remaining backticks
    while code.startswith('`'):
        code = code[1:].strip()
    while code.endswith('`'):
        code = code[:-1].strip()
    
    return code

async def call_manim_worker(code: str) -> tuple[str, str]:
    """Call manim-worker to render video"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://manim-worker:8001/render", 
            json={"code": code}
        )
        response.raise_for_status()
        result = response.json()
        return result.get("video_path"), result.get("render_id", "")

def generate_with_gemini(user_prompt: str) -> str:
    """Generate code using Gemini API with enhanced prompt"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    enhanced_prompt = create_enhanced_manim_prompt(user_prompt)
    response = model.generate_content(enhanced_prompt)
    
    print(f"Raw Gemini response: {repr(response.text)}")
    cleaned_code = clean_gemini_response(response.text)
    print(f"Cleaned code: {repr(cleaned_code)}")
    
    return cleaned_code

@app.post("/render-code")
async def render_code(code: dict):
    """Render code directly without AI generation"""
    try:
        code_to_render = code.get("code", "")
        if not code_to_render.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        # Emit the code for transparency
        await sio.emit('code_generated', {'code': code_to_render})
        
        # Call manim-worker to render the video
        try:
            video_path, render_id = await call_manim_worker(code_to_render)
            await sio.emit('video_rendered', {
                'video_path': video_path,
                'render_id': render_id
            })
        except httpx.HTTPStatusError as e:
            await sio.emit('render_error', {'error': f"Render failed: {str(e)}"})
        except httpx.RequestError as e:
            await sio.emit('render_error', {'error': f"Connection failed: {str(e)}"})
            
        return {"status": "success", "message": "Code rendering started"}

    except Exception as e:
        print(f"Error in render_code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_code(prompt: Prompt):
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Generate code using demo mode or Gemini API
        if not api_key or api_key == "test_key_replace_with_real_key" or len(api_key) < 20:
            print(f"Running in demo mode. API key: {api_key[:10] if api_key else 'None'}...")
            code_to_render = generate_demo_code(prompt.prompt)
        else:
            code_to_render = generate_with_gemini(prompt.prompt)
        
        # Emit generated code
        await sio.emit('code_generated', {'code': code_to_render})
        
        # Call manim-worker to render the video
        try:
            video_path, render_id = await call_manim_worker(code_to_render)
            await sio.emit('video_rendered', {
                'video_path': video_path,
                'render_id': render_id
            })
        except httpx.HTTPStatusError as e:
            await sio.emit('render_error', {'error': f"Render failed: {str(e)}"})
        except httpx.RequestError as e:
            await sio.emit('render_error', {'error': f"Connection failed: {str(e)}"})
            
        return {"status": "success", "message": "Code generation started"}

    except Exception as e:
        print(f"Error in generate_code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@sio.event
async def connect(sid, environ):
    print(f"{sid}: connected")

@sio.event
async def disconnect(sid):
    print(f"{sid}: disconnected")
