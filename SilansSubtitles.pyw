"""Окно для скачивания субтитров и видео YouTube."""

import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
import webbrowser
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, simpledialog, ttk

try:
    from tkinterdnd2 import DND_FILES, DND_TEXT, TkinterDnD
except ImportError:
    DND_FILES = DND_TEXT = TkinterDnD = None

from PIL import Image, ImageDraw, ImageFilter, ImageTk

_ytdlp_lock = threading.Lock()
_ytdlp_types = None


def ytdlp_types():
    global _ytdlp_types
    with _ytdlp_lock:
        if _ytdlp_types is None:
            from yt_dlp import YoutubeDL
            from yt_dlp.utils import DownloadError
            _ytdlp_types = (YoutubeDL, DownloadError)
        return _ytdlp_types


def app_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


OUT_DIR = app_dir()
ASSETS = OUT_DIR / "assets"
PRIORITY = ["ru", "uk", "en-orig", "en", "de", "fr", "es", "pl", "tr", "kk", "be"]
BG = "#03040c"
BG_RGB = (3, 4, 12)
# False leaves the hole and stars in place and does not schedule frames.
COSMIC_ANIMATION = True
CHANNEL_URL = "https://www.youtube.com/@Silans"
SUBTITLE_FORMATS = (
    ("srt", "SRT"),
    ("ass", "ASS"),
    ("vtt", "VTT"),
    ("ttml", "TTML"),
    ("lrc", "LRC"),
)
FORMAT_BY_LABEL = {label: ext for ext, label in SUBTITLE_FORMATS}
VIDEO_FORMATS = (
    ("mp4", "MP4"),
    ("mkv", "MKV"),
    ("webm", "WEBM"),
)
VIDEO_FORMAT_BY_LABEL = {label: ext for ext, label in VIDEO_FORMATS}
UI_LANG = "ru"
UI = {
    "ru": {
        "paste": "Вставить",
        "search": "Найти",
        "placeholder": "Вставьте ссылку на ролик",
        "video": "Видео",
        "subs": "Субтитры",
        "download": "Скачать",
        "folder": "Открыть папку",
        "pick_folder": "Выбрать папку",
        "folder_set": "Файлы будут сохраняться в {name}.",
        "started": "Скачивание началось.",
        "queue": "Очередь",
        "hint": "Слева видео, справа субтитры. Скачивания идут по очереди.",
        "empty": "Пока пусто. Скачивания появятся здесь, их можно отменить.",
        "need_link": "Вставьте ссылку.",
        "need_http": "Ссылка должна начинаться с http:// или https://.",
        "need_any": "Вставьте ссылку на видео или на файл субтитров.",
        "need_known": "Нужна ссылка на видео или на файл субтитров: SRT, VTT, ASS, TTML, LRC.",
        "cam": "Камера",
        "screen": "Экран",
        "screen_cam": "Экран и камера",
        "passcode_title": "Код доступа",
        "passcode_prompt": "Эта запись закрыта кодом. Введите его, если он у вас есть.",
        "no_media": "У этого видео нет ни картинки, ни звука, ни субтитров.",
        "no_subs": "У этого видео нет субтитров.",
        "bad_cues": "Не удалось разобрать субтитры для выбранного формата.",
        "bad_fmt": "Этот формат субтитров не поддерживается.",
        "subs_fail": "Не удалось скачать субтитры.",
        "subs_missing": "Файл субтитров не появился. Попробуйте другую дорожку.",
        "subs_read": "Не удалось прочитать субтитры по этой ссылке.",
        "subs_convert": "Этот файл можно сохранить как {source}. В {fmt} он не конвертируется.",
        "subs_http": "Не удалось скачать субтитры по этой ссылке.",
        "need_ffmpeg": "Для этого качества нужен ffmpeg рядом с программой. Выберите формат, где видео и звук уже в одном файле, или только звук.",
        "rate_limit": "YouTube временно ограничил запросы. Подождите минуту и скачайте ещё раз.",
        "video_fail": "Не удалось скачать видео.",
        "file_missing": "Файл не появился. Попробуйте другое качество.",
        "file_busy": "Файл был занят другим скачиванием.",
        "av": "видео и звук",
        "audio_only": "только звук",
        "audio_code": "звук",
        "manual": "оригинал",
        "orig": "авто, оригинал",
        "auto": "авто",
        "subtitle_file": "Файл субтитров",
        "via_link": "по ссылке",
        "video_fallback": "Видео",
        "checking": "Смотрю ссылку…",
        "file_ready": "Это файл субтитров. Он в правом списке.",
        "found": "Видео: {videos}. Субтитры: {subs}.",
        "pick_video": "Слева выберите качество видео или звук.",
        "pick_subs": "Справа выберите дорожку субтитров.",
        "no_track": "Этой дорожки у ролика нет.",
        "picked": "Выбраны субтитры: {code} · {name}.",
        "save_media": "Куда сохранить файл",
        "save_subs": "Куда сохранить субтитры",
        "audio_word": "Звук",
        "queued": "в очереди",
        "cancel": "Отмена",
        "added": "Добавлено в очередь.",
        "cancelled_state": "отменено",
        "cancelled_btn": "Отменено",
        "cancelling": "отмена…",
        "downloading": "скачивание…",
        "saved_job": "сохранено: {name}",
        "done": "Готово",
        "error": "Ошибка",
        "saved": "Сохранено: {name}",
    },
    "eng": {
        "paste": "Paste",
        "search": "Search",
        "placeholder": "Paste a video link",
        "video": "Video",
        "subs": "Subtitles",
        "download": "Download",
        "folder": "Open folder",
        "pick_folder": "Choose folder",
        "folder_set": "Files will be saved to {name}.",
        "started": "Download started.",
        "queue": "Queue",
        "hint": "Video on the left, subtitles on the right. Downloads run one by one.",
        "empty": "Nothing yet. Downloads show up here and can be cancelled.",
        "need_link": "Paste a link.",
        "need_http": "The link must start with http:// or https://.",
        "need_any": "Paste a video link or a subtitle file link.",
        "need_known": "Paste a video link or a subtitle file: SRT, VTT, ASS, TTML, LRC.",
        "cam": "Camera",
        "screen": "Screen",
        "screen_cam": "Screen and camera",
        "passcode_title": "Passcode",
        "passcode_prompt": "This recording is locked. Enter the passcode if you have it.",
        "no_media": "This video has no picture, audio, or subtitles.",
        "no_subs": "This video has no subtitles.",
        "bad_cues": "Could not read the subtitles for this format.",
        "bad_fmt": "This subtitle format is not supported.",
        "subs_fail": "Could not download the subtitles.",
        "subs_missing": "The subtitle file did not appear. Try another track.",
        "subs_read": "Could not read the subtitles from this link.",
        "subs_convert": "This file can be saved as {source}. It cannot be converted to {fmt}.",
        "subs_http": "Could not download the subtitles from this link.",
        "need_ffmpeg": "This quality needs ffmpeg next to the program. Pick a single file or audio only.",
        "rate_limit": "YouTube is limiting requests. Wait a minute and try again.",
        "video_fail": "Could not download the video.",
        "file_missing": "The file did not appear. Try another quality.",
        "file_busy": "The file was still in use by another download.",
        "av": "video and audio",
        "audio_only": "audio only",
        "audio_code": "audio",
        "manual": "original",
        "orig": "auto, original",
        "auto": "auto",
        "subtitle_file": "Subtitle file",
        "via_link": "from link",
        "video_fallback": "Video",
        "checking": "Checking the link…",
        "file_ready": "This is a subtitle file. It is in the list on the right.",
        "found": "Video: {videos}. Subtitles: {subs}.",
        "pick_video": "Pick a video quality or audio track on the left.",
        "pick_subs": "Pick a subtitle track on the right.",
        "no_track": "This video does not have that track.",
        "picked": "Subtitles selected: {code} · {name}.",
        "save_media": "Where to save the file",
        "save_subs": "Where to save the subtitles",
        "audio_word": "Audio",
        "queued": "queued",
        "cancel": "Cancel",
        "added": "Added to the queue.",
        "cancelled_state": "cancelled",
        "cancelled_btn": "Cancelled",
        "cancelling": "cancelling…",
        "downloading": "downloading…",
        "saved_job": "saved: {name}",
        "done": "Done",
        "error": "Error",
        "saved": "Saved: {name}",
    },
}


def tr(key, **kwargs):
    table = UI.get(UI_LANG) or UI["ru"]
    text = table.get(key) or UI["ru"].get(key) or key
    return text.format(**kwargs) if kwargs else text


CUE_TIME = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


_video_password = ""


def normalize_url(text):
    url = (text or "").strip()
    if not url:
        raise ValueError(tr("need_link"))
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError(tr("need_http"))
    return url


def is_youtube(url):
    lowered = (url or "").lower()
    return "youtube.com" in lowered or "youtu.be" in lowered


def apply_password(options):
    if _video_password:
        options["videopassword"] = _video_password
    return options


def needs_passcode(text):
    lowered = (text or "").lower()
    return "passcode" in lowered or "video-password" in lowered or "wrong password" in lowered


def site_host(url):
    match = re.search(r"^https?://([^/?#]+)", (url or "").strip(), re.I)
    if not match:
        return ""
    host = match.group(1).lower()
    if host.startswith("www."):
        host = host[4:]
    return host[:80]


def resource_dir():
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", app_dir()))
    return app_dir()


def _read_telegram(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "", ""
    return str(data.get("token") or "").strip(), str(data.get("chat_id") or "").strip()


def telegram_target():
    token, chat = "", ""
    seen = set()
    for folder in (app_dir(), resource_dir()):
        key = str(folder)
        if key in seen:
            continue
        seen.add(key)
        file_token, file_chat = _read_telegram(folder / "telegram.json")
        token = token or file_token
        chat = chat or file_chat
    if not token or not chat:
        try:
            import silans_telegram
        except ImportError:
            silans_telegram = None
        if silans_telegram is not None:
            token = token or str(getattr(silans_telegram, "TOKEN", "") or "").strip()
            chat = chat or str(getattr(silans_telegram, "CHAT", "") or "").strip()
    return token, chat


_STATS_LOCK = threading.Lock()
_BOT_COMMANDS = (
    ("stats", "Общая статистика"),
    ("today", "Статистика за сегодня"),
    ("recent", "Последние события"),
    ("errors", "Последние ошибки"),
    ("hosts", "Какие сайты открывали"),
    ("help", "Список команд"),
)


def telegram_call(token, method, payload=None, timeout=20):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/{method}",
        data=data,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "ignore")
        if "message is not modified" in detail:
            return {"ok": True, "result": {}}
        raise
    if not body.get("ok"):
        raise RuntimeError(str(body.get("description") or "telegram"))
    return body


def _blank_stats():
    return {
        "launches": 0,
        "searches": 0,
        "downloads": 0,
        "errors": 0,
        "installs": [],
        "hosts": {},
        "days": {},
        "recent": [],
        "errors_log": [],
    }


def _public_error(text):
    cleaned = str(text or "").replace(str(Path.home()), "~")
    return cleaned[:180]


def _parse_stats(text):
    marker = "SILANS_STATS\n"
    if marker not in (text or ""):
        return None
    try:
        data = json.loads(text.split(marker, 1)[1])
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    stats = _blank_stats()
    for key in stats:
        if key in data:
            stats[key] = data[key]
    return stats


def _stats_message(data):
    lines = [
        "Silans · сводка",
        f"Запуски: {data['launches']}",
        f"Поиски: {data['searches']}",
        f"Скачивания: {data['downloads']}",
        f"Ошибки: {data['errors']}",
        f"Установки: {len(data['installs'])}",
    ]
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    text = "\n".join(lines) + "\n\nSILANS_STATS\n" + raw
    if len(text) > 3900:
        data["recent"] = list(data["recent"])[-5:]
        data["errors_log"] = list(data["errors_log"])[-4:]
        raw = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        text = "\n".join(lines) + "\n\nSILANS_STATS\n" + raw
    return text[:4096]


