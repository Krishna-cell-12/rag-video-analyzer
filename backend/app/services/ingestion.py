import os
import re
import time
import yt_dlp
from faster_whisper import WhisperModel
from app.models.video import VideoMetadata
import os
from groq import Groq

# Initialize the Groq client (reads GROQ_API_KEY from environment)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def transcribe_audio_file(file_path: str) -> str:
    """Sends local audio payload to Groq Cloud for ultra-fast free transcription"""
    with open(file_path, "rb") as audio_file:
        transcription = groq_client.audio.transcriptions.create(
            file=(os.path.basename(file_path), audio_file.read()),
            model="whisper-large-v3",
        )
    return transcription.text


class VideoExtractor:
    def __init__(self):
        # Initialize Whisper locally on CPU
        self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")

    @staticmethod
    def calculate_engagement(likes: int, comments: int, views: int) -> float:
        if views == 0:
            return 0.0
        return round(((likes + comments) / views) * 100, 2)

    def _transcribe_audio(self, audio_path: str) -> str:
        """Transcribe audio file using Whisper, then clean up."""
        transcript_text = ""
        if os.path.exists(audio_path):
            try:
                segments, _ = self.whisper_model.transcribe(audio_path, beam_size=5)
                transcript_text = " ".join([segment.text for segment in segments])
            except Exception as e:
                print(f"Whisper transcription failed: {e}")
                transcript_text = "Transcript extraction failed."
            finally:
                os.remove(audio_path)  # Clean up server
        else:
            transcript_text = "Audio file could not be processed."
        return transcript_text

    def _build_ydl_opts(self, audio_filename: str, browser: str | None = None) -> dict:
        """Build yt-dlp options, optionally injecting browser cookies."""
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': audio_filename,
            'quiet': True,
            'no_warnings': False,
            # Mimic a real browser to reduce bot-detection
            'http_headers': {
                'User-Agent': (
                    'Mozilla/5.0 (X11; Linux x86_64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/125.0.0.0 Safari/537.36'
                ),
            },
            # Retry on transient network/rate-limit errors
            'retries': 5,
            'fragment_retries': 5,
            'sleep_interval': 3,
            'max_sleep_interval': 10,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        if browser:
            opts['cookiesfrombrowser'] = (browser,)
        return opts

    def _extract_with_fallback(self, url: str, audio_filename: str) -> dict:
        """
        Try to extract video info with multiple cookie strategies:
          1. cookies from Chrome  (handles 'Sign in to confirm you\'re not a bot')
          2. cookies from Firefox
          3. cookies from Chromium
          4. no cookies (public/unauthenticated)
        Raises the last exception if all strategies fail.
        """
        browsers = ['chrome', 'firefox', 'chromium', None]
        last_error = None

        for browser in browsers:
            try:
                ydl_opts = self._build_ydl_opts(audio_filename, browser)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                return info  # success — stop trying
            except yt_dlp.utils.DownloadError as e:
                last_error = e
                err_str = str(e)
                # Only retry with next cookie source for auth/rate-limit errors
                if any(kw in err_str for kw in [
                    '429', 'Too Many Requests',
                    'Sign in to confirm',
                    'bot', 'cookies',
                ]):
                    label = browser if browser else 'no-cookies'
                    print(f"[yt-dlp] Strategy '{label}' failed: {err_str[:120]}. Trying next…")
                    time.sleep(2)  # brief pause before next attempt
                    continue
                # Unrelated error — raise immediately
                raise
            except Exception as e:
                last_error = e
                raise

        # All strategies exhausted
        raise RuntimeError(
            f"YouTube extraction failed after trying all cookie strategies. "
            f"Last error: {last_error}\n\n"
            "HINT: Log into YouTube in your Chrome/Firefox browser on this machine, "
            "then restart the server. The app will automatically use your session cookies."
        )

    def extract_youtube(self, url: str) -> VideoMetadata:
        audio_filename = "temp_yt_audio"

        # 1. Download audio & basic metadata (with cookie fallback chain)
        info = self._extract_with_fallback(url, audio_filename)

        video_id = info.get('id', 'yt_video')
        views = info.get('view_count', 0) or 1
        likes = info.get('like_count', 0) or 0
        comments = info.get('comment_count', 0) or 0
        creator = info.get('uploader', 'Unknown_Creator')

        # 2. Transcribe locally using Whisper
        actual_audio_path = f"{audio_filename}.mp3"
        transcript_text = self._transcribe_audio(actual_audio_path)

        return VideoMetadata(
            video_id=video_id,
            platform="youtube",
            creator=creator,
            views=views,
            likes=likes,
            comments=comments,
            engagement_rate=self.calculate_engagement(likes, comments, views),
            transcript=transcript_text
        )

    def extract_instagram(self, url: str) -> VideoMetadata:
        audio_filename = "temp_insta_audio"

        # 1. Download audio file & basic metadata (with browser cookie fallback)
        info = self._extract_with_fallback(url, audio_filename)

        video_id = info.get('id', 'insta_video')
        views = info.get('view_count', 0) or 1
        likes = info.get('like_count', 0) or 0
        comments = info.get('comment_count', 0) or 0
        creator = info.get('uploader', 'Unknown_Creator')

        # 2. Transcribe locally using Whisper
        actual_audio_path = f"{audio_filename}.mp3"
        transcript_text = self._transcribe_audio(actual_audio_path)

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