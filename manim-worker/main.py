import os
import subprocess
import uuid
import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class Code(BaseModel):
    code: str

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "manim-studio-worker"}

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

@app.get("/video/{path:path}")
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

@app.post("/render")
async def render_video(code: Code):
    """Render Manim code to video"""
    render_id = str(uuid.uuid4())
    temp_media_dir = "/tmp/manim_temp"
    scene_file = f"scene_{render_id}.py"
    
    try:
        # Save code to temporary file
        with open(scene_file, "w") as f:
            f.write(code.code)
        
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
        
        return {"video_path": relative_path, "render_id": render_id}
        
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