def _find_stats_message(token, chat):
    result = telegram_call(token, "getChat", {"chat_id": chat})
    pin = (result.get("result") or {}).get("pinned_message") or {}
    parsed = _parse_stats(pin.get("text") or "")
    if parsed is None:
        return None, _blank_stats()
    return pin.get("message_id"), parsed


def _write_stats(token, chat, data, message_id):
    text = _stats_message(data)
    if message_id:
        try:
            telegram_call(token, "editMessageText", {
                "chat_id": chat,
                "message_id": message_id,
                "text": text,
                "disable_web_page_preview": True,
            })
            return message_id
        except Exception:
            message_id = None
    sent = telegram_call(token, "sendMessage", {
        "chat_id": chat,
        "text": text,
        "disable_web_page_preview": True,
    })
    message_id = (sent.get("result") or {}).get("message_id")
    if message_id:
        try:
            telegram_call(token, "pinChatMessage", {
                "chat_id": chat,
                "message_id": message_id,
                "disable_notification": True,
            })
        except Exception:
            return message_id
    return message_id


def _bump_stats(data, event, meta):
    day = time.strftime("%Y-%m-%d", time.gmtime())
    bucket = data["days"].setdefault(day, {"launches": 0, "searches": 0, "downloads": 0, "errors": 0})
    install = str(meta.get("id") or "")[:24]
    if install and install not in data["installs"]:
        data["installs"] = (list(data["installs"]) + [install])[-300:]
    host = str(meta.get("host") or "")[:80]
    if host:
        hosts = dict(data["hosts"])
        hosts[host] = int(hosts.get(host) or 0) + 1
        if len(hosts) > 40:
            hosts = dict(sorted(hosts.items(), key=lambda item: item[1], reverse=True)[:30])
        data["hosts"] = hosts
    note = {
        "t": time.strftime("%m-%d %H:%M", time.gmtime()),
        "event": event,
        "host": host,
        "id": install[:8],
    }
    if event == "launch":
        data["launches"] += 1
        bucket["launches"] += 1
    elif event == "search":
        data["searches"] += 1
        bucket["searches"] += 1
    elif event == "download":
        data["downloads"] += 1
        bucket["downloads"] += 1
        note["item"] = str(meta.get("kind") or "")[:20]
    elif event == "error":
        data["errors"] += 1
        bucket["errors"] += 1
        note["text"] = _public_error(meta.get("text"))
        data["errors_log"] = (list(data["errors_log"]) + [dict(note)])[-8:]
    else:
        return
    data["recent"] = (list(data["recent"]) + [{key: value for key, value in note.items() if value}])[-12:]
    if len(data["days"]) > 21:
        for key in sorted(data["days"])[:-14]:
            data["days"].pop(key, None)


def record_stats(event, meta):
    token, chat = telegram_target()
    if not token or not chat or event not in {"launch", "search", "download", "error"}:
        return
    with _STATS_LOCK:
        message_id, data = _find_stats_message(token, chat)
        _bump_stats(data, event, meta or {})
        _write_stats(token, chat, data, message_id)


def _command_reply(command, data):
    command = command.split("@", 1)[0].lower()
    if command in {"/start", "/help"}:
        return (
            "Силанс на связи.\n"
            "Запуск, поиск, скачивание и ошибки приходят сами.\n"
            "Закреплённое сообщение — живая сводка.\n\n"
            "/stats — всего\n"
            "/today — за сегодня, UTC\n"
            "/recent — последние события\n"
            "/errors — последние ошибки\n"
            "/hosts — сайты"
        )
    if command == "/stats":
        return (
            "Всего\n"
            f"Запуски: {data['launches']}\n"
            f"Поиски: {data['searches']}\n"
            f"Скачивания: {data['downloads']}\n"
            f"Ошибки: {data['errors']}\n"
            f"Установки: {len(data['installs'])}"
        )
    if command == "/today":
        day = time.strftime("%Y-%m-%d", time.gmtime())
        bucket = data["days"].get(day) or {}
        return (
            f"Сегодня {day} UTC\n"
            f"Запуски: {bucket.get('launches', 0)}\n"
            f"Поиски: {bucket.get('searches', 0)}\n"
            f"Скачивания: {bucket.get('downloads', 0)}\n"
            f"Ошибки: {bucket.get('errors', 0)}"
        )
    if command == "/recent":
        rows = list(data["recent"])[-8:]
        if not rows:
            return "Событий пока нет."
        lines = ["Последние события"]
        for row in rows:
            bits = [row.get("t") or "", row.get("event") or "", row.get("host") or "", row.get("item") or ""]
            lines.append(" · ".join(bit for bit in bits if bit))
        return "\n".join(lines)
    if command == "/errors":
        rows = list(data["errors_log"])[-5:]
        if not rows:
            return "Ошибок пока нет."
        lines = ["Последние ошибки"]
        for row in rows:
            lines.append(f"{row.get('t') or ''} · {row.get('host') or '—'} · {row.get('text') or 'ошибка'}")
        return "\n".join(lines)
    if command == "/hosts":
        hosts = data["hosts"] or {}
        if not hosts:
            return "Сайтов пока нет."
        lines = ["Сайты"]
        ranked = sorted(hosts.items(), key=lambda item: item[1], reverse=True)[:8]
        lines.extend(f"{count} · {name}" for name, count in ranked)
        return "\n".join(lines)
    return ""


def owner_listens():
    path = app_dir() / "telegram.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("listen"))


def _process_alive(pid):
    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(0x1000, False, int(pid))
    if not handle:
        return False
    kernel32.CloseHandle(handle)
    return True


def _bot_pid_path():
    return app_dir() / "bot.pid"


