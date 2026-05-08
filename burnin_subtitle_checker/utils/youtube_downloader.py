"""
Utility for downloading videos from YouTube and other supported sites.
"""

import logging
import os
import yt_dlp

logger = logging.getLogger(__name__)

def download_video(url: str, output_dir: str = "downloads") -> str:
    """
    Download a video from a given URL using yt-dlp.

    Args:
        url: The URL of the video to download.
        output_dir: Directory to save the downloaded video.

    Returns:
        The absolute path to the downloaded video file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': False,
        'no_warnings': True,
    }

    logger.info("Downloading video from %s...", url)
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info_dict)
        
        # If merged, the extension might have changed to mp4
        if not video_path.endswith('.mp4'):
            base, _ = os.path.splitext(video_path)
            video_path = f"{base}.mp4"
            
    logger.info("Video downloaded successfully to %s", video_path)
    return os.path.abspath(video_path)
