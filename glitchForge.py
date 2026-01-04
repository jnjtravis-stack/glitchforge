import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import uuid
import subprocess
from catboxpy.catbox import CatboxClient
import functools
import time
import string
import psutil

# -----------------------------
# CONFIG
# -----------------------------
TOKEN = "replace ts"  # ⚠️ REPLACE WITH YOUR ACTUAL BOT TOKEN
GUILD_ID = optional  # Optional: Set to your server ID (e.g., 123456789012345678) for faster slash command sync
OWNER_ID = REPLACE TS  # ⚠️ SET THIS TO YOUR DISCORD USER ID (e.g., 123456789012345678) for owner privileges

# ⚠️ ADD FRIEND IDs HERE (comma-separated Discord user IDs)
FRIEND_IDS = [replaceme1, replaceme2, replaceme3]  # Example: [123456789012345679, 987654321098765432, 555666777888999000]

# -----------------------------
# WINDOWS USB DETECTION & TEMP DIR SETUP
# -----------------------------
def find_usb_glitchforge_folder_windows():
    """Windows-specific function to find a USB drive with a 'GlitchForge' folder."""
    for partition in psutil.disk_partitions():
        if 'removable' in partition.opts.lower():
            drive_path = partition.mountpoint
            glitchforge_path = os.path.join(drive_path, "GlitchForge")
            if os.path.exists(glitchforge_path) and os.path.isdir(glitchforge_path):
                return glitchforge_path
    return None

def get_temp_dir():
    """Get the appropriate temp directory (USB or local) for Windows."""
    usb_path = find_usb_glitchforge_folder_windows()
    if usb_path:
        print(f"📁 Using USB temp folder: {usb_path}")
        timestamp = int(time.time())
        session_path = os.path.join(usb_path, f"session_{timestamp}")
        os.makedirs(session_path, exist_ok=True)
        return session_path
    
    default_temp = "temp"
    print(f"📁 USB not found, using local temp folder: {default_temp}")
    os.makedirs(default_temp, exist_ok=True)
    return default_temp

TEMP_DIR = get_temp_dir()
LOG_FILE = os.path.join(TEMP_DIR, "FFMPEGLog.log")
print(f"✅ Temp directory set to: {TEMP_DIR}")

# -----------------------------
# HELPER FUNCTION: Check if user is owner or friend
# -----------------------------
def is_owner(user):
    """Check if the user is the bot owner."""
    if OWNER_ID:
        # Check by user ID
        return user.id == OWNER_ID
    return False

def is_friend(user):
    """Check if the user is a friend of the owner."""
    return user.id in FRIEND_IDS

def is_privileged(user):
    """Check if the user is owner or friend (gets same perks)."""
    return is_owner(user) or is_friend(user)

