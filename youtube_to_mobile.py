from pytube import YouTube
import moviepy.editor as mp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import SRTFormatter
from moviepy.video.tools.subtitles import SubtitlesClip

def get_youtube_video(link):
    try:
        # object creation using YouTube
        yt = YouTube(link)
    except:
        print("Connection Error")
    # to set the name of the file
    try:
        # downloading the video
        yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution')[-1].download()
        return yt.video_id, yt.title
    except:
        print("Error downloading:", yt.title)
    return -1, -1


def get_youtube_video_subtitles(video_id):
    # Create formatter object
    formatter = SRTFormatter()
    # Get list of transcripts
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    # Get english auto-generated transcript
    transcript = transcript_list.find_generated_transcript(['en']).fetch()
    # Format transcript into SRT
    srt_formatted_transcript = formatter.format_transcript(transcript)
    # Create SRT formatted transcript
    with open("./subtitle.srt", 'w') as f:
        f.write(srt_formatted_transcript + "\n")


def create_subtitle_clip():
    stroke_width = 12
    generator = lambda txt: mp.TextClip(txt.upper(),
                                        size=(900, None),
                                        method='caption',
                                        font='Segoe-UI-Bold',
                                        fontsize=50,
                                        color='white')

    subs = SubtitlesClip('subtitle.srt', generator)
    subtitles_clip = SubtitlesClip(subs, generator).set_pos(('center', 'center'))

    generator = lambda txt: mp.TextClip(txt.upper(),
                                        size=(900 + stroke_width, None),
                                        stroke_width=stroke_width,
                                        stroke_color='black',
                                        method='caption',
                                        font='Segoe-UI-Bold',
                                        fontsize=50,
                                        color='black')
    subs = SubtitlesClip('subtitle.srt', generator)
    subtitles_clip_margin = SubtitlesClip(subs, generator).set_pos(('center', 'center'))
    stroked_text_clip = mp.CompositeVideoClip([subtitles_clip_margin, subtitles_clip], size=(1080, 1920))
    return stroked_text_clip


def create_title_clip(video_title, margin_center):
    title_clip = mp.TextClip(video_title.upper(),
                size=(900, None),
                method='caption',
                font='Segoe-UI-Bold',
                fontsize=55,
                color='white').set_pos(('center', margin_center))
    return title_clip


def create_part_clip(part_number, part_position):
    part_clip = mp.TextClip(part_number.upper(),
                size=(900, None),
                method='caption',
                font='Segoe-UI-Bold',
                fontsize=62,
                color='black').set_pos(('center', part_position))
    return part_clip


if __name__ == '__main__':
    video_url = ""
    video_id, video_title = get_youtube_video(video_url)
    subtitles = get_youtube_video_subtitles(video_id)
    subtitles_clip = create_subtitle_clip()

    # Open both clips, secondary content and main content
    clip_youtube_video = mp.VideoFileClip(video_title + '.mp4')
    clip_secondary = mp.VideoFileClip('./background_videos/background.mp4').without_audio()

    # Set duration of secondary clip and subtitles to duration of primary content
    clip_secondary = clip_secondary.subclip(0, clip_youtube_video.duration)
    subtitles_clip = subtitles_clip.subclip(0, clip_youtube_video.duration)

    # Resize both to a width of 1080 and height of main content
    clip_youtube_video = clip_youtube_video.resize(width=1080)
    clip_secondary = clip_secondary.crop(x1=0, y1=((1920 - clip_youtube_video.size[1] * 2)/2) + clip_youtube_video.size[1] - 400,
                                         x2=1080, y2=clip_secondary.size[1]-200)

    # Combine the clips together
    clips = [[clip_youtube_video], [clip_secondary]]
    final_clips = mp.clips_array(clips)

    # Add margins to top
    margin = (1920 - final_clips.size[1])
    final_clips = final_clips.margin(top=int(margin), bottom=0, color=(0, 0, 0))

    # Composite subtitles (add subtitles)
    final_clips = mp.CompositeVideoClip([final_clips, subtitles_clip])

    # Split video into parts
    video_length = 60
    number_of_parts = final_clips.duration / video_length # Get number of parts to be split
    total_video_time = final_clips.duration # Set total video time
    if(number_of_parts > 1.50): # Only split video if there is more than 1 and half parts
        clip_number = 0
        while(total_video_time > 0):
            # Get clip part text
            clip_part = create_part_clip("Part " + str(clip_number + 1), 1700)
            final_clips_part = final_clips.subclip(clip_number * video_length, (clip_number * video_length) + video_length)
            final_clips_part = mp.CompositeVideoClip([final_clips_part, clip_part]).set_duration(video_length)

            # Add title to video
            title_clip = create_title_clip(video_title, int(margin / 2)).set_duration(6)
            final_clips_part = mp.CompositeVideoClip([final_clips_part, title_clip])
            # Write the video out
            final_clips_part.write_videofile('final_' + str(clip_number + 1) + '.mp4', fps=30)
            clip_number += 1
    else:
        # Add title to video
        title_clip = create_title_clip(video_title, int(margin / 2)).set_duration(6)
        final_clips = mp.CompositeVideoClip([final_clips, title_clip])
        # Write the video out
        final_clips.write_videofile('final.mp4', codec='hevc_nvenc', threads=12)

