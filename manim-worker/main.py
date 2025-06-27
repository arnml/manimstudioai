import os
import subprocess
import uuid
import shutil
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()

class Code(BaseModel):
    code: str

@app.get("/video/{quality}/{filename}")
async def serve_video(quality: str, filename: str):
    """Serve video files directly from temp directory"""
    try:
        # Check in temp directory first
        temp_video_path = f"/tmp/manim_temp/videos/{quality}/{filename}"
        if os.path.exists(temp_video_path):
            return FileResponse(temp_video_path, media_type="video/mp4", filename=filename)
        
        # Check in mounted media directory as fallback
        mounted_video_path = f"/app/media/videos/{quality}/{filename}"
        if os.path.exists(mounted_video_path):
            return FileResponse(mounted_video_path, media_type="video/mp4", filename=filename)
        
        raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/{scene_dir}/{quality}/{filename}")
async def serve_dynamic_scene_video(scene_dir: str, quality: str, filename: str):
    """Serve video files from dynamic scene directories (scene_<guid>)"""
    try:
        # Check in temp directory first (for scene_<guid> directories)
        temp_video_path = f"/tmp/manim_temp/videos/{scene_dir}/{quality}/{filename}"
        if os.path.exists(temp_video_path):
            file_size = os.path.getsize(temp_video_path)
            print(f"Serving dynamic scene video from: {temp_video_path}, size: {file_size} bytes")
            return FileResponse(temp_video_path, media_type="video/mp4", filename=filename)
        
        # Check in mounted media directory as fallback
        mounted_video_path = f"/app/media/videos/{scene_dir}/{quality}/{filename}"
        if os.path.exists(mounted_video_path):
            file_size = os.path.getsize(mounted_video_path)
            print(f"Serving dynamic scene video from mounted: {mounted_video_path}, size: {file_size} bytes")
            return FileResponse(mounted_video_path, media_type="video/mp4", filename=filename)
        
        print(f"Dynamic scene video file not found: {scene_dir}/{quality}/{filename}")
        raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        print(f"Error serving dynamic scene video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/scene/{quality}/{filename}")
async def serve_scene_video(quality: str, filename: str):
    """Serve scene video files directly from temp directory"""
    try:
        # Search for the file in all scene directories (including GUID-based ones)
        temp_media_dir = "/tmp/manim_temp"
        videos_dir = f"{temp_media_dir}/videos"
        
        # Look for the file in any scene directory with the specified quality
        if os.path.exists(videos_dir):
            for scene_dir in os.listdir(videos_dir):
                if scene_dir.startswith("scene"):
                    temp_video_path = f"{videos_dir}/{scene_dir}/{quality}/{filename}"
                    if os.path.exists(temp_video_path):
                        print(f"Serving video from: {temp_video_path}")
                        return FileResponse(temp_video_path, media_type="video/mp4", filename=filename)
        
        # Check in mounted media directory as fallback
        mounted_video_path = f"/app/media/videos/scene/{quality}/{filename}"
        if os.path.exists(mounted_video_path):
            print(f"Serving video from mounted: {mounted_video_path}")
            return FileResponse(mounted_video_path, media_type="video/mp4", filename=filename)
        
        # Also check the old path format
        temp_video_path = f"/tmp/manim_temp/videos/scene/{quality}/{filename}"
        if os.path.exists(temp_video_path):
            print(f"Serving video from legacy path: {temp_video_path}")
            return FileResponse(temp_video_path, media_type="video/mp4", filename=filename)
        
        print(f"Video file not found: {filename} in quality {quality}")
        raise HTTPException(status_code=404, detail="Video file not found")
    except Exception as e:
        print(f"Error serving video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/render")
