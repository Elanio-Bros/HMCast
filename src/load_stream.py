import os
from . import config
from .Models import Playlist_Files, Catalog_Files
from datetime import datetime
import ffmpeg
import m3u8
import threading as thread
import shutil

playlist = []


def __ffmpge_io(video, play_file):
    
    input_video = ffmpeg.input(video, **{
        "readrate": 1}
    )
    
    #Get Original Framrate
    probe = ffmpeg.probe(video,cmd=config.FFPROBE_PATH)
    framerate = probe['streams'][0]['r_frame_rate']
    framerate = eval(framerate)

    # Trim video from selected area
    trimmed_audio = input_video.filter_('atrim', start='00:00:09', end='00:01:07').filter_('asetpts', 'PTS-STARTPTS')
    input_video = input_video.trim(start='00:00:09', end='00:01:07').setpts('PTS-STARTPTS').concat(trimmed_audio, a=1)
    
    # Set Stream
    input_video.output("{}/stream.m3u8".format(config.DEFAULT_PATH), format='hls', **
                                                  {
        "threads": 2,
        "crf": 20,
        'preset': 'veryfast',
        "acodec": "aac",
        "vcodec": "libx264",
        "movflags": "+faststart",
        'tune': 'zerolatency',
        'bf': 1,
        'sc_threshold': 0,
        'keyint_min': 50,
        'g': 50,
        'r': framerate,
        "segment_list_flags": "+live",
        "hls_segment_type": "mpegts",
        "hls_flags": "delete_segments+append_list+omit_endlist+split_by_time",
        "hls_delete_threshold": 9,
        "hls_list_size": 10,
        "hls_time": 5,
        "remove_at_exit": 0,
        "allowed_extensions": "ALL",
        "hls_allow_cache": 0,
        "hls_segment_filename": "{}/{}".format(config.DEFAULT_PATH, "stream_%d.ts"),
        'master_pl_name': 'hls.m3u8',
    }).global_args("-hide_banner").run(cmd=config.FFMPEG_PATH)


def __after_play(play_file):

    Catalog_Files.update({"watched": 1}).where(
        Catalog_Files.id == play_file['file_id']).execute()

    dir = '{}/{}'.format(config.TEMP_PATH, play_file['file'])

    if os.path.exists(dir):
        os.remove(dir)

    temp_playlist = "{}/temp_stream.m3u8".format(config.DEFAULT_PATH)
    shutil.copyfile(
        "{}/stream.m3u8".format(config.DEFAULT_PATH), temp_playlist)

    if (os.path.exists(temp_playlist)):
        playlist = m3u8.load(temp_playlist)
        segments = [segment.uri for segment in playlist.segments]
        for file in os.listdir(config.DEFAULT_PATH):
            local_file = "{}/{}".format(config.DEFAULT_PATH, file)
            if os.path.isfile(local_file) and os.path.splitext(file)[1] == '.ts' and file not in segments:
                os.remove(local_file)
        os.remove(temp_playlist)


def get_playlist():
    global playlist
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    playlist_files = Playlist_Files.select().where(Playlist_Files.date_start ** "{}{}".format(date, "%")).order_by(
        Playlist_Files.date_start.asc()).order_by(Playlist_Files.catalog_id.asc()).dicts()

    for file in playlist_files:
        playlist.append(file)
        Playlist_Files.delete_by_id(file['id'])

    # Removi values duplicates on play
    playlist = [dict(t) for t in {tuple(d.items()) for d in playlist}]


def run_playlist():
    global playlist
    print("Start Load Playlist...")
    while True:
        playlist = [{'file': "1_t2.mp4"}]
        if len(playlist) >= 1:
            for key, play_file in enumerate(playlist):
                try:
                    dir = '{}/{}'.format(config.TEMP_PATH, play_file['file'])
                    if os.path.exists(dir):
                        print("Process Midia:", dir)
                        __ffmpge_io(dir, play_file)

                        # del playlist[key]

                        # thread.Thread(target=__after_play, args=[play_file]).start()

                except Exception as e:
                    print("Erro:", e)
                    print("Midia:", play_file['file'])
                    break