# -----------------------------
# PRESETS
# -----------------------------
PRESETS = {
    "custom": {},
    "bgm74": {
        "video": "negate,hue=h=180,lenscorrection=0.5:0.5:0.3:0.9,lenscorrection=0.5:0.5:-0.1:-0.3,lenscorrection=0.5:0.5:-0.1:-0.3",
        "audio": "[0:a]rubberband=formant=634:pitch=2^(-3/12)[a1];[0:a]rubberband=formant=634:pitch=2^(2/12)[a2];[a1][a2]amix=2,volume=1.75,atrim=0.01[outa]",
        "audio_label": "outa"
    },
    "bgm74_vegas": {
        "video": "huesaturation=hue=180:strength=100,negate,format=yuv444p,scale=ih:ih,geq='p((W*0.5)+(X-W*0.5)/(lte((hypot(X-W*0.5,Y-H*0.5)),(min(W,H)*0.5))*(1+(2.5)*2*atan(atan(atan(1-(hypot(X-W*0.5,Y-H*0.5))/(min(W,H)*0.5))^2)))+gt((hypot(X-W*0.5,Y-H*0.5)),(min(W,H)*0.5))*1),(H*0.5)+(Y-H*0.5)/(lte((hypot(X-W*0.5,Y-H*0.5)),(min(W,H)*0.5))*(1+(2.5)*2*atan(atan(atan(1-(hypot(X-W*0.5,Y-H*0.5))/(min(W,H)*0.5))^2)))+gt((hypot(X-W*0.5,Y-H*0.5)),(min(W,H)*0.5))*1))',scale=iw:ih,setsar=1:1,format=yuv420p,format=yuv444p,scale=ih:ih,geq='p((W*0.5)+(X-W*0.5)/(lte((hypot(X-W*0.5,Y-H*0.5)),(min(W,H)*0.555))*(1+(-0.75)*2*atan(atan(atan(1-(hypot(X-W*0.5,Y-H*0.5))/(min(W,H)*0.555))^2)))+gt((hypot(X-W*0.5,Y-H*0.5)),(min(W,H)*0.555))*1),(H*0.5)+(Y-H*0.5)/(lte((hypot(X-W*0.5,Y-H*0.5)),(min(W,H)*0.555))*(1+(-0.75)*2*atan(atan(atan(1-(hypot(X-W*0.5,Y-H*0.5))/(min(W,H)*0.555))^2)))+gt((hypot(X-W*0.5,Y-H*0.5)),(min(W,H)*0.555))*1))',scale=iw:ih,setsar=1:1,format=yuv420p,colorchannelmixer=0:0:1:0:0:1:0:0:1:0:0:0:0:0:0:1,format=yuv420p,format=bgr32,hue=h=180,colorchannelmixer=0:0:1:0:0:1:0:0:1:0:0:0:0:0:0:1,format=yuv420p,format=rgb24,hue=h=180",
        "audio": "[0:a]rubberband=phase=7950000/4.83:pitch=2^(-3/12):detector=2.14748e+09/56:transients=crisp:pitchq=consistency[a1];[0:a]rubberband=phase=7950000/4.83:pitch=2^(2/12):detector=2.14748e+09/56:transients=crisp:pitchq=consistency[a2];[a1][a2]amix=2:normalize=0[outa]",
        "audio_label": "outa"
    },
    "91dxi": {
        "video": "format=yuv444p,scale=iw/2.5:ih/2.5,geq='p(X,abs(Y+tan(sin(cos(T*3000/10+X*0/100)*0))))',geq='p(X,abs(Y+tan(sin(cos(T*-2000/10+X*0/100)*0))))',geq='p(X,abs(Y+tan(sin(cos(T*-5000+140/10+X*0/100)*1000))))',geq='p(X,abs(Y+atan(sin(cos(T*8000/10+X*0/100)*0))))',geq='p(X,abs(Y+tan(sin(cos(T*4000+45/10+X*0/100)*1000))))',geq='p(X,(Y+cos(sin(cos(T*30000/10+X*0/100)*0))))',geq='p(X,(Y+tan(sin(cos(T*20000/10+X*0/25)*0))))',geq='p(X,abs(Y+tan(cos(sin(T*6000/10+X*0/100)*0))))',scale=iw*2.5:ih*2.5,format=yuv444p,scale=854:480,geq='p(X,floor(Y+sin(319/100+X*0/100)*100))',scale=iw:ih,format=yuv420p,negate,huesaturation=63:saturation=0.9:strength=100",
        "audio": "[0:a]rubberband=pitch=2^(-3.5/12):window=short:transients=crisp:detector=2.14748e+09/4.9[a1];[0:a]rubberband=pitch=2^(0/12):window=short:transients=crisp:detector=2.14748e+09/4.9[a2];[a1][a2]amix=2,volume=2,atrim=0.01[outa]",
        "audio_label": "outa"
    },
    "reverse": {"video": "-vf reverse", "audio": "-af areverse"},
    "v916": {"video": "scale='min(1080,iw)':-1:force_original_aspect_ratio=decrease,pad=1080:1920:(1080-iw)/2:(1920-ih)/2", "audio": ""},
    "v169": {"video": "scale='min(1920,iw)':-1:force_original_aspect_ratio=decrease,pad=1920:1080:(1920-iw)/2:(1080-ih)/2", "audio": ""},
    "v11": {"video": "scale='min(1080,iw)':-1:force_original_aspect_ratio=decrease,pad=1080:1080:(1080-iw)/2:(1080-ih)/2", "audio": ""},
    "xm159": {
        "video": "split=3[a][b][t];[a]format=gray,curves=r=0/1 0.5/1 1/0:g=0/1 0.5/0 1/0:b=0/1 0.5/1 1/0[aa];[b]format=gray,curves=all=0/1 0.5/1 1/1[bb];[aa][bb]alphamerge[c];[t][c]overlay,format=yuv420p",
        "audio": "[0:a]rubberband=pitch=2^(7/12):window=short:transients=crisp:detector=2.14748e+09/4.9[a1];[0:a]rubberband=pitch=2^(-5/12):window=short:transients=crisp:detector=2.14748e+09/4.9[a2];[a1][a2]amix=2,volume=2,atrim=0.02[outa]",
        "audio_label": "outa"
    },
    "pgrender": {"video": "colorspace=iall=bt470bg:all=bt470bg:space=bt709,format=yuvj420p", "audio": ""},
    "nsb_ffmpeg1": {
        "video": "colorchannelmixer=0:0:1:0:0:1:0:0:1:0:0:0:0.0:0:1,hue=h=100",
        "audio": "[0:a]rubberband=pitch=2^(-4.5/12):window=short:transients=crisp:detector=2.14748e+09/4.9:pitchq=consistency[a1];[0:a]rubberband=pitch=2^(4.5/12):window=short:transients=crisp:detector=2.14748e+09/4.9:pitchq=consistency[a2];[a1][a2]amix=2,volume=2[outa]",
        "audio_label": "outa"
    },
    "corruption": {"video": "scale=480:320,setsar=1:1", "audio": "volume=50dB"},
    "gm100": {
        "video": "colorchannelmixer=0:0:1:0:0:1:0:0:1:0:0:0,hue=h=100,crop=iw/2:ih:0:0,split[left][tmp];[tmp]hflip[right];[left][right]hstack,format=yuv444p,scale=640:-1,geq='p(X+sin(0/10+Y/30)*27,(Y+sin(0/10+X*1.8/100)*15))',scale=iw:ih,format=yuv420p",
        "audio": "[0:a]rubberband=pitch=2^(-5/12):window=short:transients=crisp:detector=2.14748e+09/4.9[a1];[0:a]rubberband=pitch=2^(-1/12):window=short:transients=crisp:detector=2.14748e+09/4.9[a2];[a1][a2]amix=2,volume=2,atrim=0.02[outa]",
        "audio_label": "outa"
    },
    "gm16": {
        "video": "hue=h=-150,huesaturation=-0.12:strength=100,negate,hflip",
        "audio": "[0:a]rubberband=pitch=2^(0/12):window=short:transients=crisp:detector=2.14748e+09/4.9,atrim=-0.01[a1];[0:a]rubberband=pitch=2^(-3/12):window=short:transients=crisp:detector=2.14748e+09/4.9[a2];[a1][a2]amix=2,volume=1.5,atrim=0.02,highpass=f=20[outa]",
        "audio_label": "outa"
    },
    "gm7": {
        "video": "negate",
        "audio": "[0:a]rubberband=formant=712923000:pitch=2^(0/12)[a1];[0:a]rubberband=formant=712923000:pitch=2^(3/12)[a2];[a1][a2]amix=2,volume=2,atrim=0.02[outa]",
        "audio_label": "outa"
    },
    "gm305": {
        "video": "huesaturation=-120:strength=100,hue=s=1.0124",
        "audio": "[0:a]rubberband=formant=712923000:pitch=2^(12/12)[a1];[0:a]rubberband=formant=712923000:pitch=2^(-7/12)[a2];[a1][a2]amix=2,volume=2,atrim=0.01[outa]",
        "audio_label": "outa"
    },
    "autovocoding": {"video": None, "audio": None, "audio_label": "outa"}
}

# -----------------------------
# LOGGING & FFMPEG FUNCTIONS
# -----------------------------
def append_log(cmd, stderr):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\nCOMMAND: {' '.join(cmd)}\n")
        f.write(stderr.decode('utf-8', errors='ignore'))
        f.write("\n" + "="*80 + "\n")

def build_ffmpeg_cmd(input_path, output_path, preset_name, custom_args=None, export_length=None):
    cmd = ["ffmpeg", "-y", "-i", input_path,
           "-c:v", "libx264", "-preset", "ultrafast", "-crf", "18", "-threads", "0"]

    if export_length is not None:
        cmd += ["-t", str(export_length)]

    if preset_name == "custom":
        if not custom_args:
            raise ValueError("Custom args required for preset=custom")
        import shlex
        args_list = shlex.split(custom_args, posix=False)
        cleaned_args = []
        i = 0
        while i < len(args_list):
            arg = args_list[i]
            if arg in ["-filter_complex", "-vf", "-af"] and i + 1 < len(args_list):
                filter_arg = args_list[i + 1]
                if (filter_arg.startswith('"') and filter_arg.endswith('"')) or \
                   (filter_arg.startswith("'") and filter_arg.endswith("'")):
                    filter_arg = filter_arg[1:-1]
                cleaned_args.append(arg)
                cleaned_args.append(filter_arg)
                i += 2
            else:
                cleaned_args.append(arg)
                i += 1
        cmd += cleaned_args
    elif preset_name == "autovocoding":
        tmp_lut = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_lut.cube")
        lut_url = "https://files.catbox.moe/3txa0q.cube"  # Simplified URL
        
        # Download using Python instead of curl
        import urllib.request
        try:
            urllib.request.urlretrieve(lut_url, tmp_lut)
            abs_lut = os.path.abspath(tmp_lut)
            # Windows path fix
            lut_path = abs_lut.replace("\\", "\\\\")
            cmd += ["-vf", f"lut3d=file='{lut_path}'", "-pix_fmt", "yuv420p"]
        except Exception as e:
            print(f"Failed to download LUT: {e}")
            cmd += ["-vf", "format=yuv420p"]
    else:
        preset = PRESETS.get(preset_name)
        if preset and preset.get("video"):
            cmd += ["-vf", preset["video"]]
        if preset and preset.get("audio"):
            cmd += ["-filter_complex", preset["audio"]]
            cmd += ["-map", "0:v", "-map", f"[{preset['audio_label']}]"]
        elif preset and preset.get("audio") == "":
            # Handle cases where audio is explicitly empty
            cmd += ["-an"]
        else:
            # Default: copy audio
            cmd += ["-c:a", "copy"]

    cmd += [output_path]
    return cmd

