#!/usr/bin/env python3
"""Validate and install a reviewed lesson video map, an existing MP4 and its caption track.

The caption track (captions.json from video_pipeline.py build-map, the cues' `show` texts in lesson notation) is
installed beside the MP4 as lessons/assets/NNNN-lecture.captions.json, where the board player fetches it and overlays
it on the video. `import` carries it when the map's folder has captions.json (or --captions names one); the
`captions` command installs or replaces just the track, for an installed video, without touching the video or map."""

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import captions as caption_lib  # noqa: E402


class ImportError_(ValueError):
    pass


def board_bridge():
    path = Path(__file__).resolve().parents[1] / "board" / "bridge.py"
    spec = importlib.util.spec_from_file_location("blackboard_video_bridge", path)
    module = importlib.util.module_from_spec(spec)
    # Importing the server creates its cache directory. Keep that side effect in
    # temporary storage; the validator itself only reads the supplied workspace.
    old = os.environ.get("BLACKBOARD_HOME")
    with tempfile.TemporaryDirectory(prefix="lesson-video-bridge-") as home:
        os.environ["BLACKBOARD_HOME"] = home
        try:
            spec.loader.exec_module(module)
        finally:
            if old is None:
                os.environ.pop("BLACKBOARD_HOME", None)
            else:
                os.environ["BLACKBOARD_HOME"] = old
    return module


def inside(path, parent):
    return path.resolve().is_relative_to(parent.resolve())


def lesson_bytes(bridge, workspace, lid):
    if not workspace.is_dir() or not (workspace / "lessons").is_dir():
        raise ImportError_(f"workspace has no lessons directory: {workspace}")
    lesson = bridge.lesson_path(lid, str(workspace))
    if lesson is None:
        raise ImportError_(f"lesson {lid} was not found in {workspace / 'lessons'}")
    path = Path(lesson)
    if not inside(path, workspace):
        raise ImportError_(f"lesson {lid} resolves outside the workspace")
    return path.read_bytes()


