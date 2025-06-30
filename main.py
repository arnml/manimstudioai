import os
import subprocess
import uuid
import shutil
import google.generativeai as genai
import socketio
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Socket.IO
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, app)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Pydantic models
class Prompt(BaseModel):
    prompt: str

class Code(BaseModel):
    code: str

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "manim-studio-unified"}

@app.get("/config")
async def config_check():
    """Check API configuration status"""
    api_key = os.getenv("GEMINI_API_KEY")
    return {
        "gemini_api_configured": bool(api_key and len(api_key.strip()) >= 10),
        "api_key_length": len(api_key) if api_key else 0,
        "mode": "production" if (api_key and len(api_key.strip()) >= 10) else "demo"
    }

# Video serving functions
def find_video_file(path_parts: list[str]) -> str:
    """Helper function to find video file in various locations"""
    search_paths = [
        f"/tmp/manim_temp/videos/{'/'.join(path_parts)}",
        f"/app/media/videos/{'/'.join(path_parts)}"
    ]
    
    # Search in scene directories if needed
    if len(path_parts) == 2:  # quality/filename pattern
        videos_dir = "/tmp/manim_temp/videos"
        if os.path.exists(videos_dir):
            for scene_dir in os.listdir(videos_dir):
                if scene_dir.startswith("scene"):
                    search_paths.append(f"{videos_dir}/{scene_dir}/{'/'.join(path_parts)}")
    
    for path in search_paths:
        if os.path.exists(path):
            return path
    
    raise HTTPException(status_code=404, detail="Video file not found")