async def run_ffmpeg(input_path, output_path, preset_name, custom_args=None, export_length=None):
    cmd = build_ffmpeg_cmd(input_path, output_path, preset_name, custom_args, export_length)
    
    # Debug: Print command
    print(f"Running FFmpeg command: {' '.join(cmd)}")
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    append_log(cmd, stderr)
    
    if proc.returncode != 0:
        error_msg = stderr.decode('utf-8', errors='ignore')[:500]
        raise RuntimeError(f"FFmpeg failed with return code {proc.returncode}: {error_msg}")
    
    return output_path

# -----------------------------
# SNIP FUNCTIONS
# -----------------------------
async def get_video_duration(input_path: str) -> float:
    """Get the duration of a video file using ffprobe."""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode == 0:
            return float(stdout.strip())
        else:
            print(f"ffprobe error: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"Error getting duration: {e}")
        return None

async def snip_last_seconds(input_path: str, output_path: str, seconds: float):
    """Snip the last X seconds from a video."""
    # Get video duration
    duration = await get_video_duration(input_path)
    
    if duration is None:
        raise RuntimeError("Could not determine video duration")
    
    if duration <= seconds:
        # If video is shorter than requested seconds, copy the whole video
        cmd = ['ffmpeg', '-y', '-i', input_path, '-c', 'copy', output_path]
    else:
        # Calculate start time
        start_time = duration - seconds
        
        # Use fast seeking with copy codec
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-i', input_path,
            '-t', str(seconds),
            '-c', 'copy',  # Copy codecs (no re-encoding)
            '-avoid_negative_ts', 'make_zero',
            output_path
        ]
    
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    append_log(cmd, stderr)
    
    if proc.returncode != 0:
        raise RuntimeError(f"Snip failed: {stderr.decode('utf-8', errors='ignore')[:200]}")
    
    return output_path

# -----------------------------
# CONCATENATION FUNCTION
# -----------------------------
async def concatenate_videos(input_paths: list, output_path: str):
    """
    Concatenate multiple video files using FFmpeg's concat demuxer.
    
    Args:
        input_paths: List of paths to video files
        output_path: Path for the output concatenated video
    """
    if len(input_paths) < 2:
        raise ValueError("Need at least 2 videos to concatenate")
    
    # Create a list file for FFmpeg
    list_file = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_concat_list.txt")
    
    with open(list_file, "w", encoding="utf-8") as f:
        for video_path in input_paths:
            # Use forward slashes for FFmpeg compatibility
            abs_path = os.path.abspath(video_path).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")
    
    try:
        # Use concat demuxer for faster processing (requires same codec)
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",  # Copy streams without re-encoding
            "-movflags", "+faststart",  # Optimize for web playback
            output_path
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        append_log(cmd, stderr)
        
        if proc.returncode != 0:
            # Try alternative method with re-encoding if copy fails
            print("Copy method failed, trying re-encoding method...")
            cmd2 = [
                "ffmpeg", "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", list_file,
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-crf", "23",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                output_path
            ]
            
            proc2 = await asyncio.create_subprocess_exec(
                *cmd2,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout2, stderr2 = await proc2.communicate()
            append_log(cmd2, stderr2)
            
            if proc2.returncode != 0:
                raise RuntimeError(f"Concatenation failed: {stderr2.decode('utf-8', errors='ignore')[:500]}")
        
        return output_path
        
    finally:
        # Clean up the list file
        try:
            os.remove(list_file)
        except:
            pass

# -----------------------------
# Catbox Upload
# -----------------------------
async def upload_to_catbox(path: str) -> str:
    def do_upload(p):
        try:
            client = CatboxClient()
            return client.upload(p)
        except Exception as e:
            return f"❌ Upload failed: {e}"
    
    try:
        url = await asyncio.get_event_loop().run_in_executor(None, functools.partial(do_upload, path))
        if isinstance(url, str) and url.startswith("http"):
            return url
        else:
            return str(url)
    except Exception as e:
        return f"❌ Upload failed: {e}"

# -----------------------------
# CREATE BOT
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"🛠️  GlitchForge online! Forging video glitches since 2025...")
    print(f"📂 Temp directory: {TEMP_DIR}")
    
    if OWNER_ID:
        try:
            owner_user = await bot.fetch_user(OWNER_ID)
            print(f"👑 Owner privileges enabled for: {owner_user.name}#{owner_user.discriminator} ({OWNER_ID})")
        except:
            print(f"👑 Owner privileges enabled for ID: {OWNER_ID}")
    
    if FRIEND_IDS:
        print(f"🤝 Friend privileges enabled for {len(FRIEND_IDS)} user(s): {FRIEND_IDS}")
    
    # Sync slash commands
    try:
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"✅ Slash commands synced to guild: {GUILD_ID}")
        else:
            await bot.tree.sync()
            print("✅ Slash commands synced globally")
    except Exception as e:
        print(f"⚠️  Could not sync slash commands: {e}")
    
    print(f"🔧 Available commands:")
    print(f"   Prefix (!): !ffmpeg, !ihtx, !last_export, !last_export_custom, !concat, !usb_status, !reload_temp, !help, !owner, !friends")
    print(f"   Slash (/): /ffmpeg, /ihtx, /last_export, /last_export_custom, /concat, /usb_status, /reload_temp, /help, /owner, /friends")
    print(f"🎨 Presets loaded: {len(PRESETS)} effects ready")

# -----------------------------
# PREFIX COMMANDS (!)
# -----------------------------
@bot.command(name="ffmpeg")
async def ffmpeg_prefix(ctx, preset: str, *, custom_args: str = None):
    """Process a video with an FFmpeg preset. Usage: !ffmpeg <preset> [custom_args]"""
    if len(ctx.message.attachments) == 0:
        await ctx.send("❌ **Drag and drop a video file into Discord, then type your command.**")
        return
    
    if preset not in PRESETS:
        await ctx.send(f"❌ Unknown preset. Available: {', '.join(PRESETS.keys())}")
        return
    
    await ctx.send(f"🛠️  Forging with preset `{preset}`...")
    
    uid = str(uuid.uuid4())
    file = ctx.message.attachments[0]
    
    # Check file size (Discord limit is 25MB, but we'll be conservative)
    # OWNER & FRIENDS BYPASS: No file size restriction for privileged users
    if file.size > 24 * 1024 * 1024 and not is_privileged(ctx.author):
        await ctx.send("❌ File too large. Please use files under 24MB.")
        return
    
    in_path = os.path.join(TEMP_DIR, f"{uid}_{file.filename}")
    out_path = os.path.join(TEMP_DIR, f"{uid}_out.mp4")
    
    try:
        await file.save(in_path)
    except Exception as e:
        await ctx.send(f"❌ Failed to save file: {e}")
        return

    try:
        await run_ffmpeg(in_path, out_path, preset, custom_args)
    except Exception as e:
        await ctx.send(f"❌ Forging failed: {e}", file=discord.File(LOG_FILE))
        try: os.remove(in_path)
        except: pass
        return

    # Send the result - CATBOX REQUIRED FOR EVERYONE OVER 8MB
    try:
        size = os.path.getsize(out_path)
        if size < 8 * 1024 * 1024:
            await ctx.send(file=discord.File(out_path))
        else:
            await ctx.send("⏳ Uploading to Catbox...")
            link = await upload_to_catbox(out_path)
            await ctx.send(f"📦 **Download link:** {link}")
    except Exception as e:
        await ctx.send(f"❌ Failed to send result: {e}")

    # Cleanup
    try: os.remove(in_path)
    except: pass
    try: os.remove(out_path)
    except: pass

