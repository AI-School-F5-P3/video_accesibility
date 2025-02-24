from typing import Dict, Any
import googleapiclient.discovery
import googleapiclient.errors

class YouTubeAPI:
    def __init__(self, api_key: str):
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=api_key
        )

    async def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """Obtiene información del video de YouTube"""
        try:
            request = self.youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=video_id
            )
            response = request.execute()
            
            if not response["items"]:
                raise ValueError(f"Video {video_id} no encontrado")
                
            return response["items"][0]
        except Exception as e:
            raise ValueError(f"Error obteniendo información del video: {str(e)}")