def load_map(path, lid, lesson):
    try:
        raw = path.read_bytes()
        manifest = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ImportError_(f"cannot read map {path}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ImportError_("map must be a JSON object")
    if manifest.get("lessonId") != lid:
        raise ImportError_(f"map lessonId must be {lid}")
    if manifest.get("video") != f"{lid}-lecture.mp4":
        raise ImportError_(f"map video must be {lid}-lecture.mp4")
    actual = hashlib.sha256(lesson).hexdigest()
    if not isinstance(manifest.get("lessonSha256"), str) or manifest["lessonSha256"].lower() != actual:
        raise ImportError_(f"map lessonSha256 differs from current lesson (actual {actual})")
    return raw, manifest


def probe_duration(video, required):
    executable = shutil.which("ffprobe")
    if not executable:
        if required:
            raise ImportError_("ffprobe is required for import to verify MP4 duration")
        return None
    try:
        result = subprocess.run(
            [executable, "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_type:format=duration", "-of", "json", str(video)],
            capture_output=True, text=True, timeout=60, check=True,
        )
        info = json.loads(result.stdout)
        duration = float(info["format"]["duration"])
        if not info.get("streams") or not math.isfinite(duration) or duration <= 0:
            raise ValueError("no video stream or valid duration")
        return duration
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ImportError_(f"ffprobe could not verify {video}: {exc}") from exc


def captions_source(mapping, explicit):
    """The caption track to carry: --captions, else captions.json beside the map, else None."""
    if explicit is not None:
        return explicit
    beside = mapping.parent / "captions.json"
    return beside if beside.is_file() else None


def check_captions(path, lid, duration):
    try:
        data = json.loads(path.read_bytes().decode("utf-8"))
        caption_lib.valid_track(data, lid, duration)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ImportError_(f"caption track {path}: {exc}") from exc
    return data


def validate(bridge, workspace, lid, video, mapping, require_probe=False, captions=None):
    lesson = lesson_bytes(bridge, workspace, lid)
    if not video.is_file() or video.suffix.lower() != ".mp4":
        raise ImportError_(f"existing MP4 not found: {video}")
    raw, manifest = load_map(mapping, lid, lesson)
    # The installed server is the source of truth for schema, source line,
    # interval, and practice gate checks. Its media check needs only a file.
    with tempfile.TemporaryDirectory(prefix="lesson-video-check-") as root:
        staged = Path(root)
        (staged / "lessons" / "assets").mkdir(parents=True)
        (staged / "reference").mkdir()
        (staged / "lessons" / f"{lid}-validation.md").write_bytes(lesson)
        (staged / "lessons" / "assets" / f"{lid}-lecture.mp4").touch()
        (staged / "reference" / f"video-{lid}.json").write_bytes(raw)
        result = bridge.lesson_video(lid, str(staged))
    if not result.get("available") or not result.get("mappingValid"):
        raise ImportError_("map rejected by board validator; check schema, source lines, intervals and practice gates")
    duration = probe_duration(video, required=require_probe)
    if duration is not None and abs(duration - manifest["duration"]) > 0.5:
        raise ImportError_(f"map duration {manifest['duration']}s differs from MP4 duration {duration:.3f}s (>0.5s)")
    if captions is not None:
        check_captions(captions, lid, manifest["duration"])
    return lesson, raw, duration


def safe_destination(workspace, directory, filename):
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        raise ImportError_(f"unsafe destination directory: {directory}")
    if not inside(directory, workspace):
        raise ImportError_(f"destination escapes workspace: {directory}")
    path = directory / filename
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ImportError_(f"unsafe destination file: {path}")
    return path


def same_file(source, destination):
    if not destination.exists() or source.stat().st_size != destination.stat().st_size:
        return False
    with source.open("rb") as left, destination.open("rb") as right:
        while True:
            a, b = left.read(1024 * 1024), right.read(1024 * 1024)
            if a != b:
                return False
            if not a:
                return True


def fsync_dir(directory):
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def staged_copy(source, directory):
    fd, name = tempfile.mkstemp(prefix=".lesson-video-", dir=directory)
    try:
        with os.fdopen(fd, "wb") as output, source.open("rb") as input_file:
            shutil.copyfileobj(input_file, output, 1024 * 1024)
            output.flush()
            os.fsync(output.fileno())
        return Path(name)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def install(bridge, workspace, lid, video, mapping, replace, dry_run, captions=None):
    lesson, _, duration = validate(bridge, workspace, lid, video, mapping, require_probe=True, captions=captions)
    asset_dir, ref_dir = workspace / "lessons" / "assets", workspace / "reference"
    media_target = safe_destination(workspace, asset_dir, f"{lid}-lecture.mp4")
    map_target = safe_destination(workspace, ref_dir, f"video-{lid}.json")
    targets = [(video, media_target), (mapping, map_target)]
    if captions is not None:
        targets.append((captions, safe_destination(workspace, asset_dir, f"{lid}-lecture.captions.json")))
    changed = [(src, dst) for src, dst in targets if not same_file(src, dst)]
    conflicts = [str(dst) for _, dst in changed if dst.exists()]
    if conflicts and not replace:
        raise ImportError_("existing file differs; use --replace to retain a durable backup: " + ", ".join(conflicts))
    if dry_run or not changed:
        return {"result": "dry-run" if dry_run else "unchanged", "files": [str(dst) for _, dst in changed], "duration": duration}

    # Recheck the lesson just before writes. Staged files and backups are
    # complete before the first publication, so failure can restore both paths.
    if lesson_bytes(bridge, workspace, lid) != lesson:
        raise ImportError_("lesson changed during validation; retry with a reviewed map")
    for directory in (asset_dir, ref_dir):
        directory.mkdir(exist_ok=True)
    staged, backups, published = {}, {}, []
    pending_backup = None
    try:
        for src, dst in changed:
            staged[dst] = staged_copy(src, dst.parent)
        for _, dst in changed:
            if dst.exists():
                backup = dst.with_name(f"{dst.name}.bak-{uuid.uuid4().hex}")
                pending_backup = staged_copy(dst, dst.parent)
                os.replace(pending_backup, backup)
                pending_backup = None
                backups[dst] = backup
                fsync_dir(dst.parent)
        if lesson_bytes(bridge, workspace, lid) != lesson:
            raise ImportError_("lesson changed during staging; no files imported")
        for _, dst in changed:
            os.replace(staged[dst], dst)
            del staged[dst]
            published.append(dst)
            fsync_dir(dst.parent)
        verified = bridge.lesson_video(lid, str(workspace))
        if not verified.get("available") or not verified.get("mappingValid"):
            raise ImportError_("installed files failed board validation")
        return {"result": "imported", "files": [str(dst) for _, dst in changed],
                "backups": [str(path) for path in backups.values()], "duration": duration}
    except BaseException:
        for dst in reversed(published):
            if dst in backups:
                restore = staged_copy(backups[dst], dst.parent)
                os.replace(restore, dst)
            else:
                dst.unlink(missing_ok=True)
            fsync_dir(dst.parent)
        # Rollback succeeded: discard only backups created by this failed run.
        for backup in backups.values():
            backup.unlink(missing_ok=True)
        raise
    finally:
        if pending_backup is not None:
            pending_backup.unlink(missing_ok=True)
        for path in staged.values():
            path.unlink(missing_ok=True)


def install_captions(workspace, lid, captions, replace, dry_run):
    """Install or replace only the caption track of an installed video (no render, no new map, no video copy)."""
    asset_dir = workspace / "lessons" / "assets"
    media = safe_destination(workspace, asset_dir, f"{lid}-lecture.mp4")
    map_path = safe_destination(workspace, workspace / "reference", f"video-{lid}.json")
    if not media.is_file() or not map_path.is_file():
        raise ImportError_(f"lesson {lid} has no installed video and map; import the video first")
    try:
        duration = json.loads(map_path.read_text(encoding="utf-8"))["duration"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ImportError_(f"cannot read installed map {map_path}: {exc}") from exc
    check_captions(captions, lid, duration)
    target = safe_destination(workspace, asset_dir, f"{lid}-lecture.captions.json")
    if same_file(captions, target):
        return {"result": "unchanged", "files": []}
    if target.exists() and not replace:
        raise ImportError_(f"existing caption track differs; use --replace to retain a durable backup: {target}")
    if dry_run:
        return {"result": "dry-run", "files": [str(target)]}
    backup = None
    if target.exists():
        backup = target.with_name(f"{target.name}.bak-{uuid.uuid4().hex}")
        os.replace(staged_copy(target, asset_dir), backup)
    os.replace(staged_copy(captions, asset_dir), target)
    fsync_dir(asset_dir)
    return {"result": "imported", "files": [str(target)], "backups": [str(backup)] if backup else []}


def status(bridge, workspace, lid):
    lesson_bytes(bridge, workspace, lid)
    media = safe_destination(workspace, workspace / "lessons" / "assets", f"{lid}-lecture.mp4")
    mapping = safe_destination(workspace, workspace / "reference", f"video-{lid}.json")
    track = safe_destination(workspace, workspace / "lessons" / "assets", f"{lid}-lecture.captions.json")
    result = bridge.lesson_video(lid, str(workspace))
    return {"lesson": lid, "videoExists": media.is_file(), "mapExists": mapping.is_file(), "captionsExist": track.is_file(),
            "available": result.get("available", False), "mappingValid": result.get("mappingValid", False),
            **({"error": result["error"]} if "error" in result else {})}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "import", "status", "captions"))
    parser.add_argument("--workspace", type=Path, required=True, help="path to the learn workspace")
    parser.add_argument("--lesson", required=True, help="four-digit lesson ID, e.g. 0013")
    parser.add_argument("--video", type=Path, help="existing MP4; validate/import only")
    parser.add_argument("--map", dest="mapping", type=Path, help="reviewed JSON map; validate/import only")
    parser.add_argument("--captions", type=Path, help="caption track (default: captions.json beside --map); "
                        "with the captions command, the track to install for the installed video")
    parser.add_argument("--dry-run", action="store_true", help="show import changes without writing")
    parser.add_argument("--replace", action="store_true", help="replace different files after durable backups")
    args = parser.parse_args(argv)
    if not args.lesson.isascii() or not (len(args.lesson) == 4 and args.lesson.isdigit()):
        parser.error("--lesson must be exactly four ASCII digits")
    if args.command not in ("import", "captions") and (args.dry_run or args.replace):
        parser.error("--dry-run and --replace apply only to import and captions")
    if args.command == "captions" and args.captions is None:
        parser.error("captions requires --captions")
    if args.command in ("validate", "import") and (args.video is None or args.mapping is None):
        parser.error("validate/import require --video and --map")
    try:
        bridge = board_bridge()
        workspace = args.workspace.expanduser().resolve()
        if args.command == "status":
            result = status(bridge, workspace, args.lesson)
        elif args.command == "captions":
            result = install_captions(workspace, args.lesson, args.captions, args.replace, args.dry_run)
        elif args.command == "validate":
            _, _, duration = validate(bridge, workspace, args.lesson, args.video, args.mapping,
                                      captions=captions_source(args.mapping, args.captions))
            result = {"result": "valid", "lesson": args.lesson, "duration": duration,
                      "warning": "ffprobe unavailable; MP4 duration unchecked" if duration is None else None}
        else:
            result = install(bridge, workspace, args.lesson, args.video, args.mapping, args.replace, args.dry_run,
                             captions_source(args.mapping, args.captions))
        print(json.dumps(result, indent=2))
        return 0
    except (ImportError_, OSError) as exc:
        print(f"lesson video: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
