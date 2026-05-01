import os
import sys
import datetime
from typing import List

LOG_BASENAME = "diagnostics.log"


def _ensure_dir(path: str) -> None:
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass


def get_log_path() -> str:
    """Return a writable absolute path for the diagnostics log.
    Prefers %LOCALAPPDATA%/AmareloMind/logs on Windows, falls back to project logs/.
    """
    base = None
    if sys.platform.startswith("win"):
        local = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if local:
            base = os.path.join(local, "AmareloMind", "logs")
    if not base:
        base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    _ensure_dir(base)
    return os.path.join(base, LOG_BASENAME)


def _write(lines: List[str]) -> None:
    path = get_log_path()
    try:
        with open(path, "a", encoding="utf-8") as f:
            for ln in lines:
                f.write(ln.rstrip("\n") + "\n")
    except Exception:
        # Avoid breaking app on logging failure
        pass


def _hdr(title: str) -> None:
    _write(["", f"=== {title} ==="])


def run_startup_checks() -> None:
    """Run safe, pre-QApplication diagnostics and append to diagnostics.log.
    This does not require a QApplication and should be called as early as possible.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write([f"\n===== Amarelo Mind Diagnostics @ {now} ====="]) 

    # Python and OS
    _hdr("Python/OS")
    _write([
        f"python_executable = {sys.executable}",
        f"python_version    = {sys.version.split()[0]}",
        f"platform          = {sys.platform}",
        f"cwd               = {os.getcwd()}",
    ])

    # Important environment variables
    _hdr("Environment")
    keys = [
        "AMARELO_OPENGL", "AMARELO_DISABLE_GPU", "AMARELO_LOG_WEBENGINE",
        "QTWEBENGINE_CHROMIUM_FLAGS", "QT_LOGGING_RULES", "QT_PLUGIN_PATH",
        "PATH", "PYTHONPATH",
    ]
    env_lines = []
    for k in keys:
        v = os.environ.get(k)
        if v is not None:
            if k == "PATH":
                # keep it short
                env_lines.append(f"{k} = ...{v[-200:]}" if len(v) > 220 else f"{k} = {v}")
            else:
                env_lines.append(f"{k} = {v}")
        else:
            env_lines.append(f"{k} = <unset>")
    _write(env_lines)

    # PySide6 / Qt presence
    _hdr("PySide6/Qt modules")
    try:
        import PySide6
        from PySide6 import QtCore
        ver = getattr(PySide6, "__version__", "?")
        qtver = getattr(QtCore, "qVersion", lambda: "?")()
        _write([f"PySide6.__version__ = {ver}", f"Qt version           = {qtver}"])
    except Exception as e:
        _write([f"PySide6 import failed: {e!r}"])
        return

    # Qt paths
    try:
        from PySide6.QtCore import QLibraryInfo
        paths = {
            "PrefixPath": QLibraryInfo.path(QLibraryInfo.PrefixPath),
            "PluginsPath": QLibraryInfo.path(QLibraryInfo.PluginsPath),
            "LibraryExecutablesPath": QLibraryInfo.path(QLibraryInfo.LibraryExecutablesPath),
            "QmlImportsPath": QLibraryInfo.path(QLibraryInfo.QmlImportsPath),
            "ArchDataPath": QLibraryInfo.path(QLibraryInfo.ArchDataPath),
        }
        _hdr("Qt paths (QLibraryInfo)")
        for k, v in paths.items():
            _write([f"{k} = {v}"])
        # List known plugin subdirs of interest
        plug = paths.get("PluginsPath") or ""
        subdirs = ["platforms", "styles", "imageformats", "multimedia", "multimedia/audio", "mediaservice", "renderers"]
        _hdr("Qt plugin subdirs")
        for sd in subdirs:
            p = os.path.join(plug, sd)
            try:
                items = os.listdir(p) if os.path.isdir(p) else []
                _write([f"{sd}: {p}  ({len(items)} files)"])
            except Exception:
                _write([f"{sd}: {p}  (<unreadable>)"])
    except Exception as e:
        _write([f"QLibraryInfo failed: {e!r}"])

    # Image formats available
    try:
        from PySide6.QtGui import QImageReader
        fmts = [bytes(f).decode(errors="ignore") for f in QImageReader.supportedImageFormats()]
        _hdr("Supported image formats")
        _write([", ".join(sorted(fmts))])
    except Exception as e:
        _write([f"QImageReader failed: {e!r}"])

    # QtMultimedia and WebEngine availability (import-level only)
    _hdr("Qt modules availability")
    def _try_import(mod: str) -> None:
        try:
            __import__(mod)
            _write([f"ok: import {mod}"])
        except Exception as ex:
            _write([f"FAIL: import {mod} -> {ex!r}"])
    for m in [
        "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
    ]:
        _try_import(m)

    _write(["===== end diagnostics =====\n"])
