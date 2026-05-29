import os
import yt_dlp
from faster_whisper import WhisperModel
from app.models.video import VideoMetadata

class VideoExtractor:
    def __init__(self):
        # Initialize Whisper locally on CPU
        self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

    @staticmethod
    def calculate_engagement(likes: int, comments: int, views: int) -> float:
        if views == 0:
            return 0.0
        return round(((likes + comments) / views) * 100, 2)

    # ... [Keep existing extract_youtube method exactly as it is] ...

    def extract_instagram(self, url: str) -> VideoMetadata:
        audio_filename = "temp_insta_audio"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_filename,
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        # 1. Download audio file & basic metadata
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
        video_id = info.get('id', 'insta_video')
        views = info.get('view_count', 0) or 1
        likes = info.get('like_count', 0)
        comments = info.get('comment_count', 0)
        creator = info.get('uploader', 'Unknown_Creator')

        # 2. Transcribe locally using Whisper
        actual_audio_path = f"{audio_filename}.mp3"
        transcript_text = ""
        
        if os.path.exists(actual_audio_path):
            try:
                segments, _ = self.whisper_model.transcribe(actual_audio_path, beam_size=5)
                transcript_text = " ".join([segment.text for segment in segments])
            except Exception as e:
                print(f"Whisper transcription failed: {e}")
                transcript_text = "Transcript extraction failed."
            finally:
                os.remove(actual_audio_path) # Clean up server
        else:
            transcript_text = "Audio file could not be processed."

        return VideoMetadata(
            video_id=video_id,
            platform="instagram",
            creator=creator,
            views=views,
            likes=likes,
            comments=comments,
            engagement_rate=self.calculate_engagement(likes, comments, views),
            transcript=transcript_text
        )