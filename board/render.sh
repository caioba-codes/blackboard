#!/bin/zsh
# render.sh <lesson.md> [--live|--stream]   Render a lesson on the Blackboard. --live: mark it as being written (board appends blocks as they land).
# render.sh --ws <dir>                 Point the board at a workspace without a lesson (grid).
# Writes board/state.json, starts bridge.py if needed, opens the board once per host, pokes the bridge.
set -e
DIR=${0:A:h}; "$DIR/../bin/update.sh" 2>/dev/null || true  # git clones only, once a day; prints one line if it updated
HOME_DIR=${BLACKBOARD_HOME:-$HOME/.cache/blackboard}; mkdir -p "$HOME_DIR"; STATE=$HOME_DIR/state.json; PORT=${BLACKBOARD_PORT:-7331}; URL="http://127.0.0.1:$PORT"
LESSON=""; STREAM=0; LIVE=0; WS=""
while [ $# -gt 0 ]; do case "$1" in
  --stream) STREAM=1;; --live) LIVE=1;; --ws) WS=$2; shift;; *) LESSON=$1;; esac; shift; done

# host detection (see HOSTS.md)
AGENT=${BLACKBOARD_AGENT:-}; LAYOUT=${BLACKBOARD_LAYOUT:-}
if [ -z "$AGENT" ]; then
  if [ -n "$CLAUDECODE" ]; then AGENT=claude
  elif [ -n "$CODEX_THREAD_ID" ] || [ -n "$CODEX_HOME" ]; then AGENT=codex
  else AGENT=claude; fi
fi
if [ -z "$LAYOUT" ]; then
  if [ -n "$CMUX_WORKSPACE_ID" ]; then
    LAYOUT=cmux
  elif [[ "${CODEX_INTERNAL_ORIGINATOR_OVERRIDE:-}" == *"Codex Desktop"* ]]; then
    LAYOUT=app
  else
    LAYOUT=tab
  fi
fi

# workspace + lesson id
if [ -n "$LESSON" ]; then
  LESSON=${LESSON:A}; [ -f "$LESSON" ] || { echo "no such lesson: $LESSON" >&2; exit 1; }
  WS=${LESSON:h:h}; ID=$(basename "$LESSON" | sed -E 's/^([0-9]{4})-.*/\1/')
else
  WS=${WS:-$PWD}; WS=${WS:A}; ID=""
fi
[ -d "$WS/lessons" ] || mkdir -p "$WS/lessons"

# Fail before publishing if an author manually copied another lesson's banner.
if [ -n "$LESSON" ]; then python3 "$DIR/../bin/banner_guard.py" --lesson "$LESSON"; fi

# photo: every lesson gets a banner that shows the lesson's own subject. If the front matter has
# no photo:, fetch one in the background from the image: subject and write photo:/credit: into
# the front matter; the board reloads the header on its own. Never a generic chalkboard: the board
# itself is already a blackboard, so a chalkboard banner says nothing about the lesson.
if [ -n "$LESSON" ] && ! grep -q '^photo:' "$LESSON" 2>/dev/null && ! grep -qE '^plain:[[:space:]]*true' "$LESSON" 2>/dev/null; then
  FM=$(sed -n '/^---$/,/^---$/p' "$LESSON")
  SUBJ=$(print -r -- "$FM" | sed -n 's/^image:[[:space:]]*//p' | head -1)
  TITLE=$(print -r -- "$FM" | sed -n 's/^title:[[:space:]]*//p' | head -1)
  # The lesson's topic from its title: drop "How to", "Ace", course codes and "Test 2"-style labels.
  TOPIC=$(print -r -- "$TITLE" | sed -E 's/^(How|Why|What) (to |the |a |an )?//; s/ (Actually )?Works?$//; s/^(Ace|Pass|Solve|Learn|Understand|Master) //; s/[A-Z]{2,5} ?[0-9]{3,4}[A-Z]?//g; s/(Test|Exam|Quiz|Midterm|Final|Lesson|Chapter|Problems?|HW|Homework) ?[0-9.]*//g; s/  +/ /g; s/^ +//; s/ +$//')
  CHALK='(chalk|blackboard|chalkboard|slate|classroom|whiteboard)'
  if [ -n "$SUBJ" ] && print -r -- "$SUBJ" | grep -qiE "$CHALK" && ! print -r -- "$TITLE" | grep -qiE "$CHALK"; then
    echo "render.sh: image: \"$SUBJ\" is a generic board photo; the banner must show the lesson's subject. Using \"${TOPIC:-$TITLE}\" instead. Set image: to something from the lesson's topic." >&2
    SUBJ=""
  fi
  if [ -z "$SUBJ" ]; then
    SUBJ=${TOPIC:-$TITLE}
    echo "render.sh: no usable image: in $LESSON; searching \"$SUBJ\". Set image: to a concrete subject from the lesson's topic and re-roll if the banner is off-topic." >&2
  fi
  LOCK="$LESSON.photo.lock"
  # a lock left by a killed fetch must not block the banner forever
  [ -d "$LOCK" ] && [ -n "$(find "$LOCK" -maxdepth 0 -mmin +10 2>/dev/null)" ] && rmdir "$LOCK" 2>/dev/null
  if mkdir "$LOCK" 2>/dev/null; then
    ( trap 'rmdir "$LOCK" 2>/dev/null' EXIT
      # Search for an unused photo of the subject, then of the title's topic. Never recycle another
      # lesson's banner, never fall back to a chalkboard: no banner is better than an unrelated one.
      PHOTO_LINES=$("$DIR/../bin/image.sh" "$SUBJ" "$ID" "$WS" 2>>"$HOME_DIR/image.log") \
        || { [ -n "$TOPIC" ] && [ "$TOPIC" != "$SUBJ" ] && PHOTO_LINES=$("$DIR/../bin/image.sh" "$TOPIC" "$ID" "$WS" 2>>"$HOME_DIR/image.log"); } \
        || { echo "No unique on-topic banner found for $LESSON; set a different image: and retry image.sh" >>"$HOME_DIR/image.log"; exit 1; }
      python3 - "$LESSON" "$PHOTO_LINES" <<'PY'
import sys,re
path,lines=sys.argv[1],sys.argv[2]
s=open(path).read()
if not s.startswith('---\n') or re.search(r'^photo:',s,re.M): sys.exit(0)
end=s.index('\n---\n',4)
s=s[:end]+'\n'+lines.strip()+s[end:]
open(path,'w').write(s)
PY
    ) >/dev/null 2>&1 &
  fi
fi

# keep previous "opened" + surface ids
PREV=$(cat "$STATE" 2>/dev/null || echo '{}')
SLUG=$(python3 - "$STATE" "$WS" "$ID" "$AGENT" "$LAYOUT" "$([ "$STREAM" = 1 ] || [ "$LIVE" = 1 ] && echo 1 || echo 0)" "${CMUX_SURFACE_ID:-}" <<'PY'
import json,sys,time,os,re,hashlib
p,ws,lid,agent,layout,stream,cli=sys.argv[1:]
try: st=json.load(open(p))
except Exception: st={}
base=os.path.basename(ws); base=os.path.basename(os.path.dirname(ws)) if base=="learn" else base
slug=re.sub(r"[^a-z0-9]+","-",base.lower()).strip("-") or "ws"
wss=st.setdefault("workspaces",{})
for k,w in list(wss.items()):
    if k==slug and os.path.abspath(w.get("path",""))!=os.path.abspath(ws): slug=slug+"-"+hashlib.md5(ws.encode()).hexdigest()[:4]
w=wss.setdefault(slug,{"path":ws})
w.update({"path":ws,"current":lid or w.get("current",""),"agent":agent,"layout":layout,"streaming":stream=="1","rev":int(time.time()*1000)})
if cli: w["cli_surface"]=cli
# top level = the last rendered workspace (older pages and tools read these)
st.update({"ws":ws,"current":lid or st.get("current",""),"agent":agent,"layout":layout,"streaming":stream=="1","rev":int(time.time()*1000)})
if cli: st["cli_surface"]=cli
json.dump(st,open(p,"w")); print(slug)
PY
)
BURL="$URL/w/$SLUG"

# inline photos: `::: photo` blocks with a query: and no src: get a licensed photo in the background
if [ -n "$LESSON" ] && grep -q '^::: photo' "$LESSON" 2>/dev/null && grep -q '^query:' "$LESSON" 2>/dev/null; then
  PLOCK="$LESSON.photos.lock"
  if mkdir "$PLOCK" 2>/dev/null; then
    ( trap 'rmdir "$PLOCK" 2>/dev/null' EXIT; python3 "$DIR/../bin/photos.py" "$LESSON" >>"$HOME_DIR/image.log" 2>&1 ) >/dev/null 2>&1 &
  fi
fi

# lint: derivations written sideways are the most common contract violation; warn loudly, never block
[ -n "$LESSON" ] && python3 "$DIR/../bin/lint.py" "$LESSON" || true
# prose: hard-to-read sentences and terms used before they are explained (TEMPLATES.md, Tone)
[ -n "$LESSON" ] && python3 "$DIR/../bin/prose_lint.py" "$LESSON" || true

# bridge: launchd keeps it up (bin/install.sh, run once here on macOS); nohup is the fallback elsewhere
if [ "$(uname)" = Darwin ] && [ ! -f "$HOME/Library/LaunchAgents/com.blackboard.bridge.plist" ]; then
  zsh "$DIR/../bin/install.sh" || true
fi
if ! curl -s -m 1 "$URL/health" >/dev/null 2>&1; then
  launchctl kickstart "gui/$(id -u)/com.blackboard.bridge" 2>/dev/null || nohup python3 "$DIR/bridge.py" >"$HOME_DIR/bridge.log" 2>&1 &
  for i in {1..20}; do curl -s -m 1 "$URL/health" >/dev/null 2>&1 && break; sleep 0.15; done
fi

# open once per host
OPENED=$(python3 -c "import json;print(json.load(open('$STATE')).get('opened',''))" 2>/dev/null)
if [ "$LAYOUT" = cmux ]; then
  # look in every pane, not just the agent's own: `list-pane-surfaces` with no
  # --pane only reports the current pane, so the board was never found and a new
  # tab was opened on every render. Split the pane list on newlines explicitly;
  # an unquoted $(...) in a zsh `for` list does not word-split reliably here.
  S=""; ANY=""; BP=""
  for line in ${(f)"$(cmux list-panes 2>/dev/null)"}; do
    # first field, skipping the "*" focus marker (no extendedglob needed)
    pp=$(print -r -- "$line" | awk '{print ($1=="*")?$2:$1}')
    [[ "$pp" == pane:* ]] || continue
    for sl in ${(f)"$(cmux list-pane-surfaces --pane "$pp" 2>/dev/null | grep -E 'Blackboard|127\.0\.0\.1:'"$PORT")"}; do
      ss=$(print -r -- "$sl" | awk '{print ($1=="*")?$2:$1}'); [[ "$ss" == surface:* ]] || continue
      u=$(cmux browser --surface "$ss" url 2>/dev/null)
      if [[ "$u" == "$BURL"* ]]; then S=$ss; BP=$pp; break 2; fi
      [ -n "$ANY" ] || { ANY=$ss; BP=$pp; }
    done
  done
  [ -n "$S" ] || { S=$ANY; }
  if [ -n "$S" ]; then
    # The board must be the tab on screen. A hidden WKWebView pauses its timers, so it never follows the
    # current lesson, and a tab pinned to /lessons/NNNN never follows it at all. `goto` both navigates and
    # selects the tab; only do it when needed so a re-render of the visible lesson keeps its scroll.
    sel=$(cmux list-pane-surfaces --pane "$BP" 2>/dev/null | grep '^\*' | grep -o 'surface:[0-9]*' | head -1)
    cur=$(cmux browser --surface "$S" url 2>/dev/null)
    if [ "$sel" != "$S" ] || [[ "$cur" != "$BURL"* ]] || { [ -n "$ID" ] && [[ "$cur" == */lessons/* ]] && [[ "$cur" != */lessons/$ID* ]]; }; then
      [[ "$cur" == "$BURL"* ]] || cmux browser --surface "$S" goto "$BURL/" >/dev/null 2>&1
    fi
    # focus-webview is what actually selects the tab (it errors when the window is off screen, but still selects)
    [ "$sel" = "$S" ] || cmux browser --surface "$S" focus-webview >/dev/null 2>&1 || true
  fi
  if [ -z "$S" ]; then
    # pick a pane that does not hold the agent's own terminal surface
    P=""
    for line in ${(f)"$(cmux list-panes 2>/dev/null)"}; do
      p=$(print -r -- "$line" | awk '{print ($1=="*")?$2:$1}')
      [[ "$p" == pane:* ]] || continue
      if [ -n "$CMUX_SURFACE_ID" ] && cmux list-pane-surfaces --pane "$p" --id-format uuids 2>/dev/null | grep -qi "$CMUX_SURFACE_ID"; then continue; fi
      P=$p; break
    done
    if [ -n "$P" ]; then cmux new-surface --type browser --pane "$P" --url "$BURL/" --focus false >/dev/null
    else cmux new-pane --type browser --direction right --url "$BURL/" --focus false >/dev/null; fi
  fi
elif [ "$LAYOUT" = app ]; then
  # A shell process cannot create a Codex panel. Emit an explicit handoff for
  # the agent: create + navigate an in-app Browser tab, then present that exact
  # tab on the right with codex_app__open_in_codex.
  echo "codex-app-open-right: $BURL/"
elif [ "$OPENED" != "$BURL" ]; then
  open "$BURL/" 2>/dev/null || true
  python3 -c "import json;p='$STATE';s=json.load(open(p));s['opened']='$BURL';json.dump(s,open(p,'w'))"
fi

# stream mode (test aid): rewrite the lesson block by block
if [ "$STREAM" = 1 ] && [ -n "$LESSON" ]; then
  TMP=$(mktemp); cp "$LESSON" "$TMP"; : > "$LESSON"
  python3 - "$TMP" "$LESSON" <<'PY'
import sys,time,re
src,dst=sys.argv[1:]
text=open(src).read()
m=re.match(r'^---\n.*?\n---\n',text,re.S)
head=m.group(0) if m else ''
rest=text[len(head):]
with open(dst,'a') as f:
    f.write(head); f.flush(); time.sleep(0.4)
    for chunk in re.split(r'(\n\n)',rest):
        f.write(chunk); f.flush()
        if chunk.strip(): time.sleep(0.35)
PY
  rm -f "$TMP"
  python3 -c "import json;p='$STATE';s=json.load(open(p));s['streaming']=False;w=s.get('workspaces',{}).get('$SLUG');w and w.update(streaming=False);json.dump(s,open(p,'w'))"
fi
curl -s -m 2 -X POST "$URL/render?ws=$SLUG" >/dev/null 2>&1 || true
echo "board updated${ID:+: $ID}"
