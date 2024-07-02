import streamlink
from streamlink import NoPluginError, PluginError
from streamlink.stream import DASHStream
import urllib.request

def get_streams(query, quality="best"):
    try:
        streams = streamlink.streams(query)
        if not streams:
            return "No streams found."
        
        for stream_quality, link in streams.items():
            if quality and quality != stream_quality:
                continue

            url = link.to_url()
            if 'dailymotion.com' in query or 'dai.ly' in query:
                manifest_url = link.to_manifest_url()
                if 'https://www.dailymotion.com/cdn/live/video/' in manifest_url:
                    response = urllib.request.urlopen(manifest_url)
                    data = response.read().decode('utf-8')
                    replacements = {'live-3': 'live-0', 'live-2': 'live-0', 'live-1': 'live-0'}
                    for key, replacement in replacements.items():
                        if key in data:
                            return url.replace('live-0', replacement)
                    return url
                return manifest_url
            
            if isinstance(link, DASHStream) or any(term in stream_quality for term in ["best", "live", "http"]) or "chunklist" in url:
                return url

        return link.to_manifest_url()

    except (ValueError, NoPluginError, PluginError, Exception) as ex:
        return f"An error occurred: {ex}"
