#!/bin/sh
# Install the local Kokoro-82M narrator (Apache-2.0, no API key) for lesson videos.
# Creates a venv and downloads the model weights outside the skill and any repo:
#   $BLACKBOARD_TTS_HOME (default ~/.cache/blackboard)/tts-venv     python + kokoro-onnx
#   $BLACKBOARD_TTS_HOME/kokoro/kokoro-v1.0.onnx, voices-v1.0.bin   weights (~340 MB)
# Safe to rerun: existing pieces are kept. video/tts.py finds them on its own.
set -eu
HOME_DIR=${BLACKBOARD_TTS_HOME:-$HOME/.cache/blackboard}
VENV=$HOME_DIR/tts-venv
W=$HOME_DIR/kokoro
REL=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
mkdir -p "$W"

if [ ! -x "$VENV/bin/python" ]; then
  PY=""
  for c in python3.13 python3.12 python3.11 python3.10; do
    if command -v "$c" >/dev/null 2>&1; then PY=$(command -v "$c"); break; fi
  done
  if [ -n "$PY" ]; then
    "$PY" -m venv "$VENV"
  elif command -v uv >/dev/null 2>&1; then
    uv venv --python 3.12 "$VENV"
  else
    echo "setup_tts: need python3.10-3.13 or uv (onnxruntime has no wheels for newer Pythons yet)" >&2; exit 1
  fi
fi
if ! "$VENV/bin/python" -c "import kokoro_onnx, soundfile, numpy" 2>/dev/null; then
  if [ -x "$VENV/bin/pip" ]; then
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet kokoro-onnx soundfile numpy
  else
    uv pip install --python "$VENV/bin/python" kokoro-onnx soundfile numpy
  fi
fi

for f in kokoro-v1.0.onnx voices-v1.0.bin; do
  if [ ! -s "$W/$f" ]; then
    echo "downloading $f"
    curl -fsSL --retry 3 -o "$W/.$f.part" "$REL/$f"
    mv "$W/.$f.part" "$W/$f"
  fi
done
"$VENV/bin/python" -c "import kokoro_onnx; print('kokoro-onnx', getattr(kokoro_onnx, '__version__', 'ok'))"
echo "Kokoro ready: $VENV, $W"
