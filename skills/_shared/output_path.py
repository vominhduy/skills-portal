#!/usr/bin/env python3
"""Shared output path helper - dùng $REPORT_OUTPUT_DIR thay hardcode /mnt/user-data/outputs/
hoặc /home/claude/ (fix vi phạm CLAUDE.md:6 cho mọi skill).
Hỗ trợ chuẩn hóa tên file output: <base>_v<N>_<HHMMSS>.<ext> (tự động tăng version nếu trùng file cũ)
và tự động phân giải (resolve) tên file gốc khi skill đọc lại file trung gian/output.
"""
from __future__ import annotations
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable

REPORT_OUTPUT_DIR = os.environ.get("REPORT_OUTPUT_DIR", "")
SKILL_DIR = os.environ.get("SKILL_DIR", "")
VN_TZ = timezone(timedelta(hours=7))


def now_hhmmss() -> str:
    """Trả về chuỗi giờ phút giây hiện tại HHMMSS theo múi giờ VN (UTC+7)."""
    return datetime.now(VN_TZ).strftime("%H%M%S")


def output_dir() -> str:
    """Trả về REPORT_OUTPUT_DIR - throw nếu chưa đặt (skill bắt buộc có)."""
    env_dir = os.environ.get("REPORT_OUTPUT_DIR", "") or REPORT_OUTPUT_DIR
    if not env_dir:
        raise RuntimeError("Thiếu env REPORT_OUTPUT_DIR - webapp inject khi chạy skill.")
    return env_dir


def skill_dir() -> str:
    env_dir = os.environ.get("SKILL_DIR", "") or SKILL_DIR
    if not env_dir:
        raise RuntimeError("Thiếu env SKILL_DIR - webapp inject khi chạy skill.")
    return env_dir


def ensure_output_dir() -> str:
    d = output_dir()
    Path(d).mkdir(parents=True, exist_ok=True)
    return d


