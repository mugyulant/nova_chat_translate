# ずんだもんに回答を読み上げさせる。

## 環境構築

voiceboxのダウンロード

```powershell
docker pull voicevox/voicevox_engine:nvidia-ubuntu20.04-latest
docker run --rm --gpus all -p '127.0.0.1:50021:50021'voicevox/voicevox_engine:nvidia-ubuntu20.04-latest
```

cudaが使えないならCPU版もある。(が、めっちゃ遅い)

```powershell
docker pull voicevox/voicevox_engine:cpu-ubuntu20.04-latest
docker run --rm -it -p '127.0.0.1:50021:50021' voicevox/voicevox_engine:cpu-ubuntu20.04-latest
```