def _bot_is_running():
    try:
        pid = int(_bot_pid_path().read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    return _process_alive(pid)


def _hold_bot_mutex():
    if _bot_is_running():
        return False
    try:
        _bot_pid_path().write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        return False
    return True


def _bot_log(text):
    try:
        with (app_dir() / "bot.log").open("a", encoding="utf-8") as handle:
            handle.write(time.strftime("%H:%M:%S ") + text + "\n")
    except OSError:
        return


def bot_commands():
    if not owner_listens() or not _hold_bot_mutex():
        return
    token, chat = telegram_target()
    if not token or not chat:
        _bot_log("no target")
        return
    try:
        telegram_call(token, "setMyCommands", {
            "commands": [{"command": name, "description": text} for name, text in _BOT_COMMANDS],
        })
    except Exception as error:
        _bot_log("commands " + type(error).__name__)
    offset = None
    while True:
        try:
            payload = {"timeout": 25, "allowed_updates": ["message"]}
            if offset is not None:
                payload["offset"] = offset
            result = telegram_call(token, "getUpdates", payload, timeout=35)
            for update in result.get("result") or []:
                offset = update["update_id"] + 1
                message = update.get("message") or {}
                if str((message.get("chat") or {}).get("id") or "") != str(chat):
                    continue
                text = str(message.get("text") or "").strip()
                if not text.startswith("/"):
                    continue
                command = text.split()[0]
                try:
                    _message_id, data = _find_stats_message(token, chat)
                except Exception:
                    data = _blank_stats()
                reply = _command_reply(command, data)
                if not reply:
                    continue
                telegram_call(token, "sendMessage", {
                    "chat_id": chat,
                    "text": reply[:4000],
                    "disable_web_page_preview": True,
                })
        except Exception as error:
            _bot_log("loop " + type(error).__name__ + " " + str(error)[:180])
            time.sleep(5)


def ensure_bot_process():
    if not owner_listens() or _bot_is_running():
        return
    if getattr(sys, "frozen", False):
        command = [sys.executable, "--bot"]
    else:
        command = [sys.executable, str(Path(__file__).resolve()), "--bot"]
    subprocess.Popen(command, cwd=str(app_dir()), creationflags=0x00000008)


def send_telegram(kind, lines, meta=None):
    token, chat = telegram_target()
    if not token or not chat or ":" not in token:
        return
    try:
        record_stats(kind, meta or {})
    except Exception:
        pass
    text = ("Silans · " + kind + "\n" + "\n".join(lines))[:3500]
    try:
        telegram_call(token, "sendMessage", {
            "chat_id": chat,
            "text": text,
            "disable_web_page_preview": True,
        })
    except Exception:
        return


def report_async(kind, lines, meta=None):
    threading.Thread(
        target=send_telegram,
        args=(kind, list(lines), dict(meta or {})),
        daemon=True,
    ).start()


def classify_url(text):
    raw = (text or "").strip()
    if not raw:
        raise ValueError(tr("need_any"))
    lowered = raw.lower()
    path = lowered.split("?", 1)[0].split("#", 1)[0]
    if path.endswith((".srt", ".vtt", ".ass", ".ttml", ".lrc")) or "timedtext" in lowered:
        return "subtitle", raw
    if not lowered.startswith(("http://", "https://")):
        raise ValueError(tr("need_known"))
    if is_youtube(lowered):
        return "youtube", normalize_url(raw)
    return "media", normalize_url(raw)


def track_kind(code, name, manual):
    if manual:
        return "manual"
    if str(code).endswith("-orig") or "Original" in str(name):
        return "orig"
    return "auto"


def kind_label(kind):
    return tr(kind if kind in {"manual", "orig", "auto"} else "auto")


def _subtitle_url(formats):
    ranked = []
    for item in formats or []:
        link = item.get("url") or ""
        if not link:
            continue
        ext = str(item.get("ext") or "").lower()
        rank = 0 if ext == "vtt" else 1 if ext == "srt" else 2
        ranked.append((rank, link))
    if not ranked:
        return ""
    ranked.sort(key=lambda item: item[0])
    return ranked[0][1]


def _file_in_use(error):
    if getattr(error, "winerror", None) == 32:
        return True
    text = str(error).lower()
    return "winerror 32" in text or "being used by another process" in text


def collect_tracks(info):
    webpage = info.get("webpage_url") or info.get("original_url") or ""
    youtube = is_youtube(webpage)
    referer = str((info.get("http_headers") or {}).get("Referer") or "")
    tracks = []
    seen = set()
    groups = (
        (info.get("subtitles") or {}, True),
        (info.get("automatic_captions") or {}, False),
    )
    for bucket, manual in groups:
        for code, formats in bucket.items():
            if code in seen or not formats:
                continue
            link = _subtitle_url(formats)
            if not link and not youtube:
                continue
            name = ""
            for item in formats:
                if item.get("name"):
                    name = item["name"]
                    break
            seen.add(code)
            tracks.append({
                "code": code,
                "name": name or code,
                "kind": track_kind(code, name, manual),
                "url": link,
                "referer": referer,
            })

    def sort_key(track):
        if track["code"] in PRIORITY:
            return (0, PRIORITY.index(track["code"]))
        kind_rank = {"manual": 0, "orig": 1, "auto": 2}[track["kind"]]
        return (1, kind_rank, track["name"].casefold())

    tracks.sort(key=sort_key)
    return tracks


_request_lock = threading.Lock()
_next_request_at = 0.0


def mark_rate_limit(seconds):
    global _next_request_at
    with _request_lock:
        _next_request_at = max(_next_request_at, time.time() + seconds)


def sleep_cancel(seconds, cancel):
    deadline = time.time() + max(0, seconds)
    while time.time() < deadline:
        ensure_running(cancel)
        time.sleep(min(0.4, deadline - time.time()))


def wait_turn(cancel):
    while True:
        ensure_running(cancel)
        with _request_lock:
            delay = _next_request_at - time.time()
        if delay <= 0:
            break
        time.sleep(min(0.4, delay))


def base_options():
    return {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "windowsfilenames": True,
        "sleep_interval_requests": 1.5,
        "extractor_retries": 3,
    }


def human_size(size):
    if not size:
        return ""
    value = float(size)
    units = ("Б", "КБ", "МБ", "ГБ") if UI_LANG == "ru" else ("B", "KB", "MB", "GB")
    for index, unit in enumerate(units):
        if value < 1024 or index == len(units) - 1:
            number = f"{value:.0f}" if value >= 10 or index == 0 else f"{value:.1f}"
            return f"{number} {unit}"
        value /= 1024
    return ""


def collect_media(info):
    formats = []
    for item in info.get("formats") or []:
        note = str(item.get("format_note") or "")
        protocol = str(item.get("protocol") or "")
        ext = str(item.get("ext") or "")
        if "storyboard" in note.lower() or "mhtml" in protocol or ext in {"mhtml", "jpg", "png"}:
            continue
        if item.get("vcodec") == "none" and item.get("acodec") in (None, "none"):
            continue
        formats.append(item)

    def bytes_of(item):
        return item.get("filesize") or item.get("filesize_approx") or 0

    options = []
    used_ids = set()

    def add_direct(item):
        protocol = str(item.get("protocol") or "")
        ext = item.get("ext") or "mp4"
        hls = "m3u8" in protocol or ext == "m3u8"
        if hls:
            ext = "mp4"
        height = item.get("height")
        fps = item.get("fps") or 0
        note = item.get("format_note") or ""
        note_key = {
            "Camera stream": "cam",
            "Screen share stream": "screen",
            "Screen share with camera": "screen_cam",
        }.get(note)
        if height:
            code = f"{int(height)}p" + (str(int(fps)) if fps >= 50 else "")
        else:
            code = "MP4" if note_key else str(item.get("format_id") or ext).upper()[:18]
        row = {
            "type": "video",
            "code": code,
            "name": note or str(ext).upper(),
            "detail": "",
            "bytes": bytes_of(item),
            "selector": item.get("format_id") or "best",
            "ext": ext,
            "merged": hls,
            "_pref": item.get("preference") or 0,
        }
        if note_key:
            row["name_key"] = note_key
        options.append(row)
        if item.get("format_id"):
            used_ids.add(item.get("format_id"))

    heights = sorted(
        {
            item.get("height")
            for item in formats
            if item.get("height") and item.get("vcodec") not in (None, "none")
        },
        reverse=True,
    )
    for height in heights:
        group = [
            item for item in formats
            if item.get("height") == height and item.get("vcodec") not in (None, "none")
        ]
        notes = {item.get("format_note") or "" for item in group}
        if len(notes) > 1 and any(notes):
            for item in group:
                if item.get("vcodec") == "none":
                    continue
                add_direct(item)
            continue
        mp4 = [item for item in group if item.get("ext") == "mp4"]
        pool = mp4 or group
        ext = pool[0].get("ext") or "mp4"
        progressive = [item for item in pool if item.get("acodec") not in (None, "none")]
        fps = max((item.get("fps") or 0) for item in pool)
        quality = f"{int(height)}p" + (str(int(fps)) if fps and fps >= 50 else "")
        if progressive:
            best = max(progressive, key=lambda item: item.get("tbr") or 0)
            selector = best["format_id"]
            size = bytes_of(best)
            merged = False
            ext = best.get("ext") or ext
            used_ids.add(best.get("format_id"))
        else:
            selector = (
                f"bv*[height={int(height)}][ext={ext}]+ba[ext=m4a]/"
                f"bv*[height={int(height)}]+ba/b[height={int(height)}]"
            )
            video_size = max(bytes_of(item) for item in pool)
            audios = [
                item for item in formats
                if item.get("vcodec") in (None, "none")
                and item.get("acodec") not in (None, "none")
                and item.get("ext") in {"m4a", "mp4"}
            ]
            size = video_size + max((bytes_of(item) for item in audios), default=0)
            merged = True
            if ext == "mp4":
                ext = "mp4"
            used_ids.update(item.get("format_id") for item in pool)
        options.append({
            "type": "video",
            "code": quality,
            "name": str(ext).upper(),
            "detail": "",
            "bytes": size,
            "selector": selector,
            "ext": ext,
            "merged": merged,
        })

    direct = []
    for item in formats:
        if item.get("format_id") in used_ids or item.get("vcodec") == "none":
            continue
        if item.get("height") and item.get("vcodec") not in (None, "none"):
            continue
        before = len(options)
        add_direct(item)
        if len(options) > before:
            direct.append(options.pop())
    direct.sort(key=lambda row: row.get("_pref") or 0, reverse=True)
    options = direct + options

    audio_groups = (
        ("m4a", "M4A", lambda item: item.get("ext") == "m4a"),
        ("webm", "OPUS", lambda item: item.get("ext") == "webm" or "opus" in str(item.get("acodec") or "")),
    )
    used = set()
    for ext, title, match in audio_groups:
        pool = [
            item for item in formats
            if item.get("vcodec") in (None, "none")
            and item.get("acodec") not in (None, "none")
            and item.get("format_id") not in used
            and match(item)
        ]
        if not pool:
            continue
        best = max(pool, key=lambda item: item.get("abr") or item.get("tbr") or 0)
        used.add(best.get("format_id"))
        size = bytes_of(best)
        options.append({
            "type": "audio",
            "code": "звук",
            "name": title,
            "detail": "",
            "bytes": size,
            "selector": best["format_id"],
            "ext": best.get("ext") or ext,
            "merged": False,
        })
    return options


def inspect_link(text):
    kind, url = classify_url(text)
    if kind == "subtitle":
        ext = Path(url.split("?", 1)[0].split("#", 1)[0]).suffix.lower().lstrip(".") or "srt"
        return {
            "kind": "subtitle",
            "title": "",
            "url": url,
            "rows": [{
                "type": "file",
                "code": ext.upper(),
                "name": "",
                "name_key": "subtitle_file",
                "detail": "",
                "detail_key": "via_link",
                "url": url,
            }],
        }
    options = apply_password(base_options())
    YoutubeDL, _download_error = ytdlp_types()
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    title = info.get("title") or info.get("id") or ""
    rows = collect_media(info)
    for track in collect_tracks(info):
        rows.append({
            "type": "subs",
            "code": track["code"],
            "name": track["name"],
            "detail": "",
            "kind": track["kind"],
            "lang": track["code"],
            "url": track.get("url") or "",
            "referer": track.get("referer") or "",
        })
    if not rows:
        raise ValueError(tr("no_media"))
    return {"kind": "youtube", "title": title, "rows": rows, "url": url}


def find_tracks(url):
    result = inspect_link(url)
    tracks = [
        {"code": row["lang"], "name": row["name"], "kind": "auto"}
        for row in result["rows"]
        if row["type"] == "subs"
    ]
    if not tracks:
        raise ValueError(tr("no_subs"))
    return {"title": result["title"], "video_id": "", "tracks": tracks}


def ffmpeg_location():
    folder = app_dir() / "ffmpeg"
    if (folder / "ffmpeg.exe").exists():
        return str(folder)
    if (app_dir() / "ffmpeg.exe").exists():
        return str(app_dir())
    return None


def clock_ms(hours, minutes, seconds, millis):
    return ((int(hours) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(millis)


def parse_srt(text):
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    cues = []
    for block in re.split(r"\n\s*\n", normalized.strip()):
        lines = block.split("\n")
        timing = None
        body_at = 0
        for index, line in enumerate(lines):
            timing = CUE_TIME.search(line)
            if timing:
                body_at = index + 1
                break
        if not timing:
            continue
        body = "\n".join(lines[body_at:]).strip()
        if not body:
            continue
        cues.append((clock_ms(*timing.group(1, 2, 3, 4)), clock_ms(*timing.group(5, 6, 7, 8)), body))
    if not cues:
        raise ValueError(tr("bad_cues"))
    return cues


def srt_timestamp(ms):
    hours, remainder = divmod(max(0, int(ms)), 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    seconds, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def ass_timestamp(ms):
    centiseconds = max(0, int(round(ms / 10)))
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    seconds, centiseconds = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def lrc_timestamp(ms):
    centiseconds = max(0, int(round(ms / 10)))
    minutes, remainder = divmod(centiseconds, 6_000)
    seconds, centiseconds = divmod(remainder, 100)
    return f"[{minutes:02d}:{seconds:02d}.{centiseconds:02d}]"


def ass_text(text):
    escaped = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    escaped = re.sub(r"(?i)<\s*i\s*>", r"{\\i1}", escaped)
    escaped = re.sub(r"(?i)</\s*i\s*>", r"{\\i0}", escaped)
    escaped = re.sub(r"(?i)<\s*b\s*>", r"{\\b1}", escaped)
    escaped = re.sub(r"(?i)</\s*b\s*>", r"{\\b0}", escaped)
    escaped = re.sub(r"<[^>]+>", "", escaped)
    return escaped.replace("\n", r"\N")


def xml_text(text):
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return escaped.replace("\n", "<br/>")


def convert_srt(text, fmt):
    cues = parse_srt(text)
    if fmt == "vtt":
        lines = ["WEBVTT", ""]
        for start, end, body in cues:
            lines.append(f"{srt_timestamp(start).replace(',', '.')} --> {srt_timestamp(end).replace(',', '.')}")
            lines.append(body)
            lines.append("")
        return "\n".join(lines)
    if fmt == "ass":
        events = [
            "Dialogue: 0,{},{},Default,,0,0,0,,{}".format(ass_timestamp(start), ass_timestamp(end), ass_text(body))
            for start, end, body in cues
        ]
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,56,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,0,0,0,0,100,100,0,0,1,2,1,2,40,40,48,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        return header + "\n".join(events) + "\n"
    if fmt == "ttml":
        rows = [
            f'      <p begin="{srt_timestamp(start).replace(",", ".")}" end="{srt_timestamp(end).replace(",", ".")}">{xml_text(body)}</p>'
            for start, end, body in cues
        ]
        body = "\n".join(rows)
        return (
            '<?xml version="1.0" encoding="utf-8"?>\n'
            '<tt xmlns="http://www.w3.org/ns/ttml">\n'
            "  <body>\n"
            "    <div>\n"
            f"{body}\n"
            "    </div>\n"
            "  </body>\n"
            "</tt>\n"
        )
    if fmt == "lrc":
        rows = []
        for start, _end, body in cues:
            line = re.sub(r"\s+", " ", body).strip()
            if line:
                rows.append(f"{lrc_timestamp(start)}{line}")
        if not rows:
            raise ValueError(tr("bad_cues"))
        return "\n".join(rows) + "\n"
    raise ValueError(tr("bad_fmt"))


def download_track(url, lang, destination, fmt="srt", cancel=None, subtitle_url="", referer=""):
    last_error = None
    for attempt in range(6):
        try:
            ensure_running(cancel)
            return download_track_once(url, lang, destination, fmt, cancel, attempt)
        except DownloadCancelled:
            raise
        except ValueError as error:
            last_error = error
            text = str(error)
            if text == tr("subs_missing") and subtitle_url:
                return download_subtitle_link(subtitle_url, destination, fmt, cancel, referer)
            retryable = "429" in text or "format is not available" in text.lower()
            if not retryable or attempt == 5:
                if "429" in text:
                    raise ValueError(tr("rate_limit")) from error
                raise
            pause = 20 * (attempt + 1) if "429" in text else 3
            mark_rate_limit(pause)
            sleep_cancel(pause, cancel)
    raise last_error


def download_track_once(url, lang, destination, fmt="srt", cancel=None, attempt=0):
    fmt = (fmt or "srt").lower().lstrip(".")
    if fmt not in FORMAT_BY_LABEL.values():
        fmt = "srt"
    destination = Path(destination)
    if destination.suffix.lower() != f".{fmt}":
        destination = destination.with_suffix(f".{fmt}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    wait_turn(cancel) if is_youtube(url) else None
    order = ["android", "web", "ios", "tv"]
    start = attempt % len(order)
    clients = order[start:] + order[:start]
    with tempfile.TemporaryDirectory(prefix="silans-subs-", ignore_cleanup_errors=True) as temp_dir:
        temp_root = Path(temp_dir)
        options = apply_password(base_options())
        options.update({
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": [lang],
            "subtitlesformat": "srt",
            "ignore_no_formats_error": True,
            "outtmpl": str(temp_root / "%(id)s.%(ext)s"),
            "sleep_interval_requests": 2,
            "noprogress": True,
            "progress_hooks": [lambda _data: ensure_running(cancel)],
        })
        if is_youtube(url):
            options["extractor_args"] = {"youtube": {"player_client": clients}}
        YoutubeDL, DownloadError = ytdlp_types()
        try:
            with YoutubeDL(options) as ydl:
                ydl.extract_info(normalize_url(url), download=True)
        except DownloadCancelled:
            raise
        except DownloadError as error:
            if cancel is not None and cancel.is_set():
                raise DownloadCancelled() from error
            text = str(error).strip().splitlines()
            detail = text[-1] if text else tr("subs_fail")
            raise ValueError(detail) from error
        ensure_running(cancel)
        created = sorted(temp_root.glob("*.srt"))
        vtt_files = sorted(temp_root.glob("*.vtt"))
        if not created and not vtt_files:
            raise ValueError(tr("subs_missing"))
        if created and fmt == "srt":
            shutil.copyfile(created[-1], destination)
        else:
            source = created[-1].read_text(encoding="utf-8-sig") if created else vtt_to_srt(vtt_files[-1].read_text(encoding="utf-8-sig"))
            text = source if fmt == "srt" else convert_srt(source, fmt)
            destination.write_text(text, encoding="utf-8-sig" if fmt == "ass" else "utf-8", newline="\n")
    if is_youtube(url):
        mark_rate_limit(8)
    return destination


def vtt_to_srt(text):
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    blocks = []
    for chunk in re.split(r"\n\s*\n", normalized):
        if "-->" not in chunk:
            continue
        timing = None
        body = []
        for line in chunk.split("\n"):
            if line.startswith(("WEBVTT", "NOTE", "STYLE", "Kind:", "Language:")):
                continue
            if "-->" in line and timing is None:
                left, right = line.split("-->", 1)
                left_match = re.search(r"(?:\d{2}:)?\d{2}:\d{2}[.,]\d{3}", left)
                right_match = re.search(r"(?:\d{2}:)?\d{2}:\d{2}[.,]\d{3}", right)
                if not left_match or not right_match:
                    continue

                def clock(value):
                    value = value.replace(".", ",")
                    if value.count(":") == 1:
                        value = "00:" + value
                    return value

                timing = f"{clock(left_match.group(0))} --> {clock(right_match.group(0))}"
                continue
            if line.strip().isdigit() and not body:
                continue
            if line.strip():
                body.append(line)
        if timing and body:
            blocks.append(timing + "\n" + "\n".join(body))
    if not blocks:
        raise ValueError(tr("subs_read"))
    return "\n\n".join(f"{index}\n{block}" for index, block in enumerate(blocks, start=1)) + "\n"


def subtitle_text_for_format(raw, fmt, source="srt"):
    text = raw.lstrip("\ufeff")
    if text.lstrip().startswith("WEBVTT"):
        text = vtt_to_srt(text)
        source = "srt"
    if "-->" in text:
        return text if fmt == "srt" else convert_srt(text, fmt)
    if source == fmt:
        return text
    raise ValueError(tr("subs_convert", source=source.upper(), fmt=fmt.upper()))


class DownloadCancelled(Exception):
    pass


def ensure_running(cancel):
    if cancel is not None and cancel.is_set():
        raise DownloadCancelled()


def download_subtitle_link(url, destination, fmt="srt", cancel=None, referer=""):
    ensure_running(cancel)
    fmt = (fmt or "srt").lower().lstrip(".")
    if fmt not in FORMAT_BY_LABEL.values():
        fmt = "srt"
    destination = Path(destination)
    if destination.suffix.lower() != f".{fmt}":
        destination = destination.with_suffix(f".{fmt}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = Path(url.split("?", 1)[0].split("#", 1)[0]).suffix.lower().lstrip(".") or "srt"
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        **({"Referer": referer} if referer else {}),
    })
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8-sig", errors="replace")
    except Exception as error:
        raise ValueError(tr("subs_http")) from error
    ensure_running(cancel)
    destination.write_text(
        subtitle_text_for_format(raw, fmt, source),
        encoding="utf-8-sig" if fmt == "ass" else "utf-8",
        newline="\n",
    )
    return destination


def download_media(url, item, destination, progress=None, cancel=None):
    if item.get("merged") and not ffmpeg_location():
        raise ValueError(tr("need_ffmpeg"))
    ext = (item.get("ext") or "mp4").lower()
    destination = Path(destination)
    if destination.suffix.lower() != f".{ext}":
        destination = destination.with_suffix(f".{ext}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(6):
        try:
            ensure_running(cancel)
            return download_media_once(url, item, destination, progress, cancel)
        except DownloadCancelled:
            raise
        except OSError as error:
            last_error = error
            if _file_in_use(error) and attempt < 1:
                sleep_cancel(1.5, cancel)
                continue
            if _file_in_use(error):
                raise ValueError(tr("file_busy")) from error
            raise
        except ValueError as error:
            last_error = error
            if _file_in_use(error) and attempt < 1:
                sleep_cancel(1.5, cancel)
                continue
            if _file_in_use(error):
                raise ValueError(tr("file_busy")) from error
            if "429" not in str(error) or attempt == 5:
                if "429" in str(error):
                    raise ValueError(tr("rate_limit")) from error
                raise
            pause = 20 * (attempt + 1)
            mark_rate_limit(pause)
            sleep_cancel(pause, cancel)
    raise last_error


def download_media_once(url, item, destination, progress=None, cancel=None):
    ext = (item.get("ext") or "mp4").lower()
    wait_turn(cancel) if is_youtube(url) else None
    with tempfile.TemporaryDirectory(prefix="silans-media-", ignore_cleanup_errors=True) as temp_dir:
        temp_root = Path(temp_dir)
        options = apply_password(base_options())
        options.update({
            "skip_download": False,
            "format": item["selector"],
            "outtmpl": str(temp_root / "%(id)s.%(format_id)s.%(ext)s"),
            "retries": 3,
            "fragment_retries": 3,
            "continuedl": False,
            "noprogress": True,
        })
        if item.get("type") == "video":
            options["merge_output_format"] = ext
        ffmpeg = ffmpeg_location()
        if ffmpeg:
            options["ffmpeg_location"] = ffmpeg

        def hook(data):
            ensure_running(cancel)
            if progress and data.get("status") == "downloading":
                progress(data)

        options["progress_hooks"] = [hook]
        YoutubeDL, DownloadError = ytdlp_types()
        try:
            with YoutubeDL(options) as ydl:
                ydl.extract_info(normalize_url(url), download=True)
        except DownloadCancelled:
            raise
        except DownloadError as error:
            if cancel is not None and cancel.is_set():
                raise DownloadCancelled() from error
            text = str(error).strip().splitlines()
            detail = text[-1] if text else tr("video_fail")
            raise ValueError(detail) from error
        ensure_running(cancel)
        created = [
            path for path in temp_root.rglob("*")
            if path.is_file() and path.suffix.lower() not in {".part", ".ytdl", ".json"}
        ]
        preferred = [path for path in created if path.suffix.lower() == f".{ext}"]
        if not preferred and not created:
            raise ValueError(tr("file_missing"))
        chosen = max(preferred or created, key=lambda path: path.stat().st_size)
        shutil.copyfile(chosen, destination)
    if is_youtube(url):
        mark_rate_limit(18)
    return destination


def _accent_color(blend, dim=1.0):
    if blend < 0.45:
        mix = blend / 0.45
        red, green, blue = 57, 216, 255
        target = (120, 87, 255)
    else:
        mix = (blend - 0.45) / 0.55
        red, green, blue = 120, 87, 255
        target = (214, 66, 255)
    color = (
        int(red + (target[0] - red) * mix),
        int(green + (target[1] - green) * mix),
        int(blue + (target[2] - blue) * mix),
    )
    return tuple(max(0, min(255, int(channel * dim))) for channel in color) + (255,)


def paint_button(width, height, kind):
    scale = 2
    width *= scale
    height *= scale
    radius = 14 * scale
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    hot = kind.endswith("-hot")
    down = kind.endswith("-down")
    accent = kind.startswith("accent")
    if accent:
        for x in range(width):
            image.putpixel((x, 0), _accent_color(x / max(width - 1, 1), 0.72 if down else 1.0))
        strip = image.crop((0, 0, width, 1)).resize((width, height))
        image = strip.convert("RGBA")
        mask = Image.new("L", (width, height), 0)
        ImageDraw.Draw(mask).rounded_rectangle((2, 2, width - 3, height - 3), radius=radius, fill=255)
        image.putalpha(mask)
        plate = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        if not down:
            glow = image.filter(ImageFilter.GaussianBlur(radius=7 if hot else 4))
            plate.alpha_composite(glow)
        plate.alpha_composite(image)
        image = plate
    else:
        draw = ImageDraw.Draw(image)
        outline = (57, 216, 255, 220) if hot else ((26, 77, 122, 255) if down else (57, 168, 214, 170))
        fill = (5, 10, 18, 255) if down else (8, 17, 31, 255)
        box = (3, 3, width - 4, height - 4)
        if hot:
            haze = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            ImageDraw.Draw(haze).rounded_rectangle(box, radius=radius, outline=(57, 216, 255, 90), width=scale * 4)
            image.alpha_composite(haze.filter(ImageFilter.GaussianBlur(radius=2)))
            draw = ImageDraw.Draw(image)
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=max(2, scale))
        draw.rounded_rectangle(
            (7, 7, width - 8, height - 8),
            radius=max(4, radius - 8),
            outline=(8, 17, 31, 255),
            width=scale,
        )
        if not down:
            draw.line((radius, 5, width - radius, 5), fill=(57, 216, 255, 180 if hot else 90), width=max(1, scale // 2))
            draw.line((radius, height - 6, width - radius, height - 6), fill=(214, 66, 255, 110 if hot else 55), width=max(1, scale // 2))
    flat = Image.new("RGB", (width, height), BG_RGB)
    flat.paste(image, mask=image.getchannel("A"))
    return flat.resize((width // scale, height // scale), Image.Resampling.LANCZOS)


class CosmicBackground:
    """Static space pictures, with only a few slow star dots moving."""

    TARGET_FPS = 20
    FRAME_MS = 50
    STAR_COUNT = 40
    RESIZE_PAUSE = 0.20

    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, bg=BG, highlightthickness=0, bd=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._job = None
        self._resize_job = None
        self._last = None
        self._clock = 0.0
        self._paused_until = 0.0
        self._home_x = 0.0
        self._home_y = 0.0
        self._ox = 0.0
        self._oy = 0.0
        self._hole_radius = 40.0
        self._width = 0
        self._height = 0
        self._field_source = self._open_image("stars.png")
        self._hole_source = self._open_image("blackhole.png")
        self._field_photo = None
        self._hole_photo = None
        self._logo_photo = None
        self._field_item = self.canvas.create_image(0, 0, anchor="center")
        self._stars = []
        self._create_stars()
        self._hole_item = self.canvas.create_image(0, 0, anchor="center")
        root.bind("<Configure>", self._on_resize, add="+")
        if COSMIC_ANIMATION:
            self._animate()
        else:
            self._layout_static()

    def stop(self):
        for attr in ("_job", "_resize_job"):
            job = getattr(self, attr, None)
            if job is not None:
                try:
                    self.root.after_cancel(job)
                except tk.TclError:
                    pass
                setattr(self, attr, None)

    def _open_image(self, name):
        path = ASSETS / name
        if not path.exists():
            return None
        return Image.open(path).convert("RGBA")

    def _origin(self, width, height):
        return width * 0.53, height * 0.15

    def _layout_static(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 40 or height < 40:
            return
        self._width = width
        self._height = height
        self._home_x, self._home_y = self._origin(width, height)
        self._ox, self._oy = self._home_x, self._home_y
        if self._field_source is not None:
            field = self._field_source.resize((width, height), Image.Resampling.BILINEAR)
            self._field_photo = ImageTk.PhotoImage(field)
            self.canvas.itemconfig(self._field_item, image=self._field_photo)
            self.canvas.coords(self._field_item, width / 2, height / 2)
        hole_width = max(160, min(220, int(width * 190 / 1400)))
        source = self._hole_source
        if source is None:
            plate = Image.new("RGBA", (hole_width, hole_width), (0, 0, 0, 0))
        else:
            hole_height = max(1, int(source.height * hole_width / source.width))
            plate = source.resize((hole_width, hole_height), Image.Resampling.BILINEAR)
        self._hole_radius = hole_width * 0.34
        self._hole_photo = ImageTk.PhotoImage(plate)
        self.canvas.itemconfig(self._hole_item, image=self._hole_photo)
        self.canvas.coords(self._hole_item, self._ox, self._oy)
        self.canvas.tag_raise(self._hole_item)
        self._place_logo()
        if not any(star.get("placed") for star in self._stars):
            for star in self._stars:
                self._scatter(star)
                star["placed"] = True

    def _place_logo(self):
        if self._logo_photo is not None:
            self.canvas.tag_raise(self._logo_item)
            return
        source = self._open_image("logo.png")
        if source is None:
            return
        height = 128
        width = max(1, round(source.width * height / source.height))
        image = source.resize((width, height), Image.Resampling.LANCZOS)
        self._logo_photo = ImageTk.PhotoImage(image)
        self._logo_item = self.canvas.create_image(32, 22, image=self._logo_photo, anchor="nw")

    def _create_stars(self):
        layers = (
            (16, (2.0, 4.0), (140, 160, 220), 1),
            (16, (4.0, 7.0), (190, 170, 245), 1),
            (8, (7.0, 11.0), (235, 245, 255), 2),
        )
        for count, speeds, color, size in layers:
            for _ in range(count):
                item = self.canvas.create_rectangle(0, 0, size, size, outline="", fill="#c4b5fd")
                self._stars.append({
                    "item": item,
                    "x": 0.0,
                    "y": 0.0,
                    "velocity_x": 0.0,
                    "velocity_y": 0.0,
                    "size": size,
                    "brightness": random.uniform(0.75, 1.0),
                    "depth": random.uniform(*speeds),
                    "color": color,
                    "phase": random.random() * math.tau,
                    "twinkle_speed": random.uniform(0.35, 0.9),
                    "shade": None,
                    "placed": False,
                })

    def _scatter(self, star):
        angle = random.random() * math.tau
        reach = math.hypot(self._width, self._height) * 0.55
        distance = random.uniform(self._hole_radius * 0.8, max(reach, 80))
        star["x"] = self._ox + math.cos(angle) * distance
        star["y"] = self._oy + math.sin(angle) * distance
        star["velocity_x"] = 0.0
        star["velocity_y"] = 0.0

    def _reset_star(self, star):
        angle = random.random() * math.tau
        distance = random.uniform(2.0, max(6.0, self._hole_radius * 0.55))
        star["x"] = self._ox + math.cos(angle) * distance
        star["y"] = self._oy + math.sin(angle) * distance
        star["velocity_x"] = 0.0
        star["velocity_y"] = 0.0

    def _shade(self, star, amount):
        red, green, blue = star["color"]
        return "#{:02x}{:02x}{:02x}".format(
            int(red * amount),
            int(green * amount),
            int(blue * amount),
        )

    def _foreground(self):
        try:
            import ctypes
            user32 = ctypes.windll.user32
            fg = user32.GetForegroundWindow()
            ours = int(self.root.winfo_id())
            parent = user32.GetParent(ours)
            return fg in (ours, parent)
        except Exception:
            return True

    def _step(self, dt):
        if self._width < 40:
            self._layout_static()
            return
        self._clock += dt
        self._ox, self._oy = self._home_x, self._home_y
        ox, oy = self._ox, self._oy
        width, height = self._width, self._height
        for star in self._stars:
            dx = star["x"] - ox
            dy = star["y"] - oy
            distance = math.hypot(dx, dy)
            if distance < 1.0:
                angle = random.random() * math.tau
                direction_x = math.cos(angle)
                direction_y = math.sin(angle)
            else:
                direction_x = dx / distance
                direction_y = dy / distance
            speed = star["depth"]
            star["velocity_x"] = direction_x * speed
            star["velocity_y"] = direction_y * speed
            star["x"] += star["velocity_x"] * dt
            star["y"] += star["velocity_y"] * dt
            if star["x"] < -8 or star["y"] < -8 or star["x"] > width + 8 or star["y"] > height + 8:
                self._reset_star(star)
            glow = star["brightness"] * (0.95 + 0.05 * math.sin(self._clock * star["twinkle_speed"] + star["phase"]))
            size = star["size"]
            left = int(star["x"])
            top = int(star["y"])
            self.canvas.coords(star["item"], left, top, left + size, top + size)
            shade = self._shade(star, round(glow * 20) / 20)
            if shade != star["shade"]:
                star["shade"] = shade
                self.canvas.itemconfig(star["item"], fill=shade)

    def _animate(self):
        self._job = None
        try:
            alive = self.root.winfo_exists()
        except tk.TclError:
            return
        if not alive or not COSMIC_ANIMATION:
            return
        if not self.root.winfo_viewable():
            self._last = None
            self._job = self.root.after(1000, self._animate)
            return
        now = time.perf_counter()
        if now < self._paused_until:
            self._job = self.root.after(self.FRAME_MS, self._animate)
            return
        dt = 0.05 if self._last is None else min(0.1, now - self._last)
        self._last = now
        self._step(dt)
        interval = self.FRAME_MS if self._foreground() else 150
        self._job = self.root.after(interval, self._animate)

    def _on_resize(self, _event=None):
        if _event is not None and _event.widget is not self.root:
            return
        self._paused_until = time.perf_counter() + self.RESIZE_PAUSE
        if self._resize_job is not None:
            try:
                self.root.after_cancel(self._resize_job)
            except tk.TclError:
                pass
        self._resize_job = self.root.after(200, self._apply_resize)

    def _apply_resize(self):
        self._resize_job = None
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width == self._width and height == self._height and self._hole_photo is not None and self._field_photo is not None:
            return
        self._layout_static()


class App(TkinterDnD.Tk if TkinterDnD else tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Silans Subtitles")
        self.geometry("1360x900")
        self.minsize(1180, 760)
        self.configure(bg=BG)
        self.video_rows = []
        self.sub_rows = []
        self.jobs = []
        self.job_seq = 0
        self.lang_mode = "ru"
        self.status_key = "hint"
        self.status_args = {}
        self.busy = False
        self.search_gen = 0
        self.loaded_url = ""
        self.cosmos = None
        self._sky_mask_job = None
        self.images = []
        self.folder_chosen = False
        self.install_id = uuid.uuid4().hex[:12]
        self._subtitle_label = "SRT"
        self._video_label = "MP4"
        downloads = Path.home() / "Downloads"
        self.save_dir = downloads if downloads.is_dir() else Path.home()
        self._load_settings()
        self._apply_icon()
        self._style()
        self._build()
        self._enable_drop()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(50, self._dark_titlebar)
        self.after(100, lambda: threading.Thread(target=ytdlp_types, daemon=True).start())
        self.after(400, lambda: self._report("launch", lang=self.lang_mode))

    def _settings_path(self):
        return app_dir() / "settings.json"

    def _load_settings(self):
        global UI_LANG
        try:
            data = json.loads(self._settings_path().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        if data.get("lang") in {"ru", "eng"}:
            self.lang_mode = data["lang"]
            UI_LANG = data["lang"]
        folder = data.get("folder") or ""
        if folder and Path(folder).is_dir():
            self.save_dir = Path(folder)
            self.folder_chosen = True
        if data.get("subtitle_format") in FORMAT_BY_LABEL:
            self._subtitle_label = data["subtitle_format"]
        if data.get("video_format") in VIDEO_FORMAT_BY_LABEL:
            self._video_label = data["video_format"]
        if data.get("install_id"):
            self.install_id = str(data["install_id"])[:24]
        else:
            self._save_settings()

    def _save_settings(self):
        data = {
            "lang": self.lang_mode,
            "folder": str(self.save_dir),
            "subtitle_format": self.format_var.get() if hasattr(self, "format_var") else self._subtitle_label,
            "video_format": self.video_format_var.get() if hasattr(self, "video_format_var") else self._video_label,
            "install_id": self.install_id,
        }
        try:
            self._settings_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _on_close(self):
        if self.cosmos is not None:
            self.cosmos.stop()
        job = getattr(self, "_sky_mask_job", None)
        if job:
            self.after_cancel(job)
            self._sky_mask_job = None
        self._save_settings()
        self.destroy()

    def _report(self, kind, **fields):
        lines = [f"id: {self.install_id}"]
        meta = {"id": self.install_id}
        for key, value in fields.items():
            if value:
                lines.append(f"{key}: {value}")
                meta[key] = value
        report_async(kind, lines, meta)

    def _enable_drop(self):
        if TkinterDnD is None:
            return
        try:
            self.drop_target_register(DND_TEXT, DND_FILES)
            self.dnd_bind("<<Drop>>", self._on_drop)
        except tk.TclError:
            return

    def _on_drop(self, event):
        raw = str(getattr(event, "data", "") or "").strip()
        if not raw:
            return
        try:
            parts = [item for item in self.tk.splitlist(raw) if str(item).strip()]
        except tk.TclError:
            parts = [raw]
        text = str(parts[0]).strip().strip("{}")
        path = Path(text)
        if path.suffix.lower() == ".url" and path.is_file():
            try:
                for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if line.lower().startswith("url="):
                        text = line.split("=", 1)[1].strip()
                        break
            except OSError:
                return
        if not text.lower().startswith(("http://", "https://")):
            return
        self.url.set(text)
        self.search()

    def choose_folder(self):
        chosen = filedialog.askdirectory(
            parent=self,
            title=tr("pick_folder"),
            initialdir=str(self.save_dir if self.save_dir.is_dir() else Path.home()),
        )
        if not chosen:
            return False
        self.save_dir = Path(chosen)
        self.folder_chosen = True
        self._save_settings()
        self.say("folder_set", name=self.save_dir.name)
        return True

    def _apply_icon(self):
        icon_png = ASSETS / "icon.png"
        icon_ico = ASSETS / "icon.ico"
        try:
            if icon_ico.exists():
                self.iconbitmap(str(icon_ico))
            if icon_png.exists():
                image = ImageTk.PhotoImage(Image.open(icon_png).resize((64, 64), Image.Resampling.LANCZOS))
                self.images.append(image)
                self.iconphoto(True, image)
        except tk.TclError:
            pass

    def _dark_titlebar(self):
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            value = ctypes.c_int(1)
            for attribute in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value)
                )
        except Exception:
            pass

    def _style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Neon.Treeview",
            background="#07101d",
            fieldbackground="#07101d",
            foreground="#e7f2ff",
            borderwidth=0,
            relief="flat",
            rowheight=34,
            font=("Segoe UI", 11),
        )
        style.map(
            "Neon.Treeview",
            background=[("selected", "#1d4ed8"), ("!selected", "#07101d")],
            foreground=[("selected", "#ffffff"), ("!selected", "#e7f2ff")],
        )
        style.layout("Neon.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        style.configure(
            "Neon.Vertical.TScrollbar",
            gripcount=0,
            background="#1A4D7A",
            darkcolor="#08111F",
            lightcolor="#39D8FF",
            troughcolor="#070b16",
            bordercolor="#08111F",
            arrowcolor="#1A4D7A",
        )
    def _button(self, parent, text, kind, command, width):
        normal = ImageTk.PhotoImage(paint_button(width, 46, kind))
        hover = ImageTk.PhotoImage(paint_button(width, 46, f"{kind}-hot"))
        pressed = ImageTk.PhotoImage(paint_button(width, 46, f"{kind}-down"))
        self.images.extend((normal, hover, pressed))
        button = tk.Button(
            parent,
            text=text,
            command=command,
            image=normal,
            compound="center",
            fg="#f8fbff",
            disabledforeground="#8ea0b8",
            font=("Segoe UI", 11, "bold"),
            bd=0,
            bg=BG,
            activebackground=BG,
            activeforeground="#ffffff",
            highlightthickness=0,
            cursor="hand2",
        )
        button._normal = normal
        button._hover = hover
        button._pressed = pressed

        def on_enter(_event):
            if str(button["state"]) == "normal":
                button.configure(image=button._hover)

        def on_leave(_event):
            button.configure(image=button._normal)

        def on_press(_event):
            if str(button["state"]) == "normal":
                button.configure(image=button._pressed)

        def on_release(_event):
            pointer_x, pointer_y = button.winfo_pointerxy()
            inside = (
                button.winfo_rootx() <= pointer_x < button.winfo_rootx() + button.winfo_width()
                and button.winfo_rooty() <= pointer_y < button.winfo_rooty() + button.winfo_height()
            )
            button.configure(image=button._hover if inside else button._normal)

        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        button.bind("<ButtonPress-1>", on_press)
        button.bind("<ButtonRelease-1>", on_release)
        return button

    def _pick_format(self, label):
        self.format_var.set(label)
        self.format_button.configure(text=f"{label}  ▾")
        self._close_popups()
        self._save_settings()

    def _pick_video_format(self, label):
        self.video_format_var.set(label)
        self.video_format_button.configure(text=f"{label}  ▾")
        self._close_popups()
        self._save_settings()

    def _close_popups(self):
        for attr in ("_format_popup", "_video_format_popup"):
            popup = getattr(self, attr, None)
            if popup is not None and popup.winfo_exists():
                popup.destroy()
            setattr(self, attr, None)

    def _maybe_close_format_popup(self, event):
        widget = str(event.widget)
        for attr, button in (
            ("_format_popup", getattr(self, "format_button", None)),
            ("_video_format_popup", getattr(self, "video_format_button", None)),
        ):
            popup = getattr(self, attr, None)
            if popup is None or not popup.winfo_exists():
                continue
            if event.widget is button or widget.startswith(str(popup)):
                continue
            popup.destroy()
            setattr(self, attr, None)

    def _show_choice(self, attr, button, options, on_pick):
        popup = getattr(self, attr, None)
        if popup is not None and popup.winfo_exists():
            popup.destroy()
            setattr(self, attr, None)
            return
        self._close_popups()
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg="#1d4ed8")
        popup.attributes("-topmost", True)
        inner = tk.Frame(popup, bg="#07111f")
        inner.pack(padx=1, pady=1)
        for _ext, label in options:
            tk.Button(
                inner,
                text=label,
                command=lambda name=label: on_pick(name),
                bg="#07111f",
                fg="#e7f3ff",
                activebackground="#1d4ed8",
                activeforeground="#ffffff",
                relief="flat",
                font=("Segoe UI", 11, "bold"),
                width=10,
                bd=0,
                cursor="hand2",
                padx=8,
                pady=6,
            ).pack(fill="x")
        popup.update_idletasks()
        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height() + 4
        popup.geometry(f"+{x}+{y}")
        setattr(self, attr, popup)

    def _show_formats(self):
        self._show_choice("_format_popup", self.format_button, SUBTITLE_FORMATS, self._pick_format)

    def _show_video_formats(self):
        self._show_choice("_video_format_popup", self.video_format_button, VIDEO_FORMATS, self._pick_video_format)

    def _poke_sky(self, _event=None):
        job = getattr(self, "_sky_mask_job", None)
        if job:
            self.after_cancel(job)
        self._sky_mask_job = self.after(200, self._sync_sky_mask)

    def _sky_keep(self, widget):
        kind = widget.winfo_class()
        if kind == "Frame":
            try:
                return str(widget.cget("bg")).lower() != BG
            except tk.TclError:
                return True
        return kind in {
            "Label", "Button", "Entry", "Canvas", "Treeview",
            "TScrollbar", "Scrollbar", "TButton",
        }

    def _sky_rects(self, widget, origin, rects):
        if not widget.winfo_exists() or not widget.winfo_ismapped():
            return
        if self._sky_keep(widget):
            width = widget.winfo_width()
            height = widget.winfo_height()
            if width > 1 and height > 1:
                radius = 16 if widget.winfo_class() == "Button" else 0
                rects.append((
                    widget.winfo_rootx() - origin[0],
                    widget.winfo_rooty() - origin[1],
                    width,
                    height,
                    radius,
                ))
            return
        for child in widget.winfo_children():
            self._sky_rects(child, origin, rects)

    def _sync_sky_mask(self):
        self._sky_mask_job = None
        import ctypes
        frame = getattr(self, "_sky_frame", None)
        if frame is None or not frame.winfo_exists() or frame.winfo_width() < 80:
            return
        size = (frame.winfo_width(), frame.winfo_height())
        if size == getattr(self, "_mask_size", None):
            return
        self._mask_size = size
        origin = (frame.winfo_rootx(), frame.winfo_rooty())
        rects = []
        for child in frame.winfo_children():
            self._sky_rects(child, origin, rects)
        width = frame.winfo_width()
        height = frame.winfo_height()
        rects.extend((
            (0, 0, width, 2, 0),
            (0, height - 2, width, 2, 0),
            (0, 0, 2, height, 0),
            (width - 2, 0, 2, height, 0),
        ))
        gdi32 = ctypes.windll.gdi32
        user32 = ctypes.windll.user32
        if not getattr(self, "_sky_gdi", False):
            gdi32.CreateRectRgn.restype = ctypes.c_void_p
            gdi32.CreateRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            gdi32.CreateRoundRectRgn.restype = ctypes.c_void_p
            gdi32.CreateRoundRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            gdi32.CombineRgn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
            gdi32.SetRectRgn.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
            gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
            user32.SetWindowRgn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_bool]
            self._sky_gdi = True
        region = gdi32.CreateRectRgn(0, 0, 0, 0)
        piece = gdi32.CreateRectRgn(0, 0, 0, 0)
        for x, y, rect_width, rect_height, radius in rects:
            left, top = int(x), int(y)
            right, bottom = int(x + rect_width), int(y + rect_height)
            if radius:
                curve = min(radius * 2, rect_height, rect_width)
                shaped = gdi32.CreateRoundRectRgn(left, top, right + 1, bottom + 1, curve, curve)
                gdi32.CombineRgn(region, region, shaped, 2)
                gdi32.DeleteObject(shaped)
            else:
                gdi32.SetRectRgn(piece, left, top, right, bottom)
                gdi32.CombineRgn(region, region, piece, 2)
        gdi32.DeleteObject(piece)
        user32.SetWindowRgn(frame.winfo_id(), region, True)

    def _build(self):
        self.cosmos = CosmicBackground(self)
        self.sky = self.cosmos.canvas
        frame = tk.Frame(self, bg=BG, highlightbackground="#1A4D7A", highlightthickness=1)
        frame.place(x=12, y=12, relwidth=1, relheight=1, width=-24, height=-24)
        self._sky_frame = frame
        frame.lift()
        frame.bind("<Configure>", self._poke_sky)
        self.after(60, self._poke_sky)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(3, weight=1)
        frame.rowconfigure(6, weight=0)

        logo_path = ASSETS / "logo.png"
        logo_height = 128
        logo_width = 192
        if logo_path.exists():
            with Image.open(logo_path) as logo_image:
                logo_width = max(1, round(logo_image.width * logo_height / logo_image.height))
        spacer = tk.Frame(frame, bg=BG, width=logo_width, height=logo_height)
        spacer.grid(row=0, column=0, sticky="nw", padx=(18, 0), pady=(8, 12))
        spacer.grid_propagate(False)

        url_row = tk.Frame(frame, bg=BG)
        url_row.grid(row=1, column=0, sticky="ew", padx=18, pady=(8, 4))
        url_row.columnconfigure(0, weight=1)
        self.url = tk.StringVar()
        entry = tk.Entry(
            url_row,
            textvariable=self.url,
            font=("Segoe UI", 12),
            bg="#08111F",
            fg="#e7f3ff",
            insertbackground="#39D8FF",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#1A4D7A",
            highlightcolor="#39D8FF",
        )
        entry.grid(row=0, column=0, sticky="ew", ipady=8, padx=(8, 0))
        entry.bind("<Return>", lambda _event: self.search())
        entry.bind("<Control-KeyPress>", self._paste_shortcut)
        self.url_entry = entry
        self.paste_button = self._button(url_row, tr("paste"), "glass", self.paste, 128)
        self.paste_button.grid(row=0, column=1, padx=(10, 0))
        self.search_button = self._button(url_row, tr("search"), "accent", self.search, 148)
        self.search_button.grid(row=0, column=2, padx=(10, 8))

        title_row = tk.Frame(frame, bg=BG)
        title_row.grid(row=2, column=0, sticky="ew", padx=22, pady=(16, 8))
        tk.Frame(title_row, bg="#38bdf8", width=4, height=18).pack(side="left", padx=(0, 10))
        self.video_title = tk.StringVar(value=tr("placeholder"))
        tk.Label(
            title_row,
            textvariable=self.video_title,
            bg=BG,
            fg="#f4f8ff",
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        ).pack(side="left")

        panes = tk.Frame(frame, bg=BG)
        panes.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 4))
        panes.columnconfigure(0, weight=1)
        panes.columnconfigure(1, weight=1)
        panes.rowconfigure(1, weight=1)
        self.video_tree = self._add_list(panes, 0, tr("video"), self.download_video)
        self.sub_tree = self._add_list(panes, 1, tr("subs"), self.download_subs)
        video_actions = tk.Frame(panes, bg=BG)
        video_actions.grid(row=2, column=0, sticky="ew", padx=(0, 12), pady=(8, 0))
        self.video_format_var = tk.StringVar(value=self._video_label)
        self.video_format_button = self._button(video_actions, f"{self._video_label}  ▾", "glass", self._show_video_formats, 118)
        self.video_format_button.pack(side="left")
        self.video_button = self._button(video_actions, tr("download"), "accent", self.download_video, 160)
        self.video_button.pack(side="left", padx=(10, 0))
        sub_actions = tk.Frame(panes, bg=BG)
        sub_actions.grid(row=2, column=1, sticky="ew", padx=(12, 0), pady=(8, 0))
        self.format_var = tk.StringVar(value=self._subtitle_label)
        self.format_button = self._button(sub_actions, f"{self._subtitle_label}  ▾", "glass", self._show_formats, 118)
        self.format_button.pack(side="left")
        self.subs_button = self._button(sub_actions, tr("download"), "accent", self.download_subs, 160)
        self.subs_button.pack(side="left", padx=(10, 0))
        self.bind_all("<Button-1>", self._maybe_close_format_popup, add="+")

        actions = tk.Frame(frame, bg=BG)
        actions.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 2))
        self.folder_button = self._button(actions, tr("folder"), "glass", self.open_folder, 180)
        self.folder_button.pack(side="left")
        self.pick_folder_button = self._button(actions, tr("pick_folder"), "glass", self.choose_folder, 190)
        self.pick_folder_button.pack(side="left", padx=(10, 0))

        bottom = tk.Frame(frame, bg=BG)
        bottom.grid(row=5, column=0, sticky="ew", padx=12, pady=(4, 6))
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=0)
        queue_col = tk.Frame(bottom, bg=BG)
        queue_col.grid(row=0, column=0, sticky="ew")
        queue_col.columnconfigure(0, weight=1)
        queue_head = tk.Frame(queue_col, bg=BG)
        queue_head.grid(row=0, column=0, sticky="ew")
        self.queue_heading = tk.Label(
            queue_head,
            text=tr("queue"),
            bg=BG,
            fg="#93c5fd",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.queue_heading.pack(side="left")
        self.status = tk.StringVar(value=tr("hint"))
        self.status_label = tk.Label(
            queue_head,
            textvariable=self.status,
            bg=BG,
            fg="#93c5fd",
            font=("Segoe UI", 9),
            anchor="e",
        )
        self.status_label.pack(side="right")
        shell = tk.Frame(queue_col, bg="#07101d", highlightbackground="#1A4D7A", highlightthickness=1)
        shell.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(0, weight=1)
        self.queue_canvas = tk.Canvas(shell, bg="#07101d", highlightthickness=0, height=36, bd=0)
        self.queue_scroll = ttk.Scrollbar(shell, orient="vertical", command=self.queue_canvas.yview, style="Neon.Vertical.TScrollbar")
        self.queue_canvas.configure(yscrollcommand=self.queue_scroll.set)
        self.queue_canvas.grid(row=0, column=0, sticky="ew")
        self.queue_box = tk.Frame(self.queue_canvas, bg="#07101d")
        self.queue_window = self.queue_canvas.create_window((0, 0), window=self.queue_box, anchor="nw")
        self.queue_canvas.bind("<Configure>", self._queue_resized)
        self.queue_empty = tk.Label(
            self.queue_box,
            text=tr("empty"),
            bg="#07101d",
            fg="#7dd3fc",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )
        self.queue_empty.pack(fill="x", padx=8, pady=2)
        self._bind_queue_wheel(self.queue_canvas)
        self._bind_queue_wheel(self.queue_box)
        self._bind_queue_wheel(self.queue_empty)
        voice_path = ASSETS / "voice.png"
        if voice_path.exists():
            voice_image = Image.open(voice_path).convert("RGBA")
            bar_height = 58
            scaled_width = max(1, round(voice_image.width * bar_height / voice_image.height))
            voice_image = voice_image.resize((scaled_width, bar_height), Image.Resampling.LANCZOS)
            voice = ImageTk.PhotoImage(voice_image)
            self.images.append(voice)
            voice_link = tk.Label(bottom, image=voice, bg=BG, cursor="hand2")
            voice_link.grid(row=0, column=1, sticky="se", padx=(16, 0))
            voice_link.bind("<Button-1>", lambda _event: webbrowser.open(CHANNEL_URL))
        self._place_lang_button(frame)
        self.after(80, self._fit_queue)

    def _panel_edge(self, host):
        edge = tk.Canvas(host, bg="#07101d", highlightthickness=0, bd=0)
        edge.place(x=0, y=0, relwidth=1, relheight=1)

        def draw(_event=None):
            width = host.winfo_width()
            height = host.winfo_height()
            if width < 12 or height < 12:
                return
            edge.delete("line")
            edge.create_rectangle(1, 1, width - 2, height - 2, outline="#08111F", width=2, tags="line")
            edge.create_rectangle(2, 2, width - 3, height - 3, outline="#1A4D7A", width=1, tags="line")
            edge.create_line(12, 2, width - 12, 2, fill="#39D8FF", tags="line")
            edge.create_line(2, 12, 2, height - 12, fill="#39D8FF", tags="line")
            edge.create_line(width - 3, 12, width - 3, height - 12, fill="#7857FF", tags="line")
            edge.create_line(12, height - 3, width - 12, height - 3, fill="#D642FF", tags="line")
            for left, top, color in (
                (2, 2, "#39D8FF"),
                (width - 5, 2, "#7857FF"),
                (2, height - 5, "#39D8FF"),
                (width - 5, height - 5, "#D642FF"),
            ):
                edge.create_rectangle(left, top, left + 2, top + 2, outline=color, fill=color, width=0, tags="line")

        host.bind("<Configure>", draw, add="+")
        tk.Misc.lower(edge)

    def _add_list(self, parent, column, title, command):
        head = tk.Frame(parent, bg=BG)
        gap = (0, 12) if column == 0 else (12, 0)
        head.grid(row=0, column=column, sticky="ew", padx=gap, pady=(0, 6))
        label = tk.Label(
            head,
            text=title,
            bg=BG,
            fg="#f4f8ff",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        label.pack(side="left")
        if column == 0:
            self.video_heading = label
        else:
            self.sub_heading = label
        wrap = tk.Frame(parent, bg="#07101d", highlightthickness=0)
        wrap.grid(row=1, column=column, sticky="nsew", padx=gap)
        self._panel_edge(wrap)
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        tree = ttk.Treeview(
            wrap,
            columns=("code", "name", "kind"),
            show="",
            style="Neon.Treeview",
            selectmode="browse",
        )
        tree.column("code", width=90, minwidth=70, stretch=False, anchor="w")
        tree.column("name", width=140, minwidth=80, stretch=True, anchor="w")
        tree.column("kind", width=180, minwidth=110, stretch=True, anchor="w")
        tree.heading("code", text="")
        tree.heading("name", text="")
        tree.heading("kind", text="")
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=tree.yview, style="Neon.Vertical.TScrollbar")
        tree.configure(yscrollcommand=scroll.set)
        tree.grid(row=0, column=0, sticky="nsew", padx=(8, 0), pady=8)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 6), pady=8)
        tree.bind("<Double-1>", lambda _event: command())
        tree.tag_configure("picked", background="#1d4ed8", foreground="#ffffff")
        return tree

    def _place_lang_button(self, parent):
        normal = ImageTk.PhotoImage(paint_button(78, 32, "glass"))
        hover = ImageTk.PhotoImage(paint_button(78, 32, "glass-hot"))
        self.images.extend((normal, hover))
        self.lang_button = tk.Button(
            parent,
            text="ENG" if self.lang_mode == "eng" else "RU",
            command=self.toggle_lang,
            image=normal,
            compound="center",
            fg="#f8fbff",
            font=("Segoe UI", 10, "bold"),
            bd=0,
            bg=BG,
            activebackground=BG,
            activeforeground="#ffffff",
            highlightthickness=0,
            cursor="hand2",
        )
        self.lang_button._normal = normal
        self.lang_button._hover = hover
        self.lang_button.bind("<Enter>", lambda _event: self.lang_button.configure(image=self.lang_button._hover))
        self.lang_button.bind("<Leave>", lambda _event: self.lang_button.configure(image=self.lang_button._normal))
        self.lang_button.place(relx=1, x=-16, y=12, anchor="ne")

    def toggle_lang(self):
        global UI_LANG
        self.lang_mode = "eng" if self.lang_mode == "ru" else "ru"
        UI_LANG = self.lang_mode
        self.lang_button.configure(text="ENG" if self.lang_mode == "eng" else "RU")
        self.apply_language()
        if self.sub_rows and not self.select_subtitle():
            self.say("no_track", "#fda4af")
        self._save_settings()

    def apply_language(self):
        self.paste_button.configure(text=tr("paste"))
        self.search_button.configure(text=tr("search"))
        self.video_button.configure(text=tr("download"))
        self.subs_button.configure(text=tr("download"))
        self.folder_button.configure(text=tr("folder"))
        self.pick_folder_button.configure(text=tr("pick_folder"))
        self.video_heading.configure(text=tr("video"))
        self.sub_heading.configure(text=tr("subs"))
        self.queue_heading.configure(text=tr("queue"))
        self.queue_empty.configure(text=tr("empty"))
        titles = {UI["ru"]["placeholder"], UI["eng"]["placeholder"]}
        files = {UI["ru"]["subtitle_file"], UI["eng"]["subtitle_file"]}
        current = self.video_title.get()
        if current in titles:
            self.video_title.set(tr("placeholder"))
        elif current in files:
            self.video_title.set(tr("subtitle_file"))
        video_sel = self.video_tree.selection()
        self._fill_tree(
            self.video_tree,
            self.video_rows,
            keep=video_sel[0] if video_sel else None,
            preferred_type=None if video_sel else "video",
        )
        self._fill_tree(self.sub_tree, self.sub_rows)
        for job in self.jobs:
            self._refresh_job(job)
        if self.status_key:
            self.status.set(tr(self.status_key, **self.status_args))
        self._poke_sky()

    def say(self, key, color="#93c5fd", **kwargs):
        self.status_key = key
        self.status_args = kwargs
        self.status_label.configure(fg=color)
        self.status.set(tr(key, **kwargs))

    def _row_cells(self, row):
        code = tr("audio_code") if row.get("type") == "audio" else row["code"]
        name = tr(row["name_key"]) if row.get("name_key") else row["name"]
        if row.get("type") == "video":
            size = human_size(row.get("bytes") or 0)
            detail = f"{size} · {tr('av')}" if size else tr("av")
        elif row.get("type") == "audio":
            size = human_size(row.get("bytes") or 0)
            detail = f"{size} · {tr('audio_only')}" if size else tr("audio_only")
        elif row.get("type") == "subs":
            detail = kind_label(row.get("kind") or "auto")
        elif row.get("detail_key"):
            detail = tr(row["detail_key"])
        else:
            detail = row.get("detail") or ""
        return code, name, f"·   {detail}"

    def _subtitle_rank(self, row):
        code = str(row.get("lang") or row.get("code") or "").strip().lower()
        name = str(row.get("name") or "").lower()
        prefix = code.split("-", 1)[0].split("_", 1)[0]
        if self.lang_mode == "eng":
            english = prefix == "en" or "english" in name or "англий" in name
            if not english:
                return None
            if "orig" in code:
                return 0
            if code == "en":
                return 1
            return 2
        russian = prefix == "ru" or "russian" in name or "русск" in name
        if not russian:
            return None
        if code in {"ru", "rus"}:
            return 0
        return 1

    def select_subtitle(self):
        ranked = []
        for index, row in enumerate(self.sub_rows):
            rank = self._subtitle_rank(row)
            if rank is not None:
                ranked.append((rank, index))
        if not ranked:
            return False
        index = min(ranked)[1]
        iid = str(index)
        for item in self.sub_tree.get_children():
            self.sub_tree.item(item, tags=())
        self.sub_tree.item(iid, tags=("picked",))
        self.sub_tree.selection_set(iid)
        self.sub_tree.focus(iid)
        self.sub_tree.see(iid)
        row = self.sub_rows[index]
        self.say("picked", code=row["code"], name=row["name"])
        return True

    def paste(self):
        text = self._clipboard_text()
        if text:
            self.url.set(text)

    def _clipboard_text(self):
        try:
            return self.clipboard_get().strip()
        except tk.TclError:
            return ""

    def _paste_shortcut(self, event):
        # Коды клавиш не зависят от раскладки: на русской Ctrl+A тоже выделяет всё поле.
        widget = event.widget
        if event.keycode == 65:
            widget.select_range(0, "end")
            widget.icursor("end")
            return "break"
        if event.keycode == 67:
            try:
                if widget.selection_present():
                    self.clipboard_clear()
                    self.clipboard_append(widget.selection_get())
            except tk.TclError:
                pass
            return "break"
        if event.keycode == 88:
            try:
                if widget.selection_present():
                    self.clipboard_clear()
                    self.clipboard_append(widget.selection_get())
                    widget.delete("sel.first", "sel.last")
            except tk.TclError:
                pass
            return "break"
        if event.keycode != 86:
            return None
        text = self._clipboard_text()
        if not text:
            return "break"
        try:
            widget.delete("sel.first", "sel.last")
        except tk.TclError:
            pass
        widget.insert("insert", text)
        return "break"

    def set_busy(self, busy, status=None, key=None, **kwargs):
        self.busy = busy
        state = "disabled" if busy else "normal"
        for button in (self.paste_button, self.search_button):
            button.configure(state=state)
        if key:
            self.say(key, **kwargs)
        elif status is not None:
            self.status_key = None
            self.status_args = {}
            self.status.set(status)
            self.status_label.configure(fg="#93c5fd")

    def selected_from(self, tree, rows):
        selection = tree.selection()
        if not selection:
            return None
        return rows[int(selection[0])]

    def _reject_search(self, text):
        self.set_busy(False, text)
        self.status_label.configure(fg="#fda4af")

    def search(self, keep_password=False):
        global _video_password
        url = self.url.get().strip()
        if not url:
            self._reject_search(tr("need_any"))
            return
        try:
            classify_url(url)
        except ValueError as error:
            self._reject_search(str(error))
            return
        if not keep_password:
            _video_password = ""
        self.search_gen += 1
        generation = self.search_gen
        self.say("checking")
        self.set_busy(True)

        def worker():
            try:
                result = inspect_link(url)
            except Exception as error:
                self.after(0, lambda gen=generation, err=error: self._search_result(gen, error=err))
                return
            self.after(0, lambda gen=generation, found=result: self._search_result(gen, result=found))

        threading.Thread(target=worker, daemon=True).start()

    def _search_result(self, generation, result=None, error=None):
        if generation != self.search_gen:
            return
        if error is not None:
            self.search_failed(error)
            return
        self.search_done(result)

    def search_failed(self, error):
        global _video_password
        text = str(error)
        self.set_busy(False, text)
        self.status_label.configure(fg="#fda4af")
        if needs_passcode(text):
            password = simpledialog.askstring(
                tr("passcode_title"),
                tr("passcode_prompt"),
                parent=self,
                show="*",
            )
            if password and password.strip():
                _video_password = password.strip()
                self.search(keep_password=True)
            return
        self._report("error", where="search", host=site_host(self.url.get()), text=text[:500])

    def _fill_tree(self, tree, rows, preferred_type=None, preferred_code=None, keep=None):
        tree.delete(*tree.get_children())
        preferred = None
        for index, row in enumerate(rows):
            code, name, detail = self._row_cells(row)
            tree.insert("", "end", iid=str(index), values=(code, name, detail))
            if preferred is None and preferred_type and row["type"] == preferred_type:
                preferred = str(index)
            if preferred is None and preferred_code and row["code"] == preferred_code:
                preferred = str(index)
        if rows:
            chosen = keep if keep and tree.exists(keep) else (preferred or "0")
            tree.selection_set(chosen)
            tree.focus(chosen)
            tree.see(chosen)

    def search_done(self, result):
        self.loaded_url = result.get("url") or self.url.get().strip()
        self.video_rows = [row for row in result["rows"] if row["type"] in {"video", "audio"}]
        self.sub_rows = [row for row in result["rows"] if row["type"] in {"subs", "file"}]
        self._fill_tree(self.video_tree, self.video_rows, preferred_type="video")
        self._fill_tree(self.sub_tree, self.sub_rows)
        self.select_subtitle()
        if result["kind"] == "subtitle":
            self.video_title.set(tr("subtitle_file"))
            self.set_busy(False, key="file_ready")
        else:
            self.video_title.set(result["title"] or tr("video_fallback"))
            self.set_busy(False, key="found", videos=len(self.video_rows), subs=len(self.sub_rows))
        self._report("search", host=site_host(self.loaded_url))

    def clean_title(self):
        title = self.video_title.get().strip()
        if not title or title in {UI["ru"]["placeholder"], UI["eng"]["placeholder"]}:
            title = "download"
        cleaned = re.sub(r'[\\/:*?"<>|]', " ", title)
        return re.sub(r"\s+", " ", cleaned).strip()[:80] or "download"

    def suggest_filename(self, row):
        if row["type"] in {"subs", "file"}:
            code = row.get("lang") or row["code"].lower()
            return f"{self.clean_title()}.{code}.{self.selected_format()}"
        ext = self.selected_video_format() if row["type"] == "video" else row["ext"]
        code = tr("audio_code") if row["type"] == "audio" else row["code"]
        return f"{self.clean_title()}.{code}.{ext}"

    def selected_video_format(self):
        return VIDEO_FORMAT_BY_LABEL.get(self.video_format_var.get(), "mp4")

    def selected_format(self):
        return FORMAT_BY_LABEL.get(self.format_var.get(), "srt")

    def download_video(self):
        row = self.selected_from(self.video_tree, self.video_rows)
        if row is None:
            self.say("pick_video", "#fda4af")
            return
        self._ask_and_enqueue(row)

    def download_subs(self):
        row = self.selected_from(self.sub_tree, self.sub_rows)
        if row is None:
            self.say("pick_subs", "#fda4af")
            return
        self._ask_and_enqueue(row)

    def _unique_path(self, folder, filename):
        path = folder / filename
        reserved = {
            Path(job["destination"])
            for job in self.jobs
            if job["state"] in {"waiting", "running"}
        }
        candidate = path
        number = 2
        while candidate.exists() or candidate in reserved:
            candidate = path.with_name(f"{path.stem} ({number}){path.suffix}")
            number += 1
            if number > 500:
                break
        return candidate

    def _ask_and_enqueue(self, row):
        self._close_popups()
        if not self.folder_chosen:
            if not self.choose_folder():
                return
        folder = self.save_dir if self.save_dir.is_dir() else Path.home()
        self.save_dir = folder
        row = dict(row)
        fmt = None
        if row["type"] == "video":
            ext = self.selected_video_format()
            if ext != row.get("ext"):
                row["merged"] = True
            row["ext"] = ext
        elif row["type"] not in {"audio"}:
            fmt = self.selected_format()
        destination = self._unique_path(folder, self.suggest_filename(row))
        self._enqueue(row, destination, self.loaded_url or self.url.get().strip(), fmt)

    def _job_name(self, row):
        code = tr("audio_code") if row.get("type") == "audio" else row["code"]
        name = tr(row["name_key"]) if row.get("name_key") else row["name"]
        return f"{code} {name}".strip()

    def _refresh_job(self, job):
        name = self._job_name(job["row"])
        state = job["state"]
        button = job.get("button")
        detail = job.get("detail") or ""
        if state == "waiting":
            job["text"].set(f"{name}  —  {tr('queued')}")
            if button:
                button.configure(text=tr("cancel"), state="normal", fg="#fda4af")
        elif state == "running":
            job["text"].set(f"{name}  —  {tr('downloading')}")
            if button:
                button.configure(text=tr("cancel"), fg="#fda4af")
        elif state == "cancelled":
            job["text"].set(f"{name}  —  {tr('cancelled_state')}")
            if button:
                button.configure(text=tr("cancelled_btn"), state="disabled", fg="#94a3b8")
        elif state == "done":
            job["text"].set(f"{name}  —  {tr('saved_job', name=detail)}")
            if button:
                button.configure(text=tr("done"), state="disabled", fg="#86efac")
        else:
            job["text"].set(f"{name}  —  {detail or tr('error')}")
            if button:
                button.configure(text=tr("error"), state="disabled", fg="#fda4af")

    def _bind_queue_wheel(self, widget):
        widget.bind("<MouseWheel>", self._queue_wheel, add="+")

    def _queue_wheel(self, event):
        if self.queue_box.winfo_height() <= self.queue_canvas.winfo_height():
            return
        self.queue_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _queue_resized(self, event):
        self.queue_canvas.itemconfigure(self.queue_window, width=event.width)
        wrap = max(160, event.width - 120)
        if self.queue_empty.winfo_exists():
            self.queue_empty.configure(wraplength=wrap)
        for job in self.jobs:
            label = job.get("label")
            if label is not None and label.winfo_exists():
                label.configure(wraplength=wrap)
        self._fit_queue()

    def _fit_queue(self):
        self.queue_box.update_idletasks()
        bbox = self.queue_canvas.bbox("all")
        if not bbox:
            return
        content = max(bbox[3] - bbox[1], 1)
        height = min(content, 156)
        if int(self.queue_canvas.cget("height")) != height:
            self.queue_canvas.configure(height=height)
        self.queue_canvas.configure(scrollregion=bbox)
        if content > 156:
            self.queue_scroll.grid(row=0, column=1, sticky="ns")
        else:
            self.queue_scroll.grid_remove()
        self._poke_sky()

    def _scroll_job(self, job):
        line = job.get("line")
        if line is None:
            return
        self._fit_queue()
        total = max(self.queue_box.winfo_height(), 1)
        self.queue_canvas.yview_moveto(max(0, line.winfo_y() - 2) / total)

    def _enqueue(self, row, destination, url, fmt):
        self.job_seq += 1
        job = {
            "id": self.job_seq,
            "row": row,
            "destination": destination,
            "url": url,
            "fmt": fmt,
            "cancel": threading.Event(),
            "state": "waiting",
            "limited": is_youtube(url),
            "text": tk.StringVar(value=f"{self._job_name(row)}  —  {tr('queued')}"),
        }
        self.jobs.append(job)
        if self.queue_empty.winfo_ismapped():
            self.queue_empty.pack_forget()
        line = tk.Frame(self.queue_box, bg="#07101d")
        line.pack(fill="x", padx=6, pady=1)
        label = tk.Label(
            line,
            textvariable=job["text"],
            bg="#07101d",
            fg="#e7f2ff",
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
            wraplength=max(160, self.queue_canvas.winfo_width() - 120),
        )
        label.pack(side="left", fill="x", expand=True, padx=(4, 8))
        job["label"] = label
        button = tk.Button(
            line,
            text=tr("cancel"),
            command=lambda current=job: self.cancel_job(current),
            bg="#1e293b",
            fg="#fda4af",
            activebackground="#7f1d1d",
            activeforeground="#ffffff",
            relief="flat",
            bd=0,
            padx=8,
            pady=1,
            cursor="hand2",
            font=("Segoe UI", 8, "bold"),
        )
        button.pack(side="right", padx=4, pady=2)
        job["button"] = button
        job["line"] = line
        self._bind_queue_wheel(line)
        self._bind_queue_wheel(label)
        self._bind_queue_wheel(button)
        self._scroll_job(job)
        self._start_queue()
        self.say("started" if job["state"] == "running" else "added")

    def cancel_job(self, job):
        if job["state"] in {"done", "cancelled", "error"}:
            return
        job["cancel"].set()
        job["state"] = "cancelled"
        job["detail"] = ""
        self._refresh_job(job)
        self._start_queue()

    def _start_queue(self):
        youtube_running = any(job["state"] == "running" and job.get("limited") for job in self.jobs)
        for job in self.jobs:
            if job["state"] != "waiting":
                continue
            if job.get("limited"):
                if youtube_running:
                    continue
                youtube_running = True
            job["state"] = "running"
            job["text"].set(f"{self._job_name(job['row'])}  —  {tr('downloading')}")
            self._scroll_job(job)
            threading.Thread(target=self._run_job, args=(job,), daemon=True).start()

    def _run_job(self, job):
        if job["cancel"].is_set():
            self.after(0, lambda current=job: self._finish_job(current, "cancelled"))
            return
        row = job["row"]
        try:
            if row["type"] in {"video", "audio"}:
                def progress(data, current=job):
                    percent = (data.get("_percent_str") or "").strip()

                    def show(value=percent, item=current):
                        if item["state"] != "running":
                            return
                        item["text"].set(f"{self._job_name(item['row'])}  —  {value or tr('downloading')}")

                    self.after(0, show)

                path = download_media(job["url"], row, job["destination"], progress, job["cancel"])
            elif row["type"] == "file":
                path = download_subtitle_link(row["url"], job["destination"], job["fmt"], job["cancel"])
            elif row.get("url") and not is_youtube(job["url"]):
                path = download_subtitle_link(
                    row["url"], job["destination"], job["fmt"], job["cancel"], row.get("referer") or "",
                )
            else:
                path = download_track(
                    job["url"], row["lang"], job["destination"], job["fmt"], job["cancel"],
                    row.get("url") or "", row.get("referer") or "",
                )
        except DownloadCancelled:
            self.after(0, lambda current=job: self._finish_job(current, "cancelled"))
            return
        except Exception as error:
            message = tr("file_busy") if _file_in_use(error) else str(error)
            self.after(0, lambda current=job, text=message: self._finish_job(current, "error", text))
            return
        saved = path.name
        self.after(0, lambda current=job, name=saved: self._finish_job(current, "done", name))

    def _finish_job(self, job, state, detail=""):
        if job["state"] in {"done", "cancelled", "error"}:
            return
        job["state"] = state
        job["detail"] = detail
        self._refresh_job(job)
        if state == "done":
            self.say("saved", "#86efac", name=detail)
            self._report("download", host=site_host(job.get("url")), kind=job["row"].get("type"))
        elif state == "error":
            self.status_key = None
            self.status_args = {}
            self.status_label.configure(fg="#fda4af")
            self.status.set(detail)
            self._report(
                "error",
                where="download",
                host=site_host(job.get("url")),
                kind=job["row"].get("type"),
                text=str(detail)[:500],
            )
        self._start_queue()

    def open_folder(self):
        folder = self.save_dir if self.save_dir.is_dir() else Path.home()
        import os
        os.startfile(folder)


def main(argv):
    if "--bot" in argv:
        bot_commands()
        return
    if len(argv) >= 3 and argv[1] == "--download":
        lang = argv[2]
        url = argv[3] if len(argv) > 3 else "https://www.youtube.com/watch?v=1DilfTSy7Fo"
        result = find_tracks(url)
        print(result["title"], len(result["tracks"]))
        path = download_track(url, lang, OUT_DIR / f"subtitles.{lang}.srt")
        print(path)
        return
    app = App()
    app.after(600, ensure_bot_process)
    app.mainloop()


if __name__ == "__main__":
    main(sys.argv)
