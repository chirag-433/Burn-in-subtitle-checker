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
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'referer': 'https://www.youtube.com/',
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info_dict)
    return os.path.abspath(video_path)
