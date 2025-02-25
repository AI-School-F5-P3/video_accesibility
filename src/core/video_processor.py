import os
import shutil
import subprocess
import shlex
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener rutas desde las variables de entorno o establecer valores predeterminados
video_dir = os.getenv("video_dir_path", "c:\\Windows\\ffmpeg\\Video")  # Singular
audio_dir = os.getenv("audio_dir_path", "c:\\Windows\\ffmpeg\\Audio")
subs_dir = os.getenv("subs_dir_path", "c:\\Windows\\ffmpeg\\Subtitles")
output_dir = os.getenv("output_dir_path", "c:\\Windows\\ffmpeg\\Output")

# Crear carpetas si no existen
for folder in [video_dir, audio_dir, subs_dir, output_dir]:
    os.makedirs(folder, exist_ok=True)

def move_files_and_process_ffmpeg():
    """Mueve archivos desde Temp a rutas fijas y ejecuta FFmpeg."""
    
    temp_files = {
        "video": str(Path("C:/Users/Administrator/AppData/Local/Temp/video.mp4").resolve()),
        "audio": str(Path("C:/Users/Administrator/AppData/Local/Temp/audio.aac").resolve()),
        "subs": str(Path("C:/Users/Administrator/AppData/Local/Temp/subtitles.srt").resolve())
    }

    fixed_paths = {
        "video": os.path.join(video_dir),
        "audio": os.path.join(audio_dir),
        "subs": os.path.join(subs_dir),
        "output": os.path.join(output_dir)
    }

    # Normalizar rutas para evitar problemas con espacios
    for key in fixed_paths:
        fixed_paths[key] = str(Path(fixed_paths[key]).resolve())

    # Mover archivos si existen
    for key, temp_path in temp_files.items():
        if os.path.exists(temp_path):
            try:
                # Asegurarse de que el directorio de destino existe
                os.makedirs(os.path.dirname(fixed_paths[key]), exist_ok=True)
                
                # Si el archivo de destino ya existe, eliminarlo
                if os.path.exists(fixed_paths[key]):
                    os.remove(fixed_paths[key])
                    
                shutil.copy2(temp_path, fixed_paths[key])
                print(f"✅ {key.capitalize()} copiado a {fixed_paths[key]}")
            except Exception as e:
                print(f"❌ Error copiando {key}: {e}")
                return

    # Verificar si existen los archivos necesarios para procesar
    if not os.path.exists(fixed_paths["video"]):
        print(f"❌ Error: No se encontró el archivo de video {fixed_paths['video']}")
        return
        
    if not os.path.exists(fixed_paths["audio"]):
        print(f"❌ Error: No se encontró el archivo de audio {fixed_paths['audio']}")
        return
        
    if not os.path.exists(fixed_paths["subs"]):
        print(f"❌ Error: No se encontró el archivo de subtítulos {fixed_paths['subs']}")
        return

    # Preparar comando ffmpeg con rutas correctas
    # En Windows, escapar las rutas correctamente
    if os.name == 'nt':  # Windows
        subs_path = fixed_paths["subs"].replace('\\', '\\\\').replace(':', '\\:')
    else:  # Linux/Mac
        subs_path = fixed_paths["subs"].replace(':', '\\:')

    # Construir comando FFmpeg
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-i", fixed_paths["video"],
        "-i", fixed_paths["audio"],
        "-vf", f"subtitles={subs_path}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,BorderStyle=3,Outline=1,Shadow=1,MarginV=20'",
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-c:a", "copy",
        fixed_paths["output"]
    ]

    # Ejecutar FFmpeg
    try:
        result = subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.PIPE, text=True)
        print(f"\n✅ Video procesado correctamente: {fixed_paths['output']}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error ejecutando FFmpeg: {e}")
        print(f"⚠️ Detalles del error: {e.stderr}")

# Ejecutar la función
if __name__ == "__main__":
    move_files_and_process_ffmpeg()