declare module 'ytdl-core' {
    interface VideoDetails {
        title: string;
        lengthSeconds: string;
        author: {
            name: string;
            id: string;
        };
        videoId: string;
    }

    interface VideoInfo {
        videoDetails: {
            videoId: string;
            title: string;
            lengthSeconds: string;
            author: {
                name: string;
            };
        };
        formats: VideoFormat[];
    }

    interface BasicInfo {
        videoDetails: VideoDetails;
    }

    interface VideoFormat {
        itag: number;
        url: string;
        mimeType?: string;
        quality: string;
        container: string;
        hasVideo: boolean;
        hasAudio: boolean;
    }

    interface DownloadOptions {
        quality?: string | number;
        filter?: string | ((format: VideoFormat) => boolean);
        format?: VideoFormat;
        range?: { start?: number; end?: number };
        requestOptions?: any;
    }

    interface Options {
        quality?: string;
        filter?: 'audioandvideo' | 'videoonly' | 'audioonly' | ((format: any) => boolean);
    }

    function getBasicInfo(url: string): Promise<VideoInfo>;
    function getInfo(url: string, options?: any): Promise<VideoInfo>;
    function getURLVideoID(url: string): string;
    function getVideoID(url: string): string;
    function validateURL(url: string): boolean;
    function downloadFromInfo(info: VideoInfo, options?: DownloadOptions): NodeJS.ReadableStream;

    export default function ytdl(
        url: string,
        options?: {
            quality?: string;
            filter?: string | ((format: VideoFormat) => boolean);
        }
    ): NodeJS.ReadableStream;
}