@bot.command(name="ihtx")
async def ihtx_prefix(ctx, powers: int, export_length: float, preset: str, *, custom_args: str = None):
    """Run IHTX iterative effect. Usage: !ihtx <powers> <export_length> <preset> [custom_args]"""
    if len(ctx.message.attachments) == 0:
        await ctx.send("❌ **Drag and drop a video file into Discord, then type your command.**")
        return
    
    if preset not in PRESETS:
        await ctx.send(f"❌ Unknown preset. Available: {', '.join(PRESETS.keys())}")
        return
    
    # ALL USERS: 100 iterations maximum
    # OWNER & FRIENDS BYPASS: Unlimited iterations for privileged users
    max_powers = 100
    if powers > max_powers and not is_privileged(ctx.author):
        await ctx.send(f"❌ Powers limited to {max_powers} for performance reasons.")
        return
    
    await ctx.send(f"⚡ Forging {powers} iterative glitches ({export_length}s each) with preset `{preset}`...")
    
    uid = str(uuid.uuid4())
    file = ctx.message.attachments[0]
    orig = os.path.join(TEMP_DIR, f"{uid}_orig_{file.filename}")
    await file.save(orig)

    segments = []
    for i in range(powers):
        seg_out = os.path.join(TEMP_DIR, f"{uid}_seg_{i}.mp4")
        try:
            await run_ffmpeg(orig if i == 0 else segments[-1],
                             seg_out, preset, custom_args, export_length)
            segments.append(seg_out)
        except Exception as e:
            await ctx.send(f"❌ Forging failed on iteration {i+1}: {e}", file=discord.File(LOG_FILE))
            # Cleanup
            for seg in segments:
                try: os.remove(seg)
                except: pass
            try: os.remove(orig)
            except: pass
            return

    # Concatenate segments
    list_file = os.path.join(TEMP_DIR, f"{uid}_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for seg in segments:
            # Use forward slashes for FFmpeg compatibility
            abs_path = os.path.abspath(seg).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")

    final_out = os.path.join(TEMP_DIR, f"{uid}_final.mp4")
    concat_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", final_out]
    
    try:
        proc = await asyncio.create_subprocess_exec(*concat_cmd,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        append_log(concat_cmd, stderr)
        
        if proc.returncode != 0:
            raise RuntimeError("Concatenation failed")
    except Exception as e:
        await ctx.send(f"❌ Concatenation failed: {e}")
        # Cleanup
        for p in [orig, list_file] + segments:
            try: os.remove(p)
            except: pass
        return

    # Send result - CATBOX REQUIRED FOR EVERYONE OVER 8MB
    try:
        size = os.path.getsize(final_out)
        if size < 8 * 1024 * 1024:
            await ctx.send(file=discord.File(final_out))
        else:
            await ctx.send("⏳ Uploading to Catbox...")
            link = await upload_to_catbox(final_out)
            await ctx.send(f"📦 **Download link:** {link}")
    except Exception as e:
        await ctx.send(f"❌ Failed to send result: {e}")

    # Cleanup
    for p in [orig, list_file, final_out] + segments:
        try: os.remove(p)
        except: pass

@bot.command(name="last_export")
async def last_export_prefix(ctx):
    """Export the last 0.44 seconds of a video. Usage: !last_export"""
    if len(ctx.message.attachments) == 0:
        await ctx.send("❌ **Drag and drop a video file into Discord, then type `!last_export`**")
        return
    
    await ctx.send("✂️ Snipping the last 0.44 seconds...")
    
    uid = str(uuid.uuid4())
    file = ctx.message.attachments[0]
    in_path = os.path.join(TEMP_DIR, f"{uid}_{file.filename}")
    out_path = os.path.join(TEMP_DIR, f"{uid}_last_0.44s.mp4")
    
    try:
        await file.save(in_path)
    except Exception as e:
        await ctx.send(f"❌ Failed to save file: {e}")
        return
    
    try:
        await snip_last_seconds(in_path, out_path, 0.44)
    except Exception as e:
        await ctx.send(f"❌ Failed to snip video: {e}")
        try: os.remove(in_path)
        except: pass
        return
    
    # Send the result - CATBOX REQUIRED FOR EVERYONE OVER 8MB
    try:
        size = os.path.getsize(out_path)
        if size < 8 * 1024 * 1024:
            await ctx.send(file=discord.File(out_path))
        else:
            await ctx.send("⏳ Uploading to Catbox...")
            link = await upload_to_catbox(out_path)
            await ctx.send(f"📦 **Last 0.44 seconds:** {link}")
    except Exception as e:
        await ctx.send(f"❌ Failed to send result: {e}")
    
    # Cleanup
    try: os.remove(in_path); os.remove(out_path)
    except: pass

@bot.command(name="last_export_custom")
async def last_export_custom_prefix(ctx, seconds: float):
    """Export the last X seconds of a video. Usage: !last_export_custom <seconds>"""
    if len(ctx.message.attachments) == 0:
        await ctx.send(f"❌ **Drag and drop a video file into Discord, then type `!last_export_custom {seconds}`**")
        return
    
    if seconds <= 0:
        await ctx.send("❌ Seconds must be a positive number!")
        return
    
    # OWNER & FRIENDS BYPASS: No time restriction for privileged users
    max_seconds = 300 if is_privileged(ctx.author) else 60  # 5 minutes for privileged, 1 minute for others
    if seconds > max_seconds and not is_privileged(ctx.author):
        await ctx.send(f"⚠️ Warning: Clipping to maximum {max_seconds} seconds")
        seconds = min(seconds, max_seconds)
    
    await ctx.send(f"✂️ Snipping the last {seconds} seconds...")
    
    uid = str(uuid.uuid4())
    file = ctx.message.attachments[0]
    in_path = os.path.join(TEMP_DIR, f"{uid}_{file.filename}")
    out_path = os.path.join(TEMP_DIR, f"{uid}_last_{seconds}s.mp4")
    
    try:
        await file.save(in_path)
    except Exception as e:
        await ctx.send(f"❌ Failed to save file: {e}")
        return
    
    try:
        await snip_last_seconds(in_path, out_path, seconds)
    except Exception as e:
        await ctx.send(f"❌ Failed to snip video: {e}")
        try: os.remove(in_path)
        except: pass
        return
    
    # Send the result - CATBOX REQUIRED FOR EVERYONE OVER 8MB
    try:
        size = os.path.getsize(out_path)
        if size < 8 * 1024 * 1024:
            await ctx.send(file=discord.File(out_path))
        else:
            await ctx.send("⏳ Uploading to Catbox...")
            link = await upload_to_catbox(out_path)
            await ctx.send(f"📦 **Last {seconds} seconds:** {link}")
    except Exception as e:
        await ctx.send(f"❌ Failed to send result: {e}")
    
    # Cleanup
    try: os.remove(in_path); os.remove(out_path)
    except: pass

@bot.command(name="concat")
async def concat_prefix(ctx):
    """Concatenate multiple video files. Usage: !concat (attach 2+ videos)"""
    if len(ctx.message.attachments) < 2:
        await ctx.send("❌ **Need at least 2 video files to concatenate!**")
        return
    
    # ALL USERS: 25 files maximum
    # OWNER & FRIENDS BYPASS: Unlimited files for privileged users
    max_files = 25
    if len(ctx.message.attachments) > max_files and not is_privileged(ctx.author):
        await ctx.send(f"⚠️ Maximum {max_files} files allowed. Using first {max_files} files.")
        attachments = ctx.message.attachments[:max_files]
    else:
        attachments = ctx.message.attachments
    
    await ctx.send(f"🔗 Concatenating {len(attachments)} videos...")
    
    uid = str(uuid.uuid4())
    input_paths = []
    
    # Save all attachments
    for i, file in enumerate(attachments):
        # OWNER & FRIENDS BYPASS: No file size restriction for privileged users
        max_size = 24 * 1024 * 1024  # 24MB for all users
        if file.size > max_size and not is_privileged(ctx.author):
            await ctx.send(f"❌ File `{file.filename}` is too large (max {max_size//(1024*1024)}MB).")
            # Cleanup already saved files
            for path in input_paths:
                try: os.remove(path)
                except: pass
            return
        
        file_path = os.path.join(TEMP_DIR, f"{uid}_input_{i}_{file.filename}")
        try:
            await file.save(file_path)
            input_paths.append(file_path)
        except Exception as e:
            await ctx.send(f"❌ Failed to save file `{file.filename}`: {e}")
            # Cleanup
            for path in input_paths:
                try: os.remove(path)
                except: pass
            return
    
    # Output path
    out_path = os.path.join(TEMP_DIR, f"{uid}_concat.mp4")
    
    try:
        await concatenate_videos(input_paths, out_path)
    except Exception as e:
        await ctx.send(f"❌ Failed to concatenate videos: {e}")
        # Cleanup
        for path in input_paths:
            try: os.remove(path)
            except: pass
        try: os.remove(out_path)
        except: pass
        return
    
    # Send the result - CATBOX REQUIRED FOR EVERYONE OVER 8MB
    try:
        size = os.path.getsize(out_path)
        if size < 8 * 1024 * 1024:
            await ctx.send(file=discord.File(out_path))
        else:
            await ctx.send("⏳ Uploading to Catbox...")
            link = await upload_to_catbox(out_path)
            await ctx.send(f"📦 **Concatenated video:** {link}")
    except Exception as e:
        await ctx.send(f"❌ Failed to send result: {e}")
    
    # Cleanup
    for path in input_paths:
        try: os.remove(path)
        except: pass
    try: os.remove(out_path)
    except: pass

@bot.command(name="usb_status")
async def usb_status_prefix(ctx):
    """Check USB detection status."""
    usb_path = find_usb_glitchforge_folder_windows()
    current_temp = TEMP_DIR
    
    if usb_path:
        try:
            import shutil
            total, used, free = shutil.disk_usage(usb_path)
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)
            await ctx.send(
                f"✅ **USB Forge Detected!**\n"
                f"📂 Path: `{usb_path}`\n"
                f"💾 Current temp folder: `{current_temp}`\n"
                f"📊 Free space: `{free_gb:.2f} GB` / `{total_gb:.2f} GB`"
            )
        except:
            await ctx.send(
                f"✅ **USB Forge Detected!**\n"
                f"📂 Path: `{usb_path}`\n"
                f"💾 Current temp folder: `{current_temp}`"
            )
    else:
        await ctx.send(
            "❌ **No USB forge detected**\n"
            f"💾 Using local temp folder: `{current_temp}`\n\n"
            "**To use USB storage:**\n"
            "1. Connect a USB drive\n"
            "2. Create a folder named `GlitchForge` at the root\n"
            "3. Restart the bot or use `!reload_temp`"
        )

@bot.command(name="reload_temp")
async def reload_temp_prefix(ctx):
    """Reload and check for USB temp folder."""
    global TEMP_DIR, LOG_FILE
    old_temp = TEMP_DIR
    TEMP_DIR = get_temp_dir()
    LOG_FILE = os.path.join(TEMP_DIR, "FFMPEGLog.log")
    await ctx.send(f"🔄 **Forge reloaded**\nOld: `{old_temp}`\nNew: `{TEMP_DIR}`")

@bot.command(name="owner")
async def owner_prefix(ctx):
    """Check if you have owner privileges and see your limits."""
    if is_owner(ctx.author):
        await ctx.send(f"👑 **OWNER PRIVILEGES ACTIVE**\n"
                      f"User: {ctx.author.mention}\n"
                      f"ID: `{ctx.author.id}`\n\n"
                      "**Unlimited Access:**\n"
                      "• No file size restrictions (input)\n"
                      "• Unlimited iterations in !ihtx\n"
                      "• Unlimited files in !concat\n"
                      "• Unlimited time for !last_export_custom\n"
                      "• All restrictions removed\n\n"
                      "**Catbox Required For Everyone:**\n"
                      "• Files >8MB require Catbox upload")
        
        # Show current owner ID configuration
        if OWNER_ID:
            try:
                owner_user = await bot.fetch_user(OWNER_ID)
                await ctx.send(f"**Configured Owner:** {owner_user.name}#{owner_user.discriminator} (`{OWNER_ID}`)")
            except:
                await ctx.send(f"**Configured Owner ID:** `{OWNER_ID}`")
    else:
        await ctx.send("❌ **You are not the bot owner.**\n"
                      f"Your ID: `{ctx.author.id}`\n"
                      f"Configured Owner ID: `{OWNER_ID if OWNER_ID else 'Not set'}`\n\n"
                      "**Your Limits:**\n"
                      "• Input file size: 24MB\n"
                      "• ihtx iterations: 100\n"
                      "• Concat files: 25\n"
                      "• Last export custom: 60 seconds\n"
                      "• **Catbox Required:** Files >8MB")

@bot.command(name="friends")
async def friends_prefix(ctx):
    """Check if you have friend privileges and see the friend list."""
    is_friend_user = is_friend(ctx.author)
    is_owner_user = is_owner(ctx.author)
    is_privileged_user = is_privileged(ctx.author)
    
    if is_privileged_user:
        status = "👑 **OWNER**" if is_owner_user else "🤝 **FRIEND OF OWNER**"
        await ctx.send(f"{status}\n"
                      f"User: {ctx.author.mention}\n"
                      f"ID: `{ctx.author.id}`\n\n"
                      "**Unlimited Access (Same as Owner):**\n"
                      "• No file size restrictions (input)\n"
                      "• Unlimited iterations in !ihtx\n"
                      "• Unlimited files in !concat\n"
                      "• Unlimited time for !last_export_custom\n"
                      "• All restrictions removed\n\n"
                      "**Catbox Required For Everyone:**\n"
                      "• Files >8MB require Catbox upload")
        
        # Show friend list
        if FRIEND_IDS:
            friend_list = []
            for friend_id in FRIEND_IDS:
                try:
                    friend_user = await bot.fetch_user(friend_id)
                    friend_list.append(f"{friend_user.name}#{friend_user.discriminator} (`{friend_id}`)")
                except:
                    friend_list.append(f"Unknown User (`{friend_id}`)")
            
            friend_count = len(FRIEND_IDS)
            friend_text = "\n".join(friend_list)
            await ctx.send(f"**🤝 Friend List ({friend_count}):**\n{friend_text}")
        else:
            await ctx.send("**🤝 Friend List:** No friends added yet.")
    else:
        await ctx.send("❌ **You are not a friend of the owner.**\n"
                      f"Your ID: `{ctx.author.id}`\n\n"
                      "**Your Limits:**\n"
                      "• Input file size: 24MB\n"
                      "• ihtx iterations: 100\n"
                      "• Concat files: 25\n"
                      "• Last export custom: 60 seconds\n"
                      "• **Catbox Required:** Files >8MB\n\n"
                      f"**Friend IDs:** `{FRIEND_IDS}`")

@bot.command(name="help")
async def help_prefix(ctx):
    """Show all available commands and presets."""
    is_owner_user = is_owner(ctx.author)
    is_friend_user = is_friend(ctx.author)
    is_privileged_user = is_privileged(ctx.author)
    
    status = ""
    if is_owner_user:
        status = "👑"
    elif is_friend_user:
        status = "🤝"
    
    help_text = f"""
**🛠️  GlitchForge - Video Glitch Creation Bot** {status}

**📋 How to Use:**
1. **Drag and drop video file(s)** into Discord chat
2. **Type your command** in the same message:
   - `!ffmpeg <preset>` - Apply a glitch effect to one video
   - `!ihtx <powers> <seconds> <preset>` - Create iterative glitches
   - `!last_export` - Export the last 0.44 seconds
   - `!last_export_custom <seconds>` - Export the last X seconds
   - `!concat` - Concatenate 2+ videos (attach multiple files)

**📁 Available Presets ({len(PRESETS)} total):**
`{"`, `".join(PRESETS.keys())}`

**💡 Examples:**
1. Drag a video, then type: `!last_export`
2. Drag a video, then type: `!last_export_custom 2.5`
3. Drag 3 videos, then type: `!concat`

**{'👑 Owner & 🤝 Friend Privileges:' if is_privileged_user else '📊 User Limits:'}"""
    
    if is_privileged_user:
        help_text += """
• Input file size: Unlimited (privileged) vs 24MB (users)
• ihtx iterations: Unlimited (privileged) vs 100 (users)
• Concat files: Unlimited (privileged) vs 25 (users)
• Last export: Unlimited (privileged) vs 1min (users)
• **Catbox Required For Everyone:** Files >8MB"""
    else:
        help_text += """
• Input file size: 24MB max
• ihtx iterations: 100 max
• Concat files: 25 max
• Last export: 60 seconds max
• **Catbox Required:** Files >8MB"""

    help_text += """

**Other Commands:**
- `!usb_status` - Check USB storage
- `!reload_temp` - Rescan for USB
- `!owner` - Check owner status
- `!friends` - Check friend status
- `!help` - This message
"""
    await ctx.send(help_text)

# -----------------------------
# SLASH COMMANDS (/)
# -----------------------------
@bot.tree.command(name="ffmpeg", description="Forge a video with an FFmpeg preset")
@app_commands.describe(
    file="The video file to process",
    preset="Select a glitch preset",
    custom_args="Custom FFmpeg arguments (for preset=custom only)"
)
@app_commands.choices(preset=[app_commands.Choice(name=k, value=k) for k in PRESETS.keys()])
async def ffmpeg_slash(interaction: discord.Interaction, file: discord.Attachment, preset: app_commands.Choice[str], custom_args: str = None):
    await interaction.response.defer(thinking=True)
    
    if preset.value not in PRESETS:
        await interaction.followup.send(f"❌ Unknown preset. Available: {', '.join(PRESETS.keys())}")
        return
    
    # OWNER & FRIENDS BYPASS: No file size restriction for privileged users
    max_size = 24 * 1024 * 1024  # 24MB for all users
    if file.size > max_size and not is_privileged(interaction.user):
        await interaction.followup.send(f"❌ File too large. Please use files under {max_size//(1024*1024)}MB.")
        return
    
    # Process the file (similar to prefix command)
    uid = str(uuid.uuid4())
    in_path = os.path.join(TEMP_DIR, f"{uid}_{file.filename}")
    out_path = os.path.join(TEMP_DIR, f"{uid}_out.mp4")
    
    try:
        await file.save(in_path)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to save file: {e}")
        return
    
    try:
        await run_ffmpeg(in_path, out_path, preset.value, custom_args)
    except Exception as e:
        await interaction.followup.send(f"❌ Forging failed: {e}", file=discord.File(LOG_FILE))
        try: os.remove(in_path)
        except: pass
        return
    
    # Send result - CATBOX REQUIRED FOR EVERYONE OVER 8MB
    try:
        size = os.path.getsize(out_path)
        if size < 8 * 1024 * 1024:
            await interaction.followup.send(file=discord.File(out_path))
        else:
            link = await upload_to_catbox(out_path)
            await interaction.followup.send(f"📦 **Download link:** {link}")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to send result: {e}")
    
    # Cleanup
    try: os.remove(in_path); os.remove(out_path)
    except: pass

@bot.tree.command(name="ihtx", description="Forge iterative glitch effects")
@app_commands.describe(
    file="The video file to process",
    powers="Number of iterations/powers",
    export_length="Length of each glitch segment in seconds",
    preset="Select a glitch preset",
    custom_args="Custom FFmpeg arguments (for preset=custom only)"
)
@app_commands.choices(preset=[app_commands.Choice(name=k, value=k) for k in PRESETS.keys()])
async def ihtx_slash(interaction: discord.Interaction, file: discord.Attachment, powers: int, export_length: float, preset: app_commands.Choice[str], custom_args: str = None):
    await interaction.response.defer(thinking=True)
    
    if preset.value not in PRESETS:
        await interaction.followup.send(f"❌ Unknown preset. Available: {', '.join(PRESETS.keys())}")
        return
    
    # ALL USERS: 100 iterations maximum
    # OWNER & FRIENDS BYPASS: Unlimited iterations for privileged users
    max_powers = 100
    if powers > max_powers and not is_privileged(interaction.user):
        await interaction.followup.send(f"❌ Powers limited to {max_powers} for performance reasons.")
        return
    
    uid = str(uuid.uuid4())
    orig = os.path.join(TEMP_DIR, f"{uid}_orig_{file.filename}")
    
    try:
        await file.save(orig)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to save file: {e}")
        return

    segments = []
    for i in range(powers):
        seg_out = os.path.join(TEMP_DIR, f"{uid}_seg_{i}.mp4")
        try:
            await run_ffmpeg(orig if i == 0 else segments[-1],
                             seg_out, preset.value, custom_args, export_length)
            segments.append(seg_out)
        except Exception as e:
            await interaction.followup.send(f"❌ Forging failed on iteration {i+1}: {e}", file=discord.File(LOG_FILE))
            # Cleanup
            for seg in segments:
                try: os.remove(seg)
                except: pass
            try: os.remove(orig)
            except: pass
            return

    # Concatenate segments
    list_file = os.path.join(TEMP_DIR, f"{uid}_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for seg in segments:
            abs_path = os.path.abspath(seg).replace("\\", "/")
            f.write(f"file '{abs_path}'\n")

    final_out = os.path.join(TEMP_DIR, f"{uid}_final.mp4")
    concat_cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", final_out]
    
    try:
        proc = await asyncio.create_subprocess_exec(*concat_cmd,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        append_log(concat_cmd, stderr)
        
        if proc.returncode != 0:
            raise RuntimeError("Concatenation failed")
    except Exception as e:
        await interaction.followup.send(f"❌ Concatenation failed: {e}")
        # Cleanup
        for p in [orig, list_file] + segments:
            try: os.remove(p)
            except: pass
        return

    # Send result - CATBOX REQUIRED FOR EVERYONE OVER 8MB
    try:
        size = os.path.getsize(final_out)
        if size < 8 * 1024 * 1024:
            await interaction.followup.send(file=discord.File(final_out))
        else:
            link = await upload_to_catbox(final_out)
            await interaction.followup.send(f"📦 **Download link:** {link}")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to send result: {e}")

    # Cleanup
    for p in [orig, list_file, final_out] + segments:
        try: os.remove(p)
        except: pass

@bot.tree.command(name="last_export", description="Export the last 0.44 seconds of a video")
@app_commands.describe(file="The video file to process")
async def last_export_slash(interaction: discord.Interaction, file: discord.Attachment):
    await interaction.response.defer(thinking=True)
    
    await interaction.followup.send("✂️ Snipping the last 0.44 seconds...")
    
    uid = str(uuid.uuid4())
    in_path = os.path.join(TEMP_DIR, f"{uid}_{file.filename}")
    out_path = os.path.join(TEMP_DIR, f"{uid}_last_0.44s.mp4")
    
    try:
        await file.save(in_path)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to save file: {e}")
        return
    
    try:
        await snip_last_seconds(in_path, out_path, 0.44)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to snip video: {e}")
        try: os.remove(in_path)
        except: pass
        return
    
    # Send the result - CATBOX REQUIRED FOR EVERYONE OVER 8MB
    try:
        size = os.path.getsize(out_path)
        if size < 8 * 1024 * 1024:
            await interaction.followup.send(file=discord.File(out_path))
        else:
            await interaction.followup.send("⏳ Uploading to Catbox...")
            link = await upload_to_catbox(out_path)
            await interaction.followup.send(f"📦 **Last 0.44 seconds:** {link}")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to send result: {e}")
    
    # Cleanup
    try: os.remove(in_path); os.remove(out_path)
    except: pass

@bot.tree.command(name="last_export_custom", description="Export the last X seconds of a video")
@app_commands.describe(
    file="The video file to process",
    seconds="Number of seconds to snip from the end"
)
async def last_export_custom_slash(interaction: discord.Interaction, file: discord.Attachment, seconds: float):
    await interaction.response.defer(thinking=True)
    
    if seconds <= 0:
        await interaction.followup.send("❌ Seconds must be a positive number!")
        return
    
    # OWNER & FRIENDS BYPASS: No time restriction for privileged users
    max_seconds = 300 if is_privileged(interaction.user) else 60
    if seconds > max_seconds and not is_privileged(interaction.user):
        await interaction.followup.send(f"⚠️ Warning: Clipping to maximum {max_seconds} seconds")
        seconds = min(seconds, max_seconds)
    
    await interaction.followup.send(f"✂️ Snipping the last {seconds} seconds...")
    
    uid = str(uuid.uuid4())
    in_path = os.path.join(TEMP_DIR, f"{uid}_{file.filename}")
    out_path = os.path.join(TEMP_DIR, f"{uid}_last_{seconds}s.mp4")
    
    try:
        await file.save(in_path)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to save file: {e}")
        return
    
    try:
        await snip_last_seconds(in_path, out_path, seconds)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to snip video: {e}")
        try: os.remove(in_path)
        except: pass
        return
    
    # Send the result - CATBOX REQUIRED FOR EVERYONE OVER 8MB
    try:
        size = os.path.getsize(out_path)
        if size < 8 * 1024 * 1024:
            await interaction.followup.send(file=discord.File(out_path))
        else:
            await interaction.followup.send("⏳ Uploading to Catbox...")
            link = await upload_to_catbox(out_path)
            await interaction.followup.send(f"📦 **Last {seconds} seconds:** {link}")
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to send result: {e}")
    
    # Cleanup
    try: os.remove(in_path); os.remove(out_path)
    except: pass

@bot.tree.command(name="concat", description="Concatenate multiple video files")
async def concat_slash(interaction: discord.Interaction):
    """
    Note: Discord doesn't support multiple file attachments in slash commands directly.
    This command accepts a comma-separated list of message IDs that contain the files.
    Alternative approach: Use the message with attachments directly.
    """
    await interaction.response.defer(thinking=True)
    is_privileged_user = is_privileged(interaction.user)
    
    await interaction.followup.send("❌ **For concatenation, please use the prefix command: `!concat`**\n"
                                   "Drag and drop 2+ video files, then type `!concat` in the same message.\n\n"
                                   f"{'👑🤝 As a privileged user, you can upload unlimited files at once!' if is_privileged_user else '📊 You can upload up to 25 files at once.'}")

@bot.tree.command(name="usb_status", description="Check USB forge detection status")
async def usb_status_slash(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    
    usb_path = find_usb_glitchforge_folder_windows()
    current_temp = TEMP_DIR
    
    if usb_path:
        try:
            import shutil
            total, used, free = shutil.disk_usage(usb_path)
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)
            await interaction.followup.send(
                f"✅ **USB Forge Detected!**\n"
                f"📂 Path: `{usb_path}`\n"
                f"💾 Current temp folder: `{current_temp}`\n"
                f"📊 Free space: `{free_gb:.2f} GB` / `{total_gb:.2f} GB`"
            )
        except:
            await interaction.followup.send(
                f"✅ **USB Forge Detected!**\n"
                f"📂 Path: `{usb_path}`\n"
                f"💾 Current temp folder: `{current_temp}`"
            )
    else:
        await interaction.followup.send(
            "❌ **No USB forge detected**\n"
            f"💾 Using local temp folder: `{current_temp}`\n\n"
            "**To use USB storage:**\n"
            "1. Connect a USB drive\n"
            "2. Create a folder named `GlitchForge` at the root\n"
            "3. Restart the bot or use `/reload_temp`"
        )

@bot.tree.command(name="reload_temp", description="Reload and check for USB forge")
async def reload_temp_slash(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    global TEMP_DIR, LOG_FILE
    old_temp = TEMP_DIR
    TEMP_DIR = get_temp_dir()
    LOG_FILE = os.path.join(TEMP_DIR, "FFMPEGLog.log")
    await interaction.followup.send(f"🔄 **Forge reloaded**\nOld: `{old_temp}`\nNew: `{TEMP_DIR}`")

@bot.tree.command(name="owner", description="Check if you have owner privileges")
async def owner_slash(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    
    if is_owner(interaction.user):
        await interaction.followup.send(f"👑 **OWNER PRIVILEGES ACTIVE**\n"
                                      f"User: {interaction.user.mention}\n"
                                      f"ID: `{interaction.user.id}`\n\n"
                                      "**Unlimited Access:**\n"
                                      "• No file size restrictions (input)\n"
                                      "• Unlimited iterations in /ihtx\n"
                                      "• Unlimited files in !concat (prefix only)\n"
                                      "• Unlimited time for /last_export_custom\n"
                                      "• All restrictions removed\n\n"
                                      "**Catbox Required For Everyone:**\n"
                                      "• Files >8MB require Catbox upload")
    else:
        await interaction.followup.send("❌ **You are not the bot owner.**\n"
                                      f"Your ID: `{interaction.user.id}`\n"
                                      f"Configured Owner ID: `{OWNER_ID if OWNER_ID else 'Not set'}`\n\n"
                                      "**Your Limits:**\n"
                                      "• Input file size: 24MB\n"
                                      "• ihtx iterations: 100\n"
                                      "• Concat files: 25\n"
                                      "• Last export: 60 seconds\n"
                                      "• **Catbox Required:** Files >8MB")

@bot.tree.command(name="friends", description="Check if you have friend privileges")
async def friends_slash(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)
    
    is_friend_user = is_friend(interaction.user)
    is_owner_user = is_owner(interaction.user)
    is_privileged_user = is_privileged(interaction.user)
    
    if is_privileged_user:
        status = "👑 **OWNER**" if is_owner_user else "🤝 **FRIEND OF OWNER**"
        await interaction.followup.send(f"{status}\n"
                                      f"User: {interaction.user.mention}\n"
                                      f"ID: `{interaction.user.id}`\n\n"
                                      "**Unlimited Access (Same as Owner):**\n"
                                      "• No file size restrictions (input)\n"
                                      "• Unlimited iterations in /ihtx\n"
                                      "• Unlimited files in !concat (prefix only)\n"
                                      "• Unlimited time for /last_export_custom\n"
                                      "• All restrictions removed\n\n"
                                      "**Catbox Required For Everyone:**\n"
                                      "• Files >8MB require Catbox upload")
    else:
        await interaction.followup.send("❌ **You are not a friend of the owner.**\n"
                                      f"Your ID: `{interaction.user.id}`\n\n"
                                      "**Your Limits:**\n"
                                      "• Input file size: 24MB\n"
                                      "• ihtx iterations: 100\n"
                                      "• Concat files: 25\n"
                                      "• Last export: 60 seconds\n"
                                      "• **Catbox Required:** Files >8MB\n\n"
                                      f"**Friend IDs:** `{FRIEND_IDS}`")

@bot.tree.command(name="help", description="Show all available commands and presets")
async def help_slash(interaction: discord.Interaction):
    is_owner_user = is_owner(interaction.user)
    is_friend_user = is_friend(interaction.user)
    is_privileged_user = is_privileged(interaction.user)
    
    status = ""
    if is_owner_user:
        status = "👑"
    elif is_friend_user:
        status = "🤝"
    
    help_text = f"""
**🛠️  GlitchForge - Video Glitch Creation Bot** {status}

**📋 How to Use:**
• **Prefix commands (!)**: Drag & drop video(s), then type commands like:
  - `!last_export` - Last 0.44 seconds
  - `!last_export_custom 2.5` - Last 2.5 seconds
  - `!concat` - Concatenate multiple videos (attach 2+ files)
• **Slash commands (/)** must have file attached when typing the command

**🎨 Available Presets ({len(PRESETS)} total):**
`{"`, `".join(PRESETS.keys())}`

**{'👑 Owner & 🤝 Friend Privileges:' if is_privileged_user else '📊 User Limits:'}"""
    
    if is_privileged_user:
        help_text += """
• Input file size: Unlimited (privileged) vs 24MB (users)
• ihtx iterations: Unlimited (privileged) vs 100 (users)
• Concat files: Unlimited (privileged) vs 25 (users)
• Last export: Unlimited (privileged) vs 1min (users)
• **Catbox Required For Everyone:** Files >8MB"""
    else:
        help_text += """
• Input file size: 24MB max
• ihtx iterations: 100 max
• Concat files: 25 max
• Last export: 60 seconds max
• **Catbox Required:** Files >8MB"""

    help_text += """

**💡 Note for concatenation:**
Use the prefix command `!concat` with multiple attachments for best results.
"""
    await interaction.response.send_message(help_text)

# -----------------------------
# RUN THE BOT
# -----------------------------
if __name__ == "__main__":
    # Check if required packages are installed
    required_packages = ['discord.py', 'catboxpy', 'psutil']
    try:
        import discord, catboxpy, psutil
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Install with: pip install discord.py catboxpy psutil")
        exit(1)
    
    # Check if FFmpeg is installed
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("❌ FFmpeg is not installed or not in PATH!")
        print("Download FFmpeg from: https://ffmpeg.org/download.html")
        exit(1)
    
    # Check if ffprobe is installed
    try:
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
    except FileNotFoundError:
        print("❌ ffprobe is not installed or not in PATH!")
        print("ffprobe is usually included with FFmpeg installation.")
        exit(1)
    
    # Warn if owner ID is not set
    if not OWNER_ID:
        print("⚠️  WARNING: OWNER_ID is not set. No one will have owner privileges.")
        print("   Set OWNER_ID in the config to your Discord user ID.")
    
    # Show friend configuration
    if FRIEND_IDS:
        print(f"🤝 Friend privileges enabled for {len(FRIEND_IDS)} user(s)")
    else:
        print("🤝 No friend IDs configured. Add user IDs to FRIEND_IDS list.")
    
    print("🚀 Starting GlitchForge bot...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🔧 FFmpeg available: Yes")
    print(f"🔧 ffprobe available: Yes")
    print(f"🎨 Presets loaded: {len(PRESETS)}")
    
    bot.run(TOKEN)
