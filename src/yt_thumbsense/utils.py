from pytube import YouTube


def is_valid_youtube_video(video_id: str):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        _ = YouTube(url)
        return True
    except Exception:
        return False
