import logging
import sys
import os

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Importar los modelos
from src.models.database_models import Video, Frame, Subtitle, AudioDescription

def mostrar_contenido_tablas():
    print("\n=== VIDEOS ===")
    videos = Video.get_all()
    if not videos:
        print("No hay videos en la base de datos.")
    else:
        for video in videos:
            print(f"ID: {video['id']}, Nombre: {video['filename']}, Procesado: {video['processed']}")
    
        print("\n=== FRAMES ===")
        # Para cada video, muestra sus frames
        for video in videos:
            frames = Frame.get_by_video_id(video['id'])
            print(f"Frames del video {video['id']} ({len(frames)} frames):")
            if not frames:
                print("  No hay frames para este video.")
            else:
                for frame in frames[:5]:  # Mostrar solo los primeros 5 para no saturar
                    print(f"  Frame #{frame['frame_number']}, Timestamp: {frame['timestamp']}")
        
        print("\n=== SUBTÍTULOS ===")
        # Para cada video, muestra sus subtítulos
        for video in videos:
            subtitles = Subtitle.get_by_video_id(video['id'])
            print(f"Subtítulos del video {video['id']} ({len(subtitles)} subtítulos):")
            if not subtitles:
                print("  No hay subtítulos para este video.")
            else:
                for subtitle in subtitles[:5]:  # Mostrar solo los primeros 5
                    print(f"  {subtitle['start_time']} -> {subtitle['end_time']}: {subtitle['text'][:50]}")
        
        print("\n=== AUDIODESCRIPCIONES ===")
        # Para cada video, muestra sus audiodescripciones
        for video in videos:
            descs = AudioDescription.get_by_video_id(video['id'])
            print(f"Audiodescripciones del video {video['id']} ({len(descs)} descripciones):")
            if not descs:
                print("  No hay audiodescripciones para este video.")
            else:
                for desc in descs[:5]:  # Mostrar solo las primeras 5
                    print(f"  {desc['start_time']} -> {desc['end_time']}: {desc['description'][:50]}")

if __name__ == "__main__":
    mostrar_contenido_tablas()