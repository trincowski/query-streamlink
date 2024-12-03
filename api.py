import streamlink
from streamlink import Streamlink
from streamlink.exceptions import NoPluginError, PluginError
from streamlink.stream import DASHStream
import urllib.request
from urllib.error import URLError
from functools import lru_cache

@lru_cache(maxsize=32)
def get_streams(query, quality="best", proxy=None, proxy_type=None, low_latency=True):
    try:
        # Create a new Streamlink session
        session = Streamlink()

        # Configure proxy if provided
        if proxy:
            if proxy_type not in ('http', 'https', 'socks4', 'socks5'):
                return "Invalid proxy type. Supported types are: http, https, socks4, socks5"
            
            session.set_option("http-proxy", f"{proxy_type}://{proxy}")
            
            # Configure urllib to use the same proxy
            proxy_handler = urllib.request.ProxyHandler({proxy_type: proxy})
            opener = urllib.request.build_opener(proxy_handler)
            urllib.request.install_opener(opener)

        # Set low latency options
        if low_latency:
            session.set_option("low-latency", True)
            session.set_option("hls-live-edge", 1)
            session.set_option("hls-segment-stream-data", True)
            session.set_option("stream-segment-threads", 2)
            session.set_option("ringbuffer-size", 1024)

        # Platform-specific optimizations
        if 'twitch.tv' in query:
            session.set_option("twitch-low-latency", True)
            session.set_option("twitch-disable-ads", True)
        elif 'youtube.com' in query or 'youtu.be' in query:
            session.set_option("youtube-live-edge", 1)

        streams = session.streams(query)
        if not streams:
            return "No streams found."

        for stream_quality, link in streams.items():
            if quality and quality != stream_quality:
                continue

            url = link.to_url()
            
            if any(domain in query for domain in ('dailymotion.com', 'dai.ly')):
                manifest_url = link.to_manifest_url()
                if 'https://www.dailymotion.com/cdn/live/video/' in manifest_url:
                    try:
                        with urllib.request.urlopen(manifest_url) as response:
                            data = response.read().decode('utf-8')
                        for key in ('live-3', 'live-2', 'live-1'):
                            if key in data:
                                return url.replace('live-0', key)
                        return url
                    except URLError as e:
                        return f"Error fetching manifest: {e}"
                return manifest_url

            if isinstance(link, DASHStream) or any(term in stream_quality for term in ("best", "live", "http")) or "chunklist" in url:
                return url

        return link.to_manifest_url()
    except (ValueError, NoPluginError, PluginError) as ex:
        return f"An error occurred: {ex}"