async def render_video(code: Code):
    try:
        # Generate a unique GUID for this render
        render_id = str(uuid.uuid4())
        
        # Use a temporary directory for rendering, then copy to mounted volume
        temp_media_dir = "/tmp/manim_temp"
        mounted_media_dir = "/app/media"
        
        # Save the code to a temporary file with GUID
        scene_file = f"scene_{render_id}.py"
        with open(scene_file, "w") as f:
            f.write(code.code)
        
        print(f"Generated code to render (ID: {render_id}):\n{code.code}")  # Debug logging
        
        # Render the video using Manim with temporary directory
        result = subprocess.run([
            "manim", "-qm", "--format", "mp4", 
            "--media_dir", temp_media_dir, 
            scene_file
        ], capture_output=True, text=True, check=False)
        
        print(f"Manim stdout: {result.stdout}")  # Debug logging
        print(f"Manim stderr: {result.stderr}")  # Debug logging
        print(f"Manim return code: {result.returncode}")  # Debug logging
        
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"Manim rendering failed: {result.stderr}")
        
        # Find the generated video file in temp directory - search dynamically for the scene directory
        temp_video_path = None
        video_files = []
        
        # First, search for directories matching the scene file pattern
        videos_dir = f"{temp_media_dir}/videos"
        if os.path.exists(videos_dir):
            # Look for scene_<guid> directories
            scene_dirs = [d for d in os.listdir(videos_dir) if d.startswith(f"scene_{render_id}")]
            
            for scene_dir in scene_dirs:
                # Check different quality directories within the scene directory
                quality_dirs = ["720p30", "480p15", "1080p60"]
                for quality in quality_dirs:
                    path = f"{videos_dir}/{scene_dir}/{quality}"
                    if os.path.exists(path):
                        video_files = [f for f in os.listdir(path) if f.endswith(".mp4")]
                        if video_files:
                            temp_video_path = path
                            break
                
                if temp_video_path:
                    break
        
        # Fallback to old search method if dynamic search fails
        if not temp_video_path:
            possible_paths = [
                f"{temp_media_dir}/videos/scene/720p30",   # Default Manim quality
                f"{temp_media_dir}/videos/scene/480p15",   # Medium quality
                f"{temp_media_dir}/videos/scene/1080p60",  # High quality 
                f"{temp_media_dir}/videos/480p15",
                f"{temp_media_dir}/videos/720p30",
                f"{temp_media_dir}/scene/720p30",
                f"{temp_media_dir}"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    video_files = [f for f in os.listdir(path) if f.endswith(".mp4")]
                    if video_files:
                        temp_video_path = path
                        break
        
        if not temp_video_path or not video_files:
            # List all directories for debugging
            debug_info = []
            if os.path.exists(f"{temp_media_dir}/videos"):
                debug_info.append(f"Contents of {temp_media_dir}/videos: {os.listdir(f'{temp_media_dir}/videos')}")
                for item in os.listdir(f"{temp_media_dir}/videos"):
                    item_path = f"{temp_media_dir}/videos/{item}"
                    if os.path.isdir(item_path):
                        debug_info.append(f"Contents of {item_path}: {os.listdir(item_path)}")
                        for subitem in os.listdir(item_path):
                            subitem_path = f"{item_path}/{subitem}"
                            if os.path.isdir(subitem_path):
                                debug_info.append(f"Contents of {subitem_path}: {os.listdir(subitem_path)}")
            
            debug_message = "; ".join(debug_info)
            raise HTTPException(status_code=500, detail=f"Video file not found. Debug info: {debug_message}")
        
        # Get the original video filename and create GUID-based filename
        original_video_filename = video_files[0]
        temp_video_file = f"{temp_video_path}/{original_video_filename}"
        
        # Verify the original file exists and has content
        if not os.path.exists(temp_video_file):
            raise HTTPException(status_code=500, detail=f"Original video file not found: {temp_video_file}")
        
        file_size = os.path.getsize(temp_video_file)
        if file_size == 0:
            raise HTTPException(status_code=500, detail=f"Original video file is empty: {temp_video_file}")
        
        print(f"Original video file: {temp_video_file}, size: {file_size} bytes")
        
        # Create GUID-based filename with .mp4 extension
        guid_video_filename = f"{render_id}.mp4"
        
        # Extract quality directory (720p30, 480p15, etc.)
        quality_dir = temp_video_path.split('/')[-1]
        
        # Instead of copying, let's use a symlink in temp directory and serve the original file directly
        # This avoids potential corruption during copying
        original_file_for_serving = temp_video_file
        
        # Try to copy to mounted volume with GUID filename for persistence
        target_dir = f"{mounted_media_dir}/videos/scene/{quality_dir}"
        
        try:
            os.makedirs(target_dir, exist_ok=True)
            mounted_video_file = f"{target_dir}/{guid_video_filename}"
            
            # Copy the file with GUID name
            shutil.copy2(temp_video_file, mounted_video_file)
            
            # Verify the copied file
            if os.path.exists(mounted_video_file):
                copied_size = os.path.getsize(mounted_video_file)
                print(f"Successfully copied video to mounted volume: {mounted_video_file}, size: {copied_size} bytes")
                if copied_size != file_size:
                    print(f"Warning: File size mismatch! Original: {file_size}, Copied: {copied_size}")
            else:
                print(f"Failed to copy video to mounted volume: {mounted_video_file}")
        except PermissionError as e:
            print(f"Permission error copying to mounted volume: {e}")
            print("Video will be served from temp directory")
        except Exception as e:
            print(f"Error copying to mounted volume: {e}")
            print("Video will be served from temp directory")
        
        # Clean up temporary scene file
        try:
            os.remove(scene_file)
        except:
            pass
        
        # Return the path to the original video file (not the copied one)
        # The scene directory name includes the GUID, so we can serve it directly
        scene_dir_name = temp_video_path.split('/')[-2]  # Get the scene_<guid> directory name
        video_path = f"media/videos/{scene_dir_name}/{quality_dir}/{original_video_filename}"
        print(f"Generated video path: {video_path} (ID: {render_id})")  # Debug logging
        print(f"Original file: {temp_video_file}")
        return {"video_path": video_path, "render_id": render_id}
    
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Manim rendering failed: {e}")
    except Exception as e:
        print(f"Error in render_video: {str(e)}")  # Debug logging
        raise HTTPException(status_code=500, detail=str(e))