@app.get("/media/videos/{path:path}")
async def serve_video(path: str):
    """Unified endpoint to serve all video files"""
    try:
        filename = path.split("/")[-1]
        path_parts = path.split("/")
        
        video_path = find_video_file(path_parts)
        return FileResponse(video_path, media_type="video/mp4", filename=filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Video rendering functions
def find_rendered_video(temp_media_dir: str, render_id: str) -> tuple[str, str]:
    """Find the rendered video file and return its path and relative path"""
    videos_dir = f"{temp_media_dir}/videos"
    
    if not os.path.exists(videos_dir):
        raise HTTPException(status_code=500, detail="Videos directory not found")
    
    # Look for scene directories with the render ID
    scene_dirs = [d for d in os.listdir(videos_dir) if d.startswith(f"scene_{render_id}")]
    
    for scene_dir in scene_dirs:
        for quality in ["720p30", "480p15", "1080p60"]:
            quality_path = f"{videos_dir}/{scene_dir}/{quality}"
            if os.path.exists(quality_path):
                video_files = [f for f in os.listdir(quality_path) if f.endswith(".mp4")]
                if video_files:
                    video_path = f"{quality_path}/{video_files[0]}"
                    relative_path = f"media/videos/{scene_dir}/{quality}/{video_files[0]}"
                    return video_path, relative_path
    
    # Fallback search in other locations
    fallback_paths = [
        f"{videos_dir}/scene/720p30",
        f"{videos_dir}/scene/480p15", 
        f"{videos_dir}/720p30",
        f"{videos_dir}/480p15"
    ]
    
    for path in fallback_paths:
        if os.path.exists(path):
            video_files = [f for f in os.listdir(path) if f.endswith(".mp4")]
            if video_files:
                video_path = f"{path}/{video_files[0]}"
                quality = path.split("/")[-1]
                scene_part = "scene" if "/scene/" in path else quality
                relative_path = f"media/videos/{scene_part}/{quality}/{video_files[0]}"
                return video_path, relative_path
    
    raise HTTPException(status_code=500, detail="Rendered video file not found")

def validate_manim_code(code: str) -> str:
    """Validate and fix common Manim code issues"""
    import re
    
    # Remove markdown formatting artifacts
    code = re.sub(r'^```python\s*', '', code, flags=re.MULTILINE)
    code = re.sub(r'^```\s*$', '', code, flags=re.MULTILINE)
    code = code.replace('```', '')  # Remove any remaining backticks
    
    # Check for non-existent methods
    invalid_methods = ['move_along_path', 'follow_path', 'trace_path', 'animate_along']
    
    for method in invalid_methods:
        if method in code:
            print(f"Warning: Removing invalid method '{method}' from code")
            code = code.replace(f'.{method}(', '.shift(')
    
    # Basic syntax validation
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        print(f"Syntax error detected: {e}")
        # If syntax error, return a safe fallback
        return """from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Fallback due to syntax error
        title = Text("Error in Generated Code", font_size=36, color=RED)
        title.to_edge(UP, buff=0.8)
        self.play(Write(title), run_time=2)
        self.wait(2)
"""
    
    # Check if 3D objects are used and add appropriate imports
    needs_3d = any(obj in code for obj in ['ParametricSurface', 'Surface', 'Sphere', 'Cube', 'Cylinder', 'ThreeDScene'])
    
    # Replace ParametricSurface with Surface for compatibility
    if 'ParametricSurface' in code:
        code = code.replace('ParametricSurface', 'Surface')
    
    # Ensure proper imports
    if needs_3d:
        # For 3D content, use standard imports without opengl
        required_imports = """from manim import *
import numpy as np"""
        
        if 'from manim import *' not in code:
            code = required_imports + '\n\n' + code
        else:
            # Replace basic import with 3D-enabled imports
            code = code.replace('from manim import *', required_imports)
    else:
        # For 2D content, use standard imports
        if 'from manim import *' not in code:
            code = 'from manim import *\nimport numpy as np\n\n' + code
        elif 'import numpy as np' not in code:
            code = code.replace('from manim import *', 'from manim import *\nimport numpy as np')
    
    # Handle scene class conversion for 3D content
    if needs_3d:
        # Replace Scene with ThreeDScene if 3D objects detected
        if 'class GeneratedScene(Scene):' in code:
            code = code.replace('class GeneratedScene(Scene):', 'class GeneratedScene(ThreeDScene):')
        elif 'Scene' in code and 'ThreeDScene' not in code:
            code = code.replace('Scene', 'ThreeDScene')
    
    if 'class' not in code or ('Scene' not in code and 'ThreeDScene' not in code):
        # Choose appropriate scene class based on content
        scene_class = 'ThreeDScene' if needs_3d else 'Scene'
        
        imports = """from manim import *
import numpy as np"""
        
        code = f"""{imports}

class GeneratedScene({scene_class}):
    def construct(self):
        # Generated code
        {code}
"""
    
    return code

async def render_manim_video(code: str) -> tuple[str, str]:
    """Render Manim code to video and return video_path and render_id"""
    render_id = str(uuid.uuid4())
    temp_media_dir = "/tmp/manim_temp"
    scene_file = f"scene_{render_id}.py"
    
    try:
        # Ensure temp directory exists
        os.makedirs(temp_media_dir, exist_ok=True)
        
        # Validate and clean the code
        validated_code = validate_manim_code(code)
        
        # Save code to temporary file
        with open(scene_file, "w") as f:
            f.write(validated_code)
        
        # Render with Manim
        result = subprocess.run([
            "manim", "-qm", "--format", "mp4", 
            "--media_dir", temp_media_dir, 
            scene_file
        ], capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Manim rendering failed: {result.stderr}")
        
        # Find and return the rendered video
        video_path, relative_path = find_rendered_video(temp_media_dir, render_id)
        
        # Optional: Copy to persistent storage
        try:
            mounted_dir = f"/app/media/videos/{render_id}"
            os.makedirs(mounted_dir, exist_ok=True)
            shutil.copy2(video_path, f"{mounted_dir}/{render_id}.mp4")
        except Exception as e:
            print(f"Warning: Could not copy to persistent storage: {e}")
        
        return relative_path, render_id
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temporary scene file
        try:
            os.remove(scene_file)
        except:
            pass

# Code generation functions
def create_enhanced_manim_prompt(user_prompt: str) -> str:
    """
    Creates a highly-structured and enhanced prompt for generating container-ready Manim code.

    This prompt instructs the AI to:
    1.  Generate professional, didactic Manim code.
    2.  Ensure the code is runnable within the `manimcommunity/manim:latest` Docker image.
    3.  Strictly avoid any overlapping text or objects.
    4.  Include all necessary imports and dependencies within the script.
    """
    return f"""
You are an expert Manim programmer creating a Python script for a mathematics education video.
Your response MUST be ONLY the raw Python code for the Manim scene. Do not add any explanations, markdown backticks, or other text.

**Execution Environment Constraint:**
* **Target Image:** The code will be executed inside a Docker container using the `manimcommunity/manim:latest` image.
* **Dependencies:** All necessary imports (`manim`, `numpy`, etc.) must be included at the top of the script. The script must be self-contained.

---

### **CRITICAL RULE: AVOID ALL OVERLAPPING TEXT AND OBJECTS**
This is the most important rule. Text and objects must NEVER be rendered on top of each other.
* **Positioning:** Use layout managers to guarantee separation.
    * Use `.to_edge()` or `.to_corner()` for titles and peripheral elements.
    * Use `.next_to(object, DIRECTION, buff=0.5)` to position new elements relative to existing ones. A `buff` of at least `0.5` is recommended.
    * For lists or sequences of text/equations, use `VGroup(...).arrange(DOWN, buff=0.8)` to stack them vertically with ample spacing.
* **Validation:** Before adding a new element, mentally check if its position could conflict with any existing element. Ensure animations do not cause temporary overlaps.

---

### **Educational Animation Structure**
1.  **Title:** Start with a clear title (e.g., `Text("My Title", font_size=48)`). Position it at the top using `.to_edge(UP, buff=1)`.
2.  **Sequential Introduction:** Introduce concepts and objects one by one. Use `Write`, `Create`, or `FadeIn`. Do not show everything at once.
3.  **Logical Flow:** Animate mathematical steps logically. Use `Transform` or `ReplacementTransform` to show the evolution of equations.
4.  **Emphasis:** Use color or animations like `Indicate()` to highlight key parts.
5.  **Pacing:** Add `self.wait(1)` after each key step to allow for comprehension.
6.  **Clean Exit:** Conclude the scene by removing all objects, for example, with `self.play(FadeOut(Group(*self.mobjects)))`.

---

### **Technical & Style Guidelines**

**Scene and Imports:**
* **2D Scene:** Use `class GeneratedScene(Scene):` and include these imports:
    ```python
    from manim import *
    import numpy as np
    ```
* **3D Scene:** Use `class GeneratedScene(ThreeDScene):` and include these imports:
    ```python
    from manim import *
    from manim.opengl import * # If using ParametricSurface
    import numpy as np
    ```

**Object & Text Formatting:**
* **Math Content:** ALWAYS use `MathTex(r"...")` for all formulas, variables, and mathematical symbols for professional typesetting.
* **Font Sizes:** Title: 48, Main Content: 36, Labels/Annotations: 24.
* **Positioning:** Position objects relative to each other or the screen edges. Avoid hardcoding `(x, y, z)` coordinates.

**Animation Rules:**
* **Runtime:** Use a default `run_time=1.5`.
* **Smoothness:** Use `.animate` syntax for property changes (e.g., `self.play(my_object.animate.shift(RIGHT))`).

---

**Final Task:**
Generate a complete, runnable Manim Python script based on the following user request. Remember: ONLY output the code.

**User Prompt:** "{user_prompt}"
"""

def generate_demo_code(user_prompt: str) -> str:
    """Generate demo Manim code with safe, reliable animations"""
    return f'''from manim import *

class GeneratedScene(Scene):
    def construct(self):
        # Demo animation for: {user_prompt}
        title = Text("Demo Animation", font_size=36, color=WHITE)
        title.to_edge(UP, buff=0.5)
        
        # Create simple shapes with safe positioning
        circle = Circle(radius=1, color=BLUE, fill_opacity=0.5)
        circle.shift(LEFT * 2)
        
        square = Square(side_length=1.5, color=RED, fill_opacity=0.5)
        square.shift(RIGHT * 2)
        
        # Simple, reliable animations
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        
        self.play(Create(circle), run_time=1)
        self.play(Create(square), run_time=1)
        self.wait(0.5)
        
        # Safe color transformations
        self.play(circle.animate.set_color(GREEN), run_time=1)
        self.play(square.animate.set_color(YELLOW), run_time=1)
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

def generate_with_gemini(user_prompt: str) -> str:
    """Generate code using Gemini API with enhanced prompt"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    enhanced_prompt = create_enhanced_manim_prompt(user_prompt)
    response = model.generate_content(enhanced_prompt)
    
    print(f"Raw Gemini response: {repr(response.text)}")
    cleaned_code = clean_gemini_response(response.text)
    print(f"Cleaned code: {repr(cleaned_code)}")
    
    return cleaned_code

# API endpoints
@app.post("/render-code")
async def render_code(code: Code):
    """Render code directly without AI generation"""
    try:
        code_to_render = code.code
        if not code_to_render.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        # Emit the code for transparency
        await sio.emit('code_generated', {'code': code_to_render})
        
        # Render the video locally
        try:
            video_path, render_id = await render_manim_video(code_to_render)
            await sio.emit('video_rendered', {
                'video_path': video_path,
                'render_id': render_id
            })
        except HTTPException as e:
            await sio.emit('render_error', {'error': f"Render failed: {str(e.detail)}"})
        except Exception as e:
            await sio.emit('render_error', {'error': f"Unexpected error: {str(e)}"})
            
        return {"status": "success", "message": "Code rendering started"}

    except Exception as e:
        print(f"Error in render_code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate")
async def generate_code(prompt: Prompt):
    """Generate code using AI and render video"""
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        
        # Generate code using demo mode or Gemini API
        if not api_key or api_key == "test_key_replace_with_real_key" or len(api_key.strip()) < 10:
            print(f"Running in demo mode. API key present: {bool(api_key)}, length: {len(api_key) if api_key else 0}")
            code_to_render = generate_demo_code(prompt.prompt)
        else:
            print(f"Using Gemini API with key: {api_key[:8]}...")
            code_to_render = generate_with_gemini(prompt.prompt)
        
        # Emit generated code
        await sio.emit('code_generated', {'code': code_to_render})
        
        # Render the video locally
        try:
            video_path, render_id = await render_manim_video(code_to_render)
            await sio.emit('video_rendered', {
                'video_path': video_path,
                'render_id': render_id
            })
        except HTTPException as e:
            await sio.emit('render_error', {'error': f"Render failed: {str(e.detail)}"})
        except Exception as e:
            await sio.emit('render_error', {'error': f"Unexpected error: {str(e)}"})
            
        return {"status": "success", "message": "Code generation started"}

    except Exception as e:
        print(f"Error in generate_code: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Socket.IO events
@sio.event
async def connect(sid, environ):
    print(f"{sid}: connected")

@sio.event
async def disconnect(sid):
    print(f"{sid}: disconnected")

# For backwards compatibility, also serve videos at /video/{path} endpoint
@app.get("/video/{path:path}")
async def serve_video_alt(path: str):
    """Alternative video serving endpoint for backwards compatibility"""
    return await serve_video(path)