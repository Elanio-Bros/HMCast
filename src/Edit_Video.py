from moviepy.editor import VideoFileClip, concatenate_videoclips
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip

def cutout(video, start, end):
    if (end >= video.duration):
        end = video.duration
    return concatenate_videoclips([video.subclip(0, start), video.subclip(end, video.duration)], method='compose')


def include_video_personality(clip: VideoFileClip, video: str, start: int, end: int):
    clip1 = clip.subclip(0, start)
    personality_video = VideoFileClip(video)
    clip2 = clip.subclip(end-(end-start), clip.duration)
    return concatenate_videoclips([clip1, personality_video, clip2], method='compose')
