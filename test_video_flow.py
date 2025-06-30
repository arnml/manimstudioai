#!/usr/bin/env python3
"""
Test script to verify complete video generation and access flow
"""
import requests
import json
import time

BASE_URL = "https://manim-studio-backend-952720044146.us-central1.run.app"

def test_render_and_get_video():
    """Test the complete flow: render code -> get video"""
    
    # Step 1: Submit code for rendering
    render_url = f"{BASE_URL}/render-code"
    code_payload = {
        "code": """from manim import *

class TestVideoScene(Scene):
    def construct(self):
        text = Text("Video Test", font_size=48, color=BLUE)
        circle = Circle(radius=1, color=RED)
        circle.next_to(text, DOWN, buff=0.5)
        
        self.play(Write(text))
        self.play(Create(circle))
        self.play(circle.animate.set_color(GREEN))
        self.wait(2)
"""
    }
    
    headers = {"Content-Type": "application/json"}
    
    print("🎬 Submitting code for rendering...")
    try:
        response = requests.post(render_url, json=code_payload, headers=headers)
        print(f"✅ Render request status: {response.status_code}")
        print(f"📋 Response: {response.json()}")
        
        if response.status_code == 200:
            print("⏳ Waiting 30 seconds for video generation...")
            time.sleep(30)
            
            # Test some common video paths that might exist
            test_paths = [
                "media/videos/TestVideoScene/720p30/TestVideoScene.mp4",
                "media/videos/GeneratedScene/720p30/GeneratedScene.mp4", 
                "media/videos/scene/720p30/scene.mp4"
            ]
            
            print("🔍 Testing video access paths...")
            for path in test_paths:
                video_url = f"{BASE_URL}/{path}"
                print(f"Testing: {video_url}")
                
                video_response = requests.head(video_url)
                print(f"  Status: {video_response.status_code}")
                
                if video_response.status_code == 200:
                    print(f"  ✅ Video found! Size: {video_response.headers.get('content-length', 'unknown')} bytes")
                    print(f"  📹 Content-Type: {video_response.headers.get('content-type', 'unknown')}")
                    return video_url
                elif video_response.status_code == 404:
                    print(f"  ❌ Video not found at this path")
                else:
                    print(f"  ⚠️  Unexpected status: {video_response.status_code}")
            
            print("❌ No videos found at tested paths")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during request: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Testing deployed app video generation and access...")
    print(f"🌐 Base URL: {BASE_URL}")
    print("-" * 60)
    
    video_url = test_render_and_get_video()
    
    if video_url:
        print(f"\n🎉 SUCCESS! Video available at: {video_url}")
    else:
        print(f"\n❌ FAILED: Could not access generated video")