import praw
import os
import glob
from redvid import Downloader
import moviepy.editor as mp
import json


def get_videopath():
    list_of_files = glob.glob('./videos/*.mp4')
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def get_img_dim(w_, h_, width = None, height = None):
    dim = None
    w = w_
    h = h_
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    return dim


# Returns [path, post title, top comment] for all downloaded subreddit posts
def download_videos(subreddit, time, limit, start_at):
    paths = []
    reddit = praw.Reddit(
        client_id= os.environ.get('CLIENT_ID'),
        client_secret= os.environ.get('CLIENT_SECRET'),
        password=os.environ.get('PASSWORD'),
        user_agent = os.environ.get('CLIENT_USERAGENT'),
        username = os.environ.get('CLIENT_USERNAME'),
    )
    top_submissions = reddit.subreddit(subreddit).top(time, limit=limit + start_at)
    for submission in top_submissions:
        top_comment = ''
        if submission.is_video:
            for top_level_comment in submission.comments:
                top_comment = top_level_comment.body
                break
            reddit = Downloader(max_q=True)
            reddit.url = submission.url
            reddit.path = './videos'
            reddit.download()
            paths.append([get_videopath(), submission.title, top_comment])
    return paths[start_at:]


def create_video_info_file(video, video_number):
    dictionary = {
        "title": video[1],
        "top_comment": video[2],
    }
    directory = str(video_number)
    file_name = video[1][:20] + ".json"
    file_path = os.path.join(directory, file_name)
    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
    try:
        with open(file_path, "w+") as outfile:
            json.dump(dictionary, outfile)
        print(f"File '{file_path}' created successfully.")
    except Exception as e:
        print(f"Error creating file '{file_path}': {e}")


def resize_videos(video_path, video_title, video_number):
    clip = mp.VideoFileClip(video_path)
    clip_resized = clip.resize(width=1080)
    dim = clip_resized.size
    margins = (1920 - dim[1])/2

    txt_clip_duration = clip_resized.duration
    if clip_resized.duration > 6:
        txt_clip_duration = 6

    clip_resized = clip_resized.margin(top=int(margins), bottom=int(margins), color=(0, 0, 0))
    txt_clip = mp.TextClip(txt=video_title, font='Arial-Bold', fontsize=45,
                           stroke_width=4, bg_color='white', color='black',
                           size=(900, None), method='caption').set_duration(txt_clip_duration).set_pos(('center', 300))

    clip_resized = mp.CompositeVideoClip([clip_resized, txt_clip])
    clip_resized.write_videofile("./" + str(video_number) + "/" + video_title[:20] + '.mp4', threads=12)


if __name__ == '__main__':
    videos = download_videos('PublicFreakout', 'week', 3, 2)
    video_number = 0
    for video in videos:
        create_video_info_file(video, video_number)
        try:
            resize_videos(video[0], video[1], video_number)
        except Exception as error:
            print("An error with video:", video_number, ":", error)  # An error occurred: name 'x' is not defined
        video_number += 1


