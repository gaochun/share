#! N:\Python27\python.exe
# -*- coding: utf-8 -*-

from util import *
import shutil

dirs_check = [u'026']
dir_root = u'e:/storage/顾诗云'
ffmpeg = 'D:/software/active/ffmpeg/bin/ffmpeg.exe'


def setup():
    backup_dir(dir_root)

def process():
    for dir_check in dirs_check:
        if not os.path.exists(dir_check):
            continue

        dir_photo_good = dir_check + u'月照片好'
        ensure_dir(dir_photo_good)
        dir_photo_all = dir_check + u'月照片全'
        ensure_dir(dir_photo_all)
        dir_video_1080 = dir_check + u'月视频1080'
        ensure_dir(dir_video_1080)
        dir_video_720 = dir_check + u'月视频720'
        ensure_dir(dir_video_720)

        files_src = os.listdir(dir_check)
        for file_src in files_src:
            file_src_suffix = file_src[-4:].upper()
            file_src_path = dir_check + '/' + file_src
            if file_src_suffix == '.MOV':
                file_dest = file_src.replace(file_src[-4:], '.MP4')
            else:
                file_dest = file_src

            if file_src_suffix == '.JPG':
                file_dest_path = dir_photo_all + '/' + file_dest
                if not os.path.exists(file_dest_path):
                    shutil.move(file_src_path, file_dest_path)
                else:
                    warning(file_dest_path + ' already exists')
            elif file_src_suffix == '.MP4' or file_src_suffix == '.MOV':
                # handle 1080p
                file_dest_path = dir_video_1080 + '/' + file_dest
                if not os.path.exists(file_dest_path):
                    if file_src_suffix == '.MP4':
                        shutil.move(file_src_path, file_dest_path)
                    elif file_src_suffix == '.MOV':
                        info('Convert file ' + file_src_path + ' to ' + file_dest_path)
                        cmd = (ffmpeg + ' -i ' + file_src_path + ' -qscale 0 -s hd1080 -f mp4 ' + file_dest + ' 2>>NUL').encode(sys.getfilesystemencoding())
                        execute(cmd, show_cmd=False)
                        os.rename(file_dest, file_dest_path)

                # handle 720p
                file_src_path = file_dest_path
                file_dest_path = dir_video_720 + '/' + file_dest
                if not os.path.exists(file_dest_path):
                    cmd = (ffmpeg + ' -i ' + file_src_path + ' -qscale 0 -s hd720 -f mp4 ' + file_dest + ' 2>>NUL').encode(sys.getfilesystemencoding())
                    info('Convert file ' + file_src_path + ' (1080P) to ' + file_dest_path + ' (720P)')
                    execute(cmd, show_cmd=False)
                    os.rename(file_dest, file_dest_path)


if __name__ == '__main__':
    setup()
    process()
