#!/bin/zsh
# doctor.sh   Check what the Blackboard skill needs on this machine and start the bridge.
DIR=${0:A:h}; SKILL=${DIR:h}
ok(){ printf "  \033[32mok\033[0m   %s\n" "$1"; } ; no(){ printf "  \033[31mmissing\033[0m %s  (%s)\n" "$1" "$2"; }
echo "Blackboard doctor"
for t in python3 node; do command -v $t >/dev/null && ok "$t" || no "$t" "required"; done
if command -v claude >/dev/null; then ok "claude (headless explain/grade)"; elif command -v codex >/dev/null; then ok "codex (headless explain/grade)"; else no "claude or codex" "Explain and quiz grading will not run"; fi
[ -f "$SKILL/node_modules/roughjs/bundled/rough.js" ] && ok "roughjs (chalk figures)" || no "roughjs" "run: cd $SKILL && npm install"
for t in pandoc tectonic yt-dlp pdftotext manim; do command -v $t >/dev/null && ok "$t (optional)" || echo "  --   $t not found (optional)"; done
python3 -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null && ok "spaCy (noun-stack check)" || echo "  --   spaCy not found (optional: pip3 install spacy && python3 -m spacy download en_core_web_sm)"
[ "$(uname)" = Darwin ] && ok "macOS: voice answers available" || echo "  --   voice answers need macOS"
PORT=${BLACKBOARD_PORT:-7331}
if curl -s -m 1 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1; then ok "bridge running on $PORT"; else
  nohup python3 "$SKILL/board/bridge.py" >/dev/null 2>&1 &
  sleep 1; curl -s -m 1 "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && ok "bridge started on $PORT" || no "bridge" "python3 $SKILL/board/bridge.py"
fi
echo "Open http://127.0.0.1:$PORT/lessons"
