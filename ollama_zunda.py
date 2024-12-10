import os
import streamlit as st
from pydub import AudioSegment
import youtube_dl
import time
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from edamame import text2zunda
from ollama_handoler import ollama_chat

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.environ["AZURE_OPENAI_VERSION"],
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)
model = os.environ["AZURE_OPENAI_DEPLOYMENT_MINI"]
speech_key = os.environ["SPEECH_KEY"]
service_region = os.environ["SPEECH_REGION"]

st.title("音声文字起こしアプリ")
st.write("このアプリはMicrosoft AzureのサービスであるSpeech Serviceを使用しています")

language = st.selectbox("言語", ["日本語", "英語"])
audio_source = st.radio("音声源", ("ファイルから", "YouTubeから", "マイクから"))


def recognize_from_mic(speech_key, service_region):
    st.session_state["stop_recording"] = False
    output = ""
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=service_region, speech_recognition_language="ja-JP"
    )
    audio_input = speechsdk.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_input
    )

    def recognized(evt):
        nonlocal output
        output += evt.result.text

    def session_stopped(evt):
        st.write("セッションが停止しました: {}".format(evt))

    def canceled(evt):
        st.error("キャンセルされました: {} (理由: {})".format(evt, evt.reason))
        if evt.reason == speechsdk.CancellationReason.Error:
            st.error("エラーコード: {}, エラー詳細: {}".format(evt.error_code, evt.error_details))

    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.session_stopped.connect(session_stopped)
    speech_recognizer.canceled.connect(canceled)

    st.write("マイク入力を開始しています...")

    with st.spinner('録音中... "録音を終了" ボタンを押して停止します'):
        speech_recognizer.start_continuous_recognition()
        input("マイクからの音声認識を終了するにはEnterキーを押してください\n")
        speech_recognizer.stop_continuous_recognition()
        st.write("マイク入力が終了しました。")

    # 認識プロセスが完全に停止した後でUIを更新
    speech_recognizer.stop_continuous_recognition_async().get()

    return output


def recognize_audio(speech_key, service_region, filename, recognize_time=100):
    output = ""
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, region=service_region, speech_recognition_language="ja-JP"
    )
    audio_input = speechsdk.AudioConfig(filename=filename)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_input
    )

    def recognized(evt):
        nonlocal output
        output += evt.result.text

    speech_recognizer.recognized.connect(recognized)
    speech_recognizer.start_continuous_recognition()
    time.sleep(recognize_time)
    speech_recognizer.stop_continuous_recognition()

    return output


async def synthesize_voice_and_display(output):
    messages = [
        {"role": "system", "content": "Assistant is a large language model trained by OpenAI."},
        {"role": "user", "content": output},
    ]
    completion = (
        client.chat.completions.create(
            model=model,
            messages=messages,
        )
        .choices[0]
        .message.content
    )
    st.text_area("回答", completion)

    # 非同期で音声合成を実行
    text2zunda(completion)


if audio_source == "ファイルから":
    byte_file = st.file_uploader(
        "ファイルを選択してアップロード", type=["wav", "m4a", "mp3", "mp4"]
    )
    if byte_file is not None:
        audio = AudioSegment.from_file(byte_file)
        filename = "uploaded_audio.wav"
        audio.export(filename, format="wav")
elif audio_source == "YouTubeから":
    url = st.text_input("YouTubeのURLを入力してください")
    if url:
        output_file_path = "downloaded_audio"
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_file_path + ".%(ext)s",
            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"},
                {"key": "FFmpegMetadata"},
            ],
        }
        ydl = youtube_dl.YoutubeDL(ydl_opts)
        _ = ydl.extract_info(url, download=True)
        audio = AudioSegment.from_mp3(output_file_path + ".mp3")
        filename = "downloaded_audio.wav"
        audio.export(filename, format="wav")
elif audio_source == "マイクから":
    if st.button("録音を開始", key="start_recording"):
        output = recognize_from_mic(speech_key, service_region)
        st.text_area("認識されたテキスト", output)
        if output:
            with st.spinner(text="回答生成中"):
                asyncio.run(synthesize_voice_and_display(output))

# 外部音声ソースからの場合 "文字起こしを開始" ボタンを表示
if audio_source in ["ファイルから", "YouTubeから"] and st.button(
    "文字起こしを開始", key="start_transcription"
):
    with st.spinner(text="文字起こし中"):
        output = recognize_audio(speech_key, service_region, filename)
        st.text_area("認識されたテキスト", output)
    if output:
        with st.spinner(text="回答生成中"):
            asyncio.run(synthesize_voice_and_display(output))