def safe_name(name: str) -> str:
    """Sanitize tên file - chỉ giữ [A-Za-z0-9._-], thay còn lại bằng '_'."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in (name or "output")).strip("._") or "output"


def split_version_and_time(stem: str) -> tuple[str, int | None, str | None]:
    """Tách stem thành (base_stem, version_number, hhmmss)."""
    m = re.match(r"^(.*?)(?:_v(\d+))?(?:_(\d{6}))?$", stem, re.IGNORECASE)
    if m and m.group(1):
        base_stem = m.group(1)
        v_num = int(m.group(2)) if m.group(2) else None
        hhmmss = m.group(3) if m.group(3) else None
        return base_stem, v_num, hhmmss
    return stem, None, None


def next_version_number(
    target_dir: str | Path,
    base_stem: str,
    extensions: Iterable[str] | str | None = None,
    suffix_tail: str = "",
) -> int:
    """Tìm version tiếp theo (max_v + 1) trong target_dir cho base_stem.
    Hỗ trợ kiểm tra đồng thời nhiều đuôi file (ví dụ ['.json', '.md']) hoặc hậu tố (ví dụ '_safe').
    """
    dir_path = Path(target_dir)
    if not dir_path.exists() or not dir_path.is_dir():
        return 1

    if extensions is None:
        ext_pattern = r"\.[^.]+"
    elif isinstance(extensions, str):
        ext_clean = extensions if extensions.startswith(".") else f".{extensions}"
        ext_pattern = re.escape(ext_clean)
    else:
        ext_list = [e if e.startswith(".") else f".{e}" for e in extensions]
        ext_pattern = "(?:" + "|".join(re.escape(e) for e in ext_list) + ")"

    tail_pattern = re.escape(suffix_tail) if suffix_tail else ""
    pattern = re.compile(
        r"^"
        + re.escape(base_stem)
        + r"(?:_v(\d+))?(?:_\d{6})?"
        + tail_pattern
        + ext_pattern
        + r"$",
        re.IGNORECASE,
    )

    max_v = 0
    for entry in dir_path.iterdir():
        if entry.is_file():
            m = pattern.match(entry.name)
            if m:
                v_num = int(m.group(1)) if m.group(1) else 1
                if v_num > max_v:
                    max_v = v_num
    return max_v + 1


def format_versioned_filename(
    filename: str,
    target_dir: str | Path,
    hhmmss: str | None = None,
    extensions: Iterable[str] | str | None = None,
) -> str:
    """Thêm hậu tố _v{N}_{HHMMSS} cho file output. Nếu trùng base name với file cũ trong target_dir thì tăng version."""
    clean_name = safe_name(Path(filename).name)
    p = Path(clean_name)
    ext = p.suffix
    stem = p.stem

    base_stem, _, _ = split_version_and_time(stem)
    next_v = next_version_number(target_dir, base_stem, extensions=extensions or ext)
    time_suffix = hhmmss if (hhmmss and re.match(r"^\d{6}$", hhmmss)) else now_hhmmss()
    return f"{base_stem}_v{next_v}_{time_suffix}{ext}"


def ensure_versioned_path(file_path: str | Path, hhmmss: str | None = None) -> str:
    """Đảm bảo đường dẫn file đích có hậu tố _v{N}_{HHMMSS}.
    Nếu file_path đã có sẵn _v{N}_{HHMMSS} và chưa tồn tại trên ổ đĩa thì giữ nguyên (tránh tăng version 2 lần).
    Nếu chưa có _v{N}_{HHMMSS} hoặc file đã tồn tại, tự động tính version tiếp theo kèm HHMMSS.
    """
    p = Path(file_path).resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    m = re.match(r"^.+_v\d+_\d{6}\.[^.]+$", p.name, re.IGNORECASE)
    if m and not p.exists():
        return str(p)
    versioned_name = format_versioned_filename(p.name, p.parent, hhmmss=hhmmss)
    return str(p.parent / versioned_name)


def resolve_versioned_output_path(filename: str, out_dir: str | None = None, hhmmss: str | None = None) -> str:
    """Trả về đường dẫn đầy đủ trong thư mục output với tên file có _v{N}_{HHMMSS}."""
    base = Path(out_dir).resolve() if out_dir else Path(ensure_output_dir()).resolve()
    base.mkdir(parents=True, exist_ok=True)
    versioned_name = format_versioned_filename(filename, base, hhmmss=hhmmss)
    target = (base / versioned_name).resolve()
    if not str(target).startswith(str(base)):
        raise RuntimeError(f"Path traversal chặn: {filename}")
    return str(target)


def resolve_input_path(file_path: str | Path, fallback_dir: str | Path | None = None) -> str:
    """Phân giải đường dẫn file đầu vào khi skill đọc lại file:
    - Nếu file_path tồn tại trực tiếp -> trả về nguyên bản.
    - Nếu không tồn tại (ví dụ skill gọi đọc '1.json' hoặc 'story_today_review_v1.json' nhưng file thực tế
      trên đĩa là '1_v2_153012.json' hoặc 'story_today_review_v1_153012.json') -> tự động tìm phiên bản
      mới nhất khớp base_stem trong cùng thư mục (hoặc fallback_dir / REPORT_OUTPUT_DIR).
    """
    raw_str = str(file_path or "").strip()
    if not raw_str:
        return raw_str

    p = Path(raw_str)
    if p.is_file():
        return str(p)

    search_dirs: list[Path] = []
    if p.parent and str(p.parent) not in ("", "."):
        search_dirs.append(p.parent)
    if fallback_dir:
        search_dirs.append(Path(fallback_dir))
    env_out = os.environ.get("REPORT_OUTPUT_DIR", "") or REPORT_OUTPUT_DIR
    if env_out:
        search_dirs.append(Path(env_out))
    search_dirs.append(Path.cwd() / "outputs")
    search_dirs.append(Path.cwd())

    req_ext = p.suffix
    req_stem = p.stem
    base_stem, requested_v, _ = split_version_and_time(req_stem)

    pattern = re.compile(
        r"^"
        + re.escape(base_stem)
        + r"(?:_v(\d+))?(?:_(\d{6}))?"
        + re.escape(req_ext)
        + r"$",
        re.IGNORECASE,
    )

    seen_dirs: set[str] = set()
    for d in search_dirs:
        try:
            abs_d = str(d.resolve())
        except Exception:
            continue
        if abs_d in seen_dirs or not d.exists() or not d.is_dir():
            continue
        seen_dirs.add(abs_d)

        exact_candidate = d / p.name
        if exact_candidate.is_file():
            return str(exact_candidate)

        matches: list[tuple[int, int, float, Path]] = []
        for entry in d.iterdir():
            if not entry.is_file():
                continue
            m = pattern.match(entry.name)
            if m:
                v_num = int(m.group(1)) if m.group(1) else 1
                # Nếu caller chỉ định rõ _v2.json thì ưu tiên khớp đúng v2 trước
                exact_v_match = 1 if (requested_v is not None and v_num == requested_v) else 0
                try:
                    mtime = entry.stat().st_mtime
                except OSError:
                    mtime = 0.0
                matches.append((exact_v_match, v_num, mtime, entry))

        if matches:
            matches.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
            return str(matches[0][3])

    return raw_str


def join_output(*parts: str, versioned: bool = True, hhmmss: str | None = None) -> str:
    """Join path an toàn dưới REPORT_OUTPUT_DIR - tự động thêm _v{N}_{HHMMSS} cho file output chính."""
    base = Path(ensure_output_dir()).resolve()
    if not parts:
        return str(base)
    rel_parts = list(parts)
    is_hidden = any(str(part).startswith(".") for part in rel_parts)
    if versioned and not is_hidden and Path(rel_parts[-1]).suffix:
        parent_dir = base.joinpath(*rel_parts[:-1]).resolve() if len(rel_parts) > 1 else base
        parent_dir.mkdir(parents=True, exist_ok=True)
        rel_parts[-1] = format_versioned_filename(rel_parts[-1], parent_dir, hhmmss=hhmmss)
    target = base.joinpath(*rel_parts).resolve()
    if not str(target).startswith(str(base)):
        raise RuntimeError(f"Path traversal chặn: {parts}")
    return str(target)
