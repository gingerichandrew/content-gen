import pvleopard
import moviepy.editor as mp
from moviepy.video.tools.subtitles import SubtitlesClip
import os
from TTS.api import TTS


leopard = pvleopard.create(access_key=os.environ.get('ACCESS_KEY'),)
os.environ['COQUI_STUDIO_TOKEN'] = 'WOqjcGRb0reNatbZ2yPxHMRzCoveEMbexqDQskZ4GLbkFpGY0n9dfRjwRbofwmF0'

def second_to_timecode(x: float) -> str:
    hour, x = divmod(x, 3600)
    minute, x = divmod(x, 60)
    second, x = divmod(x, 1)
    millisecond = int(x * 1000.)

    return '%.2d:%.2d:%.2d,%.3d' % (hour, minute, second, millisecond)

def to_srt( words: [pvleopard.Leopard.Word],
        endpoint_sec: float = 0.15,
        length_limit: [int] = 16) -> str:
    def _helper(end: int) -> None:
        lines.append("%d" % section)
        lines.append(
            "%s --> %s" %
            (
                second_to_timecode(words[start].start_sec),
                second_to_timecode(words[end].end_sec)
            )
        )
        lines.append(' '.join(x.word for x in words[start:(end + 1)]))
        lines.append('')

    lines = list()
    section = 0
    start = 0
    for k in range(1, len(words)):
        if ((words[k].start_sec - words[k - 1].end_sec) >= endpoint_sec) or \
                (length_limit is not None and (k - start) >= length_limit):
            _helper(k - 1)
            start = k
            section += 1
    _helper(len(words) - 1)

    return '\n'.join(lines)


with open('script.txt', encoding="utf8") as file:
    data = file.read().replace('\n', '')

tts_api = TTS()

tts = TTS("tts_models/multilingual/multi-dataset/bark", gpu=True)

tts.tts_to_file(text=data, emotion="Neutral", file_path="output.wav", speed=.8)


if __name__ == '__main__':
    # Open video clip
    clip = mp.VideoFileClip('./background_videos/bg_1_lq.mp4')

    # Transcribe audio and create SRT
    transcript, words = leopard.process_file('./output.wav')
    with open("./subtitle.srt", 'w') as f:
        f.write(to_srt(words))
        f.write("\n")
    print(mp.TextClip.list('font'))
    # Generate subtitles from srt file
    generator = lambda txt: mp.TextClip(txt.upper(), font='Segoe-UI-Bold-Italic', fontsize=56, color='white')
    subs = SubtitlesClip('subtitle.srt', generator)
    subtitles = SubtitlesClip(subs, generator).set_pos(('center', 'center'))

    # Add subtitles to video
    clip = mp.CompositeVideoClip([clip, subtitles])

    # Add narration to video
    audio_clip = mp.AudioFileClip("output.wav")
    clip = clip.set_audio(audio_clip)
    # Set length of video to length of audio
    clip = clip.subclip(0, audio_clip.duration)
    # Write video out
    clip.write_videofile('final.mp4', threads=12)
