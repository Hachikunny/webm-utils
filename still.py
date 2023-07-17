#!/usr/bin/python3

"""
Create webms with still images and an audio track in the background.
"""

import argparse, shutil, sys, subprocess

if not shutil.which("ffmpeg"):
	print("ffmpeg not detected; aborting.", file=sys.stderr)
	sys.exit(1)
if not shutil.which("ffprobe"):
	print("ffprobe not detected; aborting.", file=sys.stderr)
	sys.exit(2)

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--image", required=True)
parser.add_argument("-a", "--audio", required=True)
parser.add_argument("-o", "--output", required=True)
parser.add_argument("-s", "--size", type=int)
parser.add_argument("-b", "--bitrate", default=96, type=int)
parser.add_argument("--vp9", action="store_true")
args = parser.parse_args()

duration_string = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $AUDIO"
duration_command = duration_string.split()
duration_command[duration_command.index("$AUDIO")] = args.audio
duration_process = subprocess.run(duration_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if duration_process.returncode:
	print("ffprobe failed to grab the audio duration with the following error error:\n%s" % duration_process.stderr.decode(), file=sys.stderr)
	sys.exit(3)
duration = float(duration_process.stdout)

br_video = None
if args.size:
	size_kb = args.size * 1024 * 8
	video_size_kb = size_kb - duration * args.bitrate
	br_video = video_size_kb / duration
	if video_size_kb < 0 or video_size_kb / duration == 0:
		print("Unable to fit constraints. Consider choosing a smaller bitrate or image.")
		sys.exit(4)

render_string = "ffmpeg -v error -hide_banner -stats -y -loop 1 -i $IMAGE -i $AUDIO -t %(duration)d -pix_fmt yuv420p -c:v %(video_codec)s -c:a %(audio_codec)s %(video_bitrate_cmd)s %(audio_bitrate_cmd)s $OUTPUT" % {
	"duration": duration, 
	"video_codec": "libvpx-vp9" if args.vp9 else "libvpx", 
	"audio_codec": "libopus" if args.vp9 else "libvorbis", 
	"video_bitrate_cmd": "" if not br_video else "-b:v %dk" % br_video, 
	"audio_bitrate_cmd": "-b:a %dk" % args.bitrate
}
render_command = render_string.split()
render_command[render_command.index("$IMAGE")] = args.image
render_command[render_command.index("$AUDIO")] = args.audio
render_command[render_command.index("$OUTPUT")] = args.output
render_process = subprocess.run(render_command)
if render_process.returncode:
	print("ffmpeg failed to create the video." % render_process.stderr, file=sys.stderr)
	sys.exit(3)
