import requests
import json
import pyaudio
import asyncio
from concurrent.futures import ThreadPoolExecutor


def create_audio_query(text_chunk: str, speaker: int = 3):
    """Send request to create an audio query for a text chunk."""
    return requests.post(
        f"http://localhost:50021/audio_query", params={"text": text_chunk, "speaker": speaker}
    ).json()


def synthesize_audio(query_json: dict, speaker: int):
    """Synthesize audio from a query and return the voice data."""
    synthesis = requests.post(
        f"http://localhost:50021/synthesis",
        headers={"Content-Type": "application/json"},
        params={"speaker": speaker},
        data=json.dumps(query_json),
    )
    return synthesis.content


def play_audio(voice_data: bytes):
    """Play the given voice data using PyAudio."""
    pya = pyaudio.PyAudio()
    stream = pya.open(format=pyaudio.paInt16, channels=1, rate=24000, output=True)
    stream.write(voice_data)
    stream.stop_stream()
    stream.close()
    pya.terminate()


async def voicevox_synthesis_and_playback(text: str, speaker: int = 3, chunk_size: int = 50):
    """Main function to split text, synthesize audio for each chunk, and play it."""
    # Split text into manageable chunks
    text_chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        # Create audio queries for each chunk
        query_futures = [
            loop.run_in_executor(executor, create_audio_query, chunk, speaker)
            for chunk in text_chunks
        ]
        # Await results of all queries
        query_results = await asyncio.gather(*query_futures)

        # Synthesize and play audio for each chunk
        for query_result in query_results:
            voice_data = await loop.run_in_executor(
                executor, synthesize_audio, query_result, speaker
            )
            play_audio(voice_data)
            print("Partial audio played.")

