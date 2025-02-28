#!/usr/bin/env python3
"""
MIRESSE-CLI: Herramienta de línea de comandos para interactuar con MIRESSE

Esta herramienta permite procesar videos, generar y obtener subtítulos y 
audiodescripciones a través de la API de MIRESSE.
"""

import argparse
import requests
import os
import sys
import json
import time
from pathlib import Path


class MiresseCLI:
    """Clase principal para la interfaz de línea de comandos de MIRESSE."""
    
    BASE_URL = "http://localhost:8000/api/v1"
    
    def __init__(self):
        """Inicializa la aplicación CLI."""
        self.parser = self._setup_argument_parser()
        
    def _setup_argument_parser(self):
        """Configura el parser de argumentos y los subcomandos."""
        parser = argparse.ArgumentParser(
            description='MIRESSE CLI - Herramienta para gestionar audiodescripciones y subtítulos',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # Configurar subparsers para los diferentes comandos
        subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
        
        # Comando: procesar video
        self._setup_process_parser(subparsers)
        
        # Comando: obtener estado
        self._setup_status_parser(subparsers)
        
        # Comando: obtener resultados
        self._setup_result_parser(subparsers)
        
        # Comando: eliminar video
        self._setup_delete_parser(subparsers)
        
        # Comando: obtener subtítulos
        self._setup_subtitles_parser(subparsers)
        
        # Comando: generar subtítulos
        self._setup_gen_subtitles_parser(subparsers)
        
        # Comando: obtener audiodescripción
        self._setup_audiodesc_parser(subparsers)
        
        # Comando: generar audiodescripción
        self._setup_gen_audiodesc_parser(subparsers)
        
        # Comando: renderizar video con audiodescripciones
        self._setup_render_parser(subparsers)
        
        # Comando: obtener video integrado
        self._setup_integrated_parser(subparsers)
        
        # Comando: limpiar archivos temporales
        self._setup_cleanup_parser(subparsers)
        
        return parser
    
    def _setup_process_parser(self, subparsers):
        """Configura el parser para el comando 'process'."""
        process_parser = subparsers.add_parser('process', help='Subir y procesar un nuevo video')
        process_parser.add_argument('path', help='Ruta al archivo de video')
        process_parser.add_argument('--subtitles', '-s', action='store_true', help='Generar subtítulos')
        process_parser.add_argument('--audiodesc', '-a', action='store_true', help='Generar audiodescripción')
        process_parser.add_argument('--lang', '-l', help='Idioma objetivo (ej. es, en)')
        process_parser.add_argument('--format', '-f', help='Formato de subtítulos (ej. srt, vtt)')
        process_parser.add_argument('--no-wait', '-n', action='store_true', 
                                   help='No esperar a que termine el procesamiento (continuar inmediatamente)')
        process_parser.add_argument('--timeout', '-t', type=int, default=600, 
                                   help='Tiempo máximo de espera en segundos (por defecto: 600)')
        process_parser.add_argument('--integrate', '-i', action='store_true', 
                                   help='Integrar audiodescripciones en el video final')
    
    def _setup_status_parser(self, subparsers):
        """Configura el parser para el comando 'status'."""
        status_parser = subparsers.add_parser('status', help='Obtener estado de procesamiento de un video')
        status_parser.add_argument('id', help='ID del video')
    
    def _setup_result_parser(self, subparsers):
        """Configura el parser para el comando 'result'."""
        result_parser = subparsers.add_parser('result', help='Obtener resultados de procesamiento de un video')
        result_parser.add_argument('id', help='ID del video')
    
    def _setup_delete_parser(self, subparsers):
        """Configura el parser para el comando 'delete'."""
        delete_parser = subparsers.add_parser('delete', help='Eliminar un video y sus archivos asociados')
        delete_parser.add_argument('id', help='ID del video')
    
    def _setup_subtitles_parser(self, subparsers):
        """Configura el parser para el comando 'subtitles'."""
        subtitles_parser = subparsers.add_parser('subtitles', help='Obtener subtítulos de un video')
        subtitles_parser.add_argument('id', help='ID del video')
        subtitles_parser.add_argument('--format', '-f', help='Formato de salida (ej. srt, vtt)')
        subtitles_parser.add_argument('--download', '-d', action='store_true', help='Descargar como archivo')
        subtitles_parser.add_argument('--output', '-o', help='Ruta de salida para guardar')
    
    def _setup_gen_subtitles_parser(self, subparsers):
        """Configura el parser para el comando 'generate-subtitles'."""
        gen_sub_parser = subparsers.add_parser('generate-subtitles', help='Generar subtítulos para un video existente')
        gen_sub_parser.add_argument('id', help='ID del video')
        gen_sub_parser.add_argument('--lang', '-l', help='Idioma objetivo (ej. es, en)')
        gen_sub_parser.add_argument('--format', '-f', help='Formato de salida (ej. srt, vtt)')
        gen_sub_parser.add_argument('--force', action='store_true', help='Forzar intento de generación')
        gen_sub_parser.add_argument('--no-wait', '-n', action='store_true', 
                                   help='No esperar a que termine el procesamiento (continuar inmediatamente)')
        gen_sub_parser.add_argument('--timeout', '-t', type=int, default=600, 
                                   help='Tiempo máximo de espera en segundos (por defecto: 600)')
    
    def _setup_audiodesc_parser(self, subparsers):
        """Configura el parser para el comando 'audiodesc'."""
        audiodesc_parser = subparsers.add_parser('audiodesc', help='Obtener audiodescripción de un video')
        audiodesc_parser.add_argument('id', help='ID del video')
        audiodesc_parser.add_argument('--format', '-f', help='Formato de salida (ej. json, txt)')
        audiodesc_parser.add_argument('--download', '-d', action='store_true', help='Descargar como archivo')
        audiodesc_parser.add_argument('--output', '-o', help='Ruta de salida para guardar')
    
    def _setup_gen_audiodesc_parser(self, subparsers):
        """Configura el parser para el comando 'generate-audiodesc'."""
        gen_ad_parser = subparsers.add_parser('generate-audiodesc', help='Generar audiodescripción para un video')
        gen_ad_parser.add_argument('id', help='ID del video')
        gen_ad_parser.add_argument('--voice', '-v', help='Tipo de voz (ej. es-ES-F)')
        gen_ad_parser.add_argument('--no-wait', '-n', action='store_true', 
                                   help='No esperar a que termine el procesamiento (continuar inmediatamente)')
        gen_ad_parser.add_argument('--timeout', '-t', type=int, default=600, 
                                  help='Tiempo máximo de espera en segundos (por defecto: 600)')
    
    def _setup_render_parser(self, subparsers):
        """Configura el parser para el comando 'render'."""
        render_parser = subparsers.add_parser('render', help='Renderizar video con audiodescripciones integradas')
        render_parser.add_argument('id', help='ID del video')
        render_parser.add_argument('--no-wait', '-n', action='store_true', 
                                  help='No esperar a que termine el renderizado (continuar inmediatamente)')
        render_parser.add_argument('--timeout', '-t', type=int, default=600, 
                                 help='Tiempo máximo de espera en segundos (por defecto: 600)')
    
    def _setup_integrated_parser(self, subparsers):
        """Configura el parser para el comando 'integrated'."""
        integrated_parser = subparsers.add_parser('integrated', help='Obtener video con audiodescripciones integradas')
        integrated_parser.add_argument('id', help='ID del video')
        integrated_parser.add_argument('--download', '-d', action='store_true', help='Descargar como archivo')
        integrated_parser.add_argument('--output', '-o', help='Ruta de salida para guardar')

    def _setup_cleanup_parser(self, subparsers):
        """Configura el parser para el comando 'cleanup'."""
        cleanup_parser = subparsers.add_parser('cleanup', help='Eliminar archivos temporales y carpetas vacías')
        cleanup_parser.add_argument('id', nargs='?', help='ID del video (opcional, si no se especifica limpia todos)')
        cleanup_parser.add_argument('--force', '-f', action='store_true', help='Forzar eliminación sin confirmación')
    
    def check_server(self):
        """Verifica si el servidor está en ejecución."""
        try:
            # Verificar si el servidor responde, intentando acceder a la página principal
            response = requests.get("http://localhost:8000", timeout=2)
            return True
        except:
            return False
    def process_video(self, args):
        """Sube y procesa un nuevo video."""
        video_path = os.path.expanduser(args.path)
        
        if not os.path.exists(video_path):
            print(f"❌ Error: El archivo no existe: {video_path}")
            return
        
        filename = os.path.basename(video_path)
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # Tamaño en MB
        
        print(f"Procesando: {filename} ({file_size:.2f} MB)...")
        
        # Configurar los parámetros de procesamiento
        params = {
            'generate_subtitles': args.subtitles,
            'generate_audiodesc': args.audiodesc,
        }
        
        if args.lang:
            params['target_language'] = args.lang
            
        if args.format:
            params['subtitle_format'] = args.format
            
        if args.integrate:
            params['integrate_audiodesc'] = True
        
        try:
            with open(video_path, 'rb') as video_file:
                files = {'video': (filename, video_file)}
                
                print("Subiendo y procesando video, por favor espere...")
                response = requests.post(f"{self.BASE_URL}/videos/process", files=files, data=params)
            
            if response.status_code in (200, 201, 202):
                result = response.json()
                video_id = result.get('video_id', 'desconocido')
                print(f"✅ Solicitud de procesamiento aceptada")
                print(f"ID del video: {video_id}")
                
                if 'status' in result:
                    print(f"Estado inicial: {result['status']}")
                
                # Por defecto, esperar a que termine el procesamiento
                # a menos que se especifique --no-wait
                if not args.no_wait:
                    print("\n🔄 Esperando a que finalice el procesamiento...")
                    print("   (Esto puede tomar varios minutos. Presiona Ctrl+C para cancelar la espera)")
                    
                    if self.wait_for_completion(video_id, 'video', max_wait=args.timeout):
                        print("\nVerificando resultados finales...")
                        self.get_video_result(argparse.Namespace(id=video_id))
                        
                        # Si se solicitó integrar audiodescripciones, verificar
                        if args.integrate:
                            self.get_integrated_video(argparse.Namespace(id=video_id, download=False))
                    else:
                        print("\n⚠️ El procesamiento aún continúa en el servidor.")
                        print(f"   Puedes verificar el estado más tarde con: python miresse-cli.py status {video_id}")
                else:
                    print("\n⚠️ No se esperará a que termine el procesamiento.")
                    print(f"   El procesamiento continúa en segundo plano.")
                    print(f"   Puedes verificar el estado con: python miresse-cli.py status {video_id}")
                    
                    if args.integrate:
                        print(f"   Cuando termine, puedes obtener el video integrado con: python miresse-cli.py integrated {video_id}")
                
                return result
            else:
                print(f"❌ Error al procesar video: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error al procesar video: {e}")
            return None
    
    def get_video_status(self, args):
        """Obtiene el estado de procesamiento de un video."""
        video_id = args.id
        
        try:
            response = requests.get(f"{self.BASE_URL}/videos/{video_id}/status")
            
            if response.status_code == 200:
                status = response.json()
                print(f"\nEstado del video {video_id}:")
                print("-" * 50)
                
                for key, value in status.items():
                    print(f"{key}: {value}")
                    
                return status
            else:
                print(f"❌ Error al obtener estado del video: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error al obtener estado del video: {e}")
            return None
    
    def get_video_result(self, args):
        """Obtiene los resultados del procesamiento de un video."""
        video_id = args.id
        
        try:
            response = requests.get(f"{self.BASE_URL}/videos/{video_id}/result")
            
            if response.status_code == 200:
                result = response.json()
                print(f"\nResultados del video {video_id}:")
                print("-" * 50)
                
                if result.get('status') == 'processing':
                    print(f"Estado: {result.get('status')} - {result.get('message', '')}")
                    return result
                
                if 'outputs' in result:
                    outputs = result['outputs']
                    print(f"Outputs disponibles:")
                    
                    if 'subtitles' in outputs:
                        print(f"- Subtítulos: {outputs['subtitles']}")
                        
                    if 'audio_description' in outputs:
                        print(f"- Audiodescripción: {outputs['audio_description']}")
                        
                    if 'integrated_video' in outputs:
                        print(f"- Video integrado: {outputs['integrated_video']}")
                else:
                    for key, value in result.items():
                        if isinstance(value, dict) or isinstance(value, list):
                            print(f"{key}:")
                            print(json.dumps(value, indent=2))
                        else:
                            print(f"{key}: {value}")
                    
                return result
            else:
                print(f"❌ Error al obtener resultados del video: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error al obtener resultados del video: {e}")
            return None
    
    def delete_video(self, args):
        """Elimina un video y todos sus archivos asociados."""
        video_id = args.id
        
        try:
            response = requests.delete(f"{self.BASE_URL}/videos/{video_id}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Video {video_id} eliminado correctamente")
                return result
            else:
                print(f"❌ Error al eliminar video: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error al eliminar video: {e}")
            return None
    
    def get_subtitles(self, args):
        """Obtiene los subtítulos de un video."""
        video_id = args.id
        params = {}
        
        if args.format:
            params['format'] = args.format
        
        # Si se requiere descarga, establecer el parámetro
        if args.download:
            params['download'] = True
        
        try:
            response = requests.get(f"{self.BASE_URL}/subtitles/{video_id}", params=params)
            
            if response.status_code == 200:
                # Comprobar si es una descarga de archivo
                if args.download or 'application/' in response.headers.get('Content-Type', ''):
                    output_file = args.output if args.output else f"subtitles_{video_id}.{args.format or 'srt'}"
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ Subtítulos guardados en: {output_file}")
                    return output_file
                else:
                    # Es una respuesta JSON
                    subtitles = response.json()
                    print("\nSubtítulos:")
                    print("-" * 50)
                    
                    # Mostrar el contenido de los subtítulos
                    if 'content' in subtitles:
                        print(subtitles['content'])
                    else:
                        print(json.dumps(subtitles, indent=2))
                    
                    # Guardar a archivo si se solicita
                    if args.output:
                        with open(args.output, 'w', encoding='utf-8') as f:
                            if 'content' in subtitles:
                                f.write(subtitles['content'])
                            else:
                                json.dump(subtitles, f, indent=2)
                        print(f"\nSubtítulos guardados en: {args.output}")
                    
                    return subtitles
            elif response.status_code == 404:
                print("❌ No se encontraron subtítulos para este video")
                return None
            else:
                print(f"❌ Error al obtener subtítulos: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error al obtener subtítulos: {e}")
            return None
    
    def generate_subtitles(self, args):
        """Genera subtítulos para un video existente."""
        video_id = args.id
        
        print(f"Solicitando generación de subtítulos para video {video_id}...")
        
        # En la API actual no hay un endpoint específico para solo generar subtítulos
        print("⚠️ Nota: La API actual no soporta generación independiente de subtítulos.")
        print("   Para generar subtítulos, use el comando 'process' al subir un video.")
        print("   Puede volver a procesar el video con la opción --subtitles")
        
        if not args.force:
            return None
        
        # Si se fuerza, intentar usar un enfoque alternativo (no implementado)
        print("\nIntentando generar subtítulos con un enfoque alternativo...")
        return None
    
    def get_audiodesc(self, args):
        """Obtiene la audiodescripción de un video."""
        video_id = args.id
        params = {}
        
        if args.format:
            params['format'] = args.format
        
        # Si se requiere descarga, establecer el parámetro
        if args.download:
            params['download'] = True
        
        try:
            response = requests.get(f"{self.BASE_URL}/audiodesc/{video_id}", params=params)
            
            if response.status_code == 200:
                # Comprobar si es una descarga de archivo
                if args.download or 'audio/' in response.headers.get('Content-Type', ''):
                    output_file = args.output if args.output else f"audiodesc_{video_id}.{args.format or 'mp3'}"
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ Audiodescripción guardada en: {output_file}")
                    return output_file
                else:
                    # Es una respuesta JSON
                    audiodesc = response.json()
                    print("\nAudiodescripción:")
                    print("-" * 50)
                    
                    # Mostrar el contenido de la audiodescripción
                    if 'content' in audiodesc:
                        print(audiodesc['content'])
                    else:
                        print(json.dumps(audiodesc, indent=2))
                    
                    # Guardar a archivo si se solicita
                    if args.output:
                        with open(args.output, 'w', encoding='utf-8') as f:
                            if 'content' in audiodesc:
                                f.write(audiodesc['content'])
                            else:
                                json.dump(audiodesc, f, indent=2)
                        print(f"\nAudiodescripción guardada en: {args.output}")
                    
                    return audiodesc
            elif response.status_code == 404:
                print("❌ No se encontró audiodescripción para este video")
                return None
            else:
                print(f"❌ Error al obtener audiodescripción: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error al obtener audiodescripción: {e}")
            return None
    def generate_audiodesc(self, args):
        """Genera audiodescripción para un video."""
        video_id = args.id
        
        print(f"Solicitando generación de audiodescripción para video {video_id}...")
        
        params = {}
        if args.voice:
            params['voice_type'] = args.voice
        
        try:
            response = requests.post(f"{self.BASE_URL}/audiodesc/{video_id}/generate", params=params)
            
            if response.status_code in (200, 201, 202):
                result = response.json()
                print(f"✅ Solicitud de generación de audiodescripción aceptada")
                print(f"Estado: {result.get('status', 'En proceso')}")
                
                # Por defecto, esperar a menos que se especifique --no-wait
                if not args.no_wait:
                    print("\n🔄 Esperando a que finalice el proceso...")
                    print("   (Esto puede tomar varios minutos. Presiona Ctrl+C para cancelar la espera)")
                    success = self.wait_for_completion(video_id, 'audiodesc', max_wait=args.timeout)
                    
                    if not success:
                        print("\n⚠️ El procesamiento aún continúa en el servidor.")
                        print(f"   Puedes verificar el estado más tarde con: python miresse-cli.py status {video_id}")
                else:
                    print("\n⚠️ No se esperará a que termine el procesamiento.")
                    print(f"   El procesamiento continúa en segundo plano.")
                    print(f"   Puedes verificar el estado con: python miresse-cli.py status {video_id}")
                
                return result
            else:
                print(f"❌ Error al solicitar generación de audiodescripción: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error al solicitar generación de audiodescripción: {e}")
            return None
    
    def render_video(self, args):
        """Renderiza un video con audiodescripciones integradas."""
        video_id = args.id
        
        print(f"Solicitando renderizado del video {video_id} con audiodescripciones...")
        
        try:
            response = requests.post(f"{self.BASE_URL}/videos/{video_id}/render")
            
            if response.status_code in (200, 201, 202):
                result = response.json()
                print(f"✅ Solicitud de renderizado aceptada")
                print(f"Estado: {result.get('status', 'En proceso')}")
                
                # Por defecto, esperar a menos que se especifique --no-wait
                if not args.no_wait:
                    print("\n🔄 Esperando a que finalice el renderizado...")
                    print("   (Esto puede tomar varios minutos. Presiona Ctrl+C para cancelar la espera)")
                    success = self.wait_for_completion(video_id, 'video', max_wait=args.timeout)
                    
                    if success:
                        # Obtener información del video renderizado
                        self.get_integrated_video(argparse.Namespace(id=video_id, download=False))
                    else:
                        print("\n⚠️ El renderizado aún continúa en el servidor.")
                        print(f"   Puedes verificar el estado más tarde con: python miresse-cli.py status {video_id}")
                else:
                    print("\n⚠️ No se esperará a que termine el renderizado.")
                    print(f"   El proceso continúa en segundo plano.")
                    print(f"   Puedes verificar el estado con: python miresse-cli.py status {video_id}")
                    print(f"   Cuando termine, puedes obtener el video con: python miresse-cli.py integrated {video_id}")
                
                return result
            else:
                print(f"❌ Error al solicitar renderizado: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error al solicitar renderizado: {e}")
            return None
    
    def get_integrated_video(self, args):
    #Obtiene el video con audiodescripciones integradas."""
        video_id = args.id
        params = {}
    
     # Si se requiere descarga, establecer el parámetro
        if hasattr(args, 'download') and args.download:
            params['download'] = True
    
    # Verificar si existe el atributo output
        output_path = getattr(args, 'output', None)
    
        try:
            response = requests.get(f"{self.BASE_URL}/videos/{video_id}/integrated", params=params)
        
            if response.status_code == 200:
            # Comprobar si es una descarga de archivo
                if (hasattr(args, 'download') and args.download) or 'video/' in response.headers.get('Content-Type', ''):
                    output_file = output_path if output_path else f"video_integrated_{video_id}.mp4"
                    with open(output_file, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ Video con audiodescripciones guardado en: {output_file}")
                    return output_file
                else:
                # Es una respuesta JSON
                    video_info = response.json()
                
                    if video_info.get('status') == 'processing':
                        print(f"⚠️ El video con audiodescripciones aún se está procesando.")
                        print(f"   Mensaje: {video_info.get('message', '')}")
                        return video_info
                
                    print("\nVideo con audiodescripciones integradas:")
                    print("-" * 50)
                
                    for key, value in video_info.items():
                        print(f"{key}: {value}")
                
                    print(f"\nPara descargar el video: python miresse-cli.py integrated {video_id} --download")
                
                # Guardar a archivo si se solicita
                    if output_path:
                        download_response = requests.get(f"{self.BASE_URL}/videos/{video_id}/integrated?download=true")
                        with open(output_path, 'wb') as f:
                            f.write(download_response.content)
                        print(f"\nVideo guardado en: {output_path}")
                
                    return video_info
            elif response.status_code == 404:
                print("❌ No se encontró el video con audiodescripciones para este ID")
                print("   Quizás necesites generarlo primero con: python miresse-cli.py render ID")
                return None
            else:
                print(f"❌ Error al obtener el video integrado: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error al obtener el video integrado: {e}")
            return None
    
    def cleanup_temp_files(self, args):
        """Limpia archivos temporales y carpetas vacías."""
        video_id = args.id
        
        if video_id:
            # Limpiar archivos para un video específico
            confirm = "s" if args.force else input(f"¿Desea eliminar archivos temporales para el video {video_id}? (s/n): ").lower()
            
            if confirm != "s":
                print("Operación cancelada.")
                return
                
            try:
                # Endpoint para limpiar archivos temporales (puede requerir implementación en tu API)
                response = requests.post(f"{self.BASE_URL}/videos/{video_id}/cleanup")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Archivos temporales para el video {video_id} eliminados correctamente")
                    
                    if 'deleted_files' in result:
                        print("Archivos eliminados:")
                        for file in result['deleted_files']:
                            print(f"  - {file}")
                    
                    return result
                else:
                    print(f"❌ Error al limpiar archivos temporales: {response.status_code}")
                    print(response.text)
                    return None
            except Exception as e:
                print(f"❌ Error al limpiar archivos temporales: {e}")
                print("\n⚠️ La funcionalidad de limpieza puede no estar implementada en tu API.")
                print("   Considera implementar un endpoint /videos/{video_id}/cleanup en tu backend.")
                return None
        else:
            # Limpiar archivos para todos los videos
            confirm = "s" if args.force else input("¿Desea eliminar todos los archivos temporales? (s/n): ").lower()
            
            if confirm != "s":
                print("Operación cancelada.")
                return
                
            try:
                # Endpoint para limpiar todos los archivos temporales
                response = requests.post(f"{self.BASE_URL}/cleanup")
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Archivos temporales eliminados correctamente")
                    
                    if 'deleted_files' in result:
                        print("Archivos eliminados:")
                        for file in result['deleted_files']:
                            print(f"  - {file}")
                    
                    if 'deleted_dirs' in result:
                        print("Carpetas eliminadas:")
                        for directory in result['deleted_dirs']:
                            print(f"  - {directory}")
                    
                    return result
                else:
                    print(f"❌ Error al limpiar archivos temporales: {response.status_code}")
                    print(response.text)
                    return None
            except Exception as e:
                print(f"❌ Error al limpiar archivos temporales: {e}")
                print("\n⚠️ La funcionalidad de limpieza puede no estar implementada en tu API.")
                print("   Considera implementar un endpoint /cleanup en tu backend.")
                return None
    
    def wait_for_completion(self, video_id, task_type, max_wait=600, interval=5):
        """Espera a que un proceso termine, con un tiempo máximo de espera."""
        start_time = time.time()
        
        # Determinar la URL para verificar el estado según el tipo de tarea
        if task_type == 'audiodesc':
            status_url = f"{self.BASE_URL}/audiodesc/{video_id}/status"
        else:
            status_url = f"{self.BASE_URL}/videos/{video_id}/status"
        
        progress_bar_width = 40
        
        while time.time() - start_time < max_wait:
            try:
                response = requests.get(status_url)
                
                if response.status_code == 200:
                    result = response.json()
                    status = result.get('status', '').lower()
                    progress = result.get('progress', 0)
                    
                    if status in ('completed', 'finalizado', 'done', 'complete'):
                        print(f"\n✅ Proceso completado con éxito")
                        return True
                    elif status in ('error', 'failed', 'fallido', 'failure'):
                        print(f"\n❌ El proceso finalizó con errores: {result.get('error', 'Desconocido')}")
                        return False
                    
                    # Mostrar una barra de progreso si hay información de progreso
                    elapsed = time.time() - start_time
                    
                    if isinstance(progress, (int, float)) and 0 <= progress <= 100:
                        filled_length = int(progress_bar_width * progress / 100)
                        bar = '█' * filled_length + '░' * (progress_bar_width - filled_length)
                        print(f"Procesando: [{bar}] {progress:.1f}% ({elapsed:.0f}s)", end='\r')
                    else:
                        # Barra de progreso indeterminada
                        pos = int((elapsed / interval) % progress_bar_width)
                        bar = '░' * pos + '█' + '░' * (progress_bar_width - pos - 1)
                        print(f"Procesando: [{bar}] ({elapsed:.0f}s)", end='\r')
                else:
                    print(f"❌ Error al verificar estado: {response.status_code}", end='\r')
                    
            except Exception as e:
                print(f"❌ Error al verificar estado: {e}", end='\r')
            
            time.sleep(interval)
        
        print(f"\n⚠️ Tiempo de espera agotado después de {max_wait} segundos")
        return False
    
    def run(self):
        """Ejecuta la aplicación CLI."""
        args = self.parser.parse_args()
        
        # Verificar que el servidor esté en ejecución
        if not self.check_server():
            print("❌ Error: No se puede conectar al servidor MIRESSE.")
            print("   Asegúrate de que el servidor esté en ejecución con 'python main.py'")
            sys.exit(1)
        
        # Mapeo de comandos a métodos de clase
        command_handlers = {
            'process': self.process_video,
            'status': self.get_video_status,
            'result': self.get_video_result,
            'delete': self.delete_video,
            'subtitles': self.get_subtitles,
            'generate-subtitles': self.generate_subtitles,
            'audiodesc': self.get_audiodesc,
            'generate-audiodesc': self.generate_audiodesc,
            'render': self.render_video,
            'integrated': self.get_integrated_video,
            'cleanup': self.cleanup_temp_files
        }
        
        # Ejecutar el comando si existe, o mostrar ayuda
        if args.command in command_handlers:
            command_handlers[args.command](args)
        else:
            self.parser.print_help()


def main():
    """Punto de entrada principal del programa."""
    cli = MiresseCLI()
    cli.run()


if __name__ == "__main__":
    main()