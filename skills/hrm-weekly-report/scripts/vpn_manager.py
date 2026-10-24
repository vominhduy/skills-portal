"""VPN Manager cho HRM Weekly Report.

Cung cấp cơ chế tự động kiểm tra và kết nối VPN vào mạng nội bộ FPT (hrm.fpt.net / apis.fpt.net)
khi script được thực thi ngoài văn phòng (làm việc từ xa, VPS, cloud container, máy cá nhân).

Hỗ trợ các loại VPN / Tunnel:
  1. openvpn       : OpenVPN Connect (hỗ trợ csocvpn.fpt.net, account FPT, pass, và OTP / TOTP tự động)
  2. openconnect   : Cisco AnyConnect / Fortinet SSL-VPN / Pulse / GlobalProtect
  3. openfortivpn  : Fortinet FortiGate SSL-VPN chuyên biệt
  4. wireguard     : WireGuard (wg-quick)
  5. ssh_tunnel    : SSH Dynamic SOCKS5 Proxy vào máy chủ nội bộ (không cần quyền root)
  6. custom        : Script / lệnh tùy biến (HRM_VPN_UP_COMMAND & HRM_VPN_DOWN_COMMAND)
"""

from __future__ import annotations

import atexit
import base64
import contextlib
import hashlib
import hmac
import os
import re
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple


def _load_env_fallback() -> None:
    for parent in [Path(__file__).resolve().parents[2], Path(__file__).resolve().parents[3]]:
        env_file = parent / ".env"
        if env_file.exists():
            try:
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip()
                            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                                v = v[1:-1]
                            elif " #" in v or "\t#" in v:
                                v = re.split(r"\s+#", v, 1)[0].strip()
                            v = v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
            except Exception:
                pass
            break


_load_env_fallback()


# ─── Kiểm tra kết nối mạng nội bộ ─────────────────────────────────────────────

DEFAULT_INTERNAL_TARGETS: List[Tuple[str, int]] = [
    ("apis.fpt.net", 443),
    ("hrm.fpt.net", 443),
    ("172.20.18.32", 443),  # IP nội bộ trực tiếp của hrm.fpt.net (tránh phụ thuộc DNS host)
]


def check_internal_network(
    targets: Optional[List[Tuple[str, int]]] = None,
    timeout: float = 3.0,
) -> bool:
    """Kiểm tra xem ít nhất một trong các host nội bộ HRM có thể kết nối được không.

    Trả về True nếu kết nối TCP thành công đến cổng đích, ngược lại False.
    """
    targets_to_check = targets or DEFAULT_INTERNAL_TARGETS

    # Kiểm tra thêm host tùy chỉnh từ env nếu có
    custom_check = os.environ.get("HRM_VPN_CHECK_HOST", "").strip()
    if custom_check:
        if ":" in custom_check:
            host, port_str = custom_check.split(":", 1)
            try:
                targets_to_check = [(host.strip(), int(port_str.strip()))] + list(targets_to_check)
            except ValueError:
                pass
        else:
            targets_to_check = [(custom_check, 443)] + list(targets_to_check)

    for host, port in targets_to_check:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, OSError):
            continue
    return False


# ─── TOTP Generator (RFC 6238 - Tự động sinh OTP từ Secret Key) ─────────────

def generate_totp(secret: str, digits: int = 6, period: int = 30) -> str:
    """Tự động sinh mã OTP 6 số theo chuẩn RFC 6238 từ TOTP Secret Key (hỗ trợ Base32, Hex, hoặc Raw).

    Dùng cho xác thực 2FA của OpenVPN Connect (csocvpn.fpt.net) mà không cần nhập tay.
    """
    cleaned = secret.strip().replace(" ", "")
    key: Optional[bytes] = None

    # 1. Thử Base32 chuẩn (RFC 3548)
    try:
        b32_str = cleaned.upper()
        missing_padding = len(b32_str) % 8
        if missing_padding:
            b32_str += "=" * (8 - missing_padding)
        key = base64.b32decode(b32_str, casefold=True)
    except Exception:
        pass

    # 2. Thử Hexadecimal (nếu key ở định dạng hex, ví dụ bỏ prefix TOTP/0x)
    if key is None:
        try:
            hex_str = cleaned
            if hex_str.upper().startswith("TOTP"):
                hex_str = hex_str[4:]
            if hex_str.lower().startswith("0x"):
                hex_str = hex_str[2:]
            key = bytes.fromhex(hex_str)
        except Exception:
            pass

    # 3. Fallback chuỗi bytes thông thường
    if key is None:
        key = cleaned.encode("utf-8")

    counter = int(time.time()) // period
    msg = struct.pack(">Q", counter)
    h = hmac.new(key, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack(">I", h[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(code % (10**digits)).zfill(digits)


# ─── Trợ giúp giải mã mật khẩu ───────────────────────────────────────────────

def _decrypt_password_if_needed(password: Optional[str]) -> Optional[str]:
    """Giải mã mật khẩu nếu đang dùng chuẩn mã hoá HRM_PASSWORD_ENC / AES-GCM."""
    if password:
        return password

    enc_pw = os.environ.get("HRM_VPN_PASSWORD_ENC") or os.environ.get("HRM_PASSWORD_ENC")
    enc_key = os.environ.get("CREDENTIALS_ENCRYPTION_KEY")

    if not enc_pw or not enc_key:
        return None

    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        if len(enc_key) == 64:
            key_bytes = bytes.fromhex(enc_key)
        else:
            key_bytes = hashlib.sha256(enc_key.encode("utf-8")).digest()

        buf = base64.b64decode(enc_pw)
        if len(buf) >= 28:
            try:
                # Layout 1: iv (12b) + tag (16b) + ciphertext
                iv = buf[:12]
                tag = buf[12:28]
                ct = buf[28:]
                aes = AESGCM(key_bytes)
                return aes.decrypt(iv, ct + tag, None).decode("utf-8")
            except Exception:
                # Layout 2: iv (16b) + tag (16b) + ciphertext
                if len(buf) >= 32:
                    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

                    iv = buf[:16]
                    tag = buf[16:32]
                    ct = buf[32:]
                    cipher = Cipher(algorithms.AES(key_bytes), modes.GCM(iv, tag))
                    decryptor = cipher.decryptor()
                    return (decryptor.update(ct) + decryptor.finalize()).decode("utf-8")
    except Exception:
        pass

    return None


def _clean_env_val(val: Optional[Any]) -> str:
    """Loại bỏ khoảng trắng, dấu ngoặc kép và trailing comment (# ...) từ biến môi trường."""
    if val is None:
        return ""
    v = str(val).strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1].strip()
    if " #" in v or "\t#" in v:
        v = re.split(r"\s+#", v, 1)[0].strip()
    return v


# ─── Lớp quản lý VPN ─────────────────────────────────────────────────────────

class VPNManager:
    """Quản lý kết nối VPN tự động vào mạng nội bộ cho các tác vụ HRM."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        cfg = config or {}

        # 1. Bật/tắt VPN: 'auto' (chỉ bật khi không truy cập được), 'true', 'false'
        raw_enabled = cfg.get("enabled") if cfg.get("enabled") is not None else os.environ.get("HRM_VPN_ENABLED", "auto")
        self.enabled_mode = _clean_env_val(raw_enabled).lower()

        # 2. Host gateway
        raw_host = cfg.get("host") or os.environ.get("HRM_VPN_HOST") or os.environ.get("HRM_VPN_SERVER", "")
        self.host = _clean_env_val(raw_host)

        # 3. Loại VPN: nếu host là csocvpn hoặc cấu hình openvpn thì ưu tiên openvpn
        default_type = "openvpn" if "csocvpn" in self.host.lower() else "openconnect"
        raw_type = cfg.get("type") or os.environ.get("HRM_VPN_TYPE", default_type)
        self.vpn_type = _clean_env_val(raw_type).lower()

        # Nếu chọn openvpn mà chưa có host, mặc định là csocvpn.fpt.net
        if self.vpn_type == "openvpn" and not self.host:
            self.host = "csocvpn.fpt.net"

        port_val = cfg.get("port") or _clean_env_val(os.environ.get("HRM_VPN_PORT", "443"))
        try:
            self.port = int(port_val)
        except ValueError:
            self.port = 443

        # 4. Tài khoản công ty (Username)
        raw_user = (
            cfg.get("username")
            or os.environ.get("HRM_VPN_USERNAME")
            or os.environ.get("HRM_VPN_USER")
            or os.environ.get("HRM_USERNAME", "")
        )
        self.username = _clean_env_val(raw_user)

        # 5. Mật khẩu
        raw_pwd = (
            cfg.get("password")
            or os.environ.get("HRM_VPN_PASSWORD")
            or os.environ.get("HRM_PASSWORD")
        )
        decrypted = _decrypt_password_if_needed(raw_pwd)
        self.password = _clean_env_val(decrypted if decrypted is not None else (raw_pwd or ""))

        # 6. Mã OTP & Khóa TOTP Secret
        self.otp_direct = _clean_env_val(
            cfg.get("otp") or os.environ.get("HRM_VPN_OTP", "")
        )
        raw_totp = (
            cfg.get("totp_secret")
            or os.environ.get("HRM_VPN_TOTP_SECRET")
            or os.environ.get("HRM_TOTP_SECRET", "")
        )
        self.totp_secret = _clean_env_val(raw_totp)

        # Chế độ truyền OTP trong OpenVPN:
        raw_otp_mode = cfg.get("otp_mode") or os.environ.get("HRM_VPN_OTP_MODE", "append")
        self.otp_mode = _clean_env_val(raw_otp_mode).lower()

        # Protocol cho openconnect: 'fortinet', 'anyconnect', 'gp', 'pulse'
        raw_protocol = cfg.get("protocol") or os.environ.get("HRM_VPN_PROTOCOL", "fortinet")
        self.protocol = _clean_env_val(raw_protocol).lower()

        # Đường dẫn file config (.ovpn hoặc wg .conf)
        raw_cfg_path = cfg.get("config_path") or os.environ.get("HRM_VPN_CONFIG_PATH", "")
        self.config_path = _clean_env_val(raw_cfg_path)

        # Lệnh tùy chỉnh
        self.up_command = _clean_env_val(
            cfg.get("up_command") or os.environ.get("HRM_VPN_UP_COMMAND", "")
        )
        self.down_command = _clean_env_val(
            cfg.get("down_command") or os.environ.get("HRM_VPN_DOWN_COMMAND", "")
        )

        # SSH Tunnel config
        self.ssh_host = _clean_env_val(os.environ.get("HRM_VPN_SSH_HOST", ""))
        self.ssh_port = int(_clean_env_val(os.environ.get("HRM_VPN_SSH_PORT", "22")) or 22)
        self.ssh_user = _clean_env_val(os.environ.get("HRM_VPN_SSH_USER", ""))
        self.ssh_key = _clean_env_val(os.environ.get("HRM_VPN_SSH_KEY", ""))
        self.socks_port = int(_clean_env_val(os.environ.get("HRM_VPN_SOCKS_PORT", "10808")) or 10808)

        # Quyền sudo & mật khẩu sudo (nếu có)
        self.sudo_password = _clean_env_val(os.environ.get("HRM_VPN_SUDO_PASSWORD", ""))
        raw_sudo = cfg.get("use_sudo") or os.environ.get("HRM_VPN_USE_SUDO", "auto")
        use_sudo_str = _clean_env_val(raw_sudo).lower()
        if use_sudo_str in ("true", "1", "yes"):
            self.use_sudo = True
        elif use_sudo_str in ("false", "0", "no"):
            self.use_sudo = False
        else:
            self.use_sudo = bool(os.name != "nt" and os.geteuid() != 0)

        # Timeout chờ kết nối
        raw_timeout = cfg.get("timeout") or os.environ.get("HRM_VPN_TIMEOUT", "35")
        try:
            self.timeout = float(_clean_env_val(raw_timeout))
        except ValueError:
            self.timeout = 35.0

        # Tự động ngắt kết nối sau khi xong
        raw_auto_disc = cfg.get("auto_disconnect") or os.environ.get("HRM_VPN_AUTO_DISCONNECT", "true")
        auto_disc_str = _clean_env_val(raw_auto_disc).lower()
        self.auto_disconnect = auto_disc_str not in ("false", "0", "no")

        # Trạng thái runtime
        self.process: Optional[subprocess.Popen[Any]] = None
        self.temp_files: List[Path] = []
        self.connected_by_us: bool = False
        self._registered_exit_handler: bool = False

    def is_enabled(self) -> bool:
        """Kiểm tra cấu hình có cho phép chạy VPN hay không."""
        return self.enabled_mode not in ("false", "0", "no", "off", "disable", "disabled")

    def _mask_user(self, user: str) -> str:
        if not user or len(user) <= 3:
            return "***"
        return f"{user[:2]}***{user[-1]}"

    def resolve_otp(self) -> str:
        """Lấy mã OTP 6 chữ số: tự động sinh từ TOTP Secret, hoặc đọc từ tham số, hoặc prompt người dùng."""
        if self.otp_direct:
            print(f"[HRM-VPN] Sử dụng mã OTP được chỉ định ({self.otp_direct[:2]}****).")
            return self.otp_direct

        if self.totp_secret:
            try:
                code = generate_totp(self.totp_secret)
                print(f"[HRM-VPN] ✓ Tự động sinh mã OTP từ TOTP Secret thành công ({code[:2]}****).")
                return code
            except Exception as e:
                print(f"[HRM-VPN] ⚠️  Lỗi sinh OTP từ TOTP Secret: {e}", file=sys.stderr)

        # Nếu chạy trực tiếp từ Terminal và chưa có OTP -> hỏi người dùng
        if sys.stdin and sys.stdin.isatty():
            try:
                user_input = input("[HRM-VPN] Nhập mã OTP từ Authenticator (6 chữ số): ").strip()
                if user_input:
                    return user_input
            except (KeyboardInterrupt, EOFError):
                pass

        print(
            "[HRM-VPN] ⚠️  Cảnh báo: Chưa cấu hình HRM_VPN_TOTP_SECRET hoặc mã OTP. "
            "Nếu máy chủ VPN yêu cầu xác thực 2FA, kết nối có thể thất bại.",
            file=sys.stderr,
        )
        return ""

    def start(self, force: bool = False) -> bool:
        """Khởi động kết nối VPN nếu mạng nội bộ chưa thông hoặc khi có cờ force=True."""
        if not self.is_enabled():
            print("[HRM-VPN] Cơ chế VPN đang bị tắt bởi cấu hình (HRM_VPN_ENABLED=false).")
            return check_internal_network()

        # 1. Kiểm tra mạng nội bộ trước (nếu không force và ở chế độ auto)
        print("[HRM-VPN] Đang kiểm tra kết nối mạng nội bộ HRM (apis.fpt.net / hrm.fpt.net)...")
        already_accessible = check_internal_network(timeout=3.0)
        if already_accessible and not force and self.enabled_mode == "auto":
            print("[HRM-VPN] ✓ Mạng nội bộ FPT đã khả dụng (không cần kích hoạt VPN).")
            self.connected_by_us = False
            return True

        if force:
            print(f"[HRM-VPN] Bắt buộc kích hoạt VPN ({self.vpn_type}) theo yêu cầu người dùng (force=True)...")
        elif self.enabled_mode in ("auto", "true", "1", "yes"):
            print(f"[HRM-VPN] ⚠️  Chưa kết nối mạng nội bộ. Bắt đầu kích hoạt VPN ({self.vpn_type})...")

        # 2. Đăng ký dọn dẹp khi tiến trình thoát đột ngột
        if not self._registered_exit_handler:
            atexit.register(self.stop)
            self._setup_signal_handlers()
            self._registered_exit_handler = True

        # 3. Kích hoạt VPN tương ứng
        try:
            if self.vpn_type == "openvpn":
                self._start_openvpn()
            elif self.vpn_type == "openconnect":
                self._start_openconnect()
            elif self.vpn_type == "openfortivpn":
                self._start_openfortivpn()
            elif self.vpn_type == "wireguard":
                self._start_wireguard()
            elif self.vpn_type == "ssh_tunnel":
                self._start_ssh_tunnel()
            elif self.vpn_type == "custom":
                self._start_custom()
            else:
                raise ValueError(
                    f"Loại VPN '{self.vpn_type}' không được hỗ trợ. "
                    "Các loại hợp lệ: openvpn, openconnect, openfortivpn, wireguard, ssh_tunnel, custom."
                )

            # 4. Chờ mạng nội bộ thông
            print(f"[HRM-VPN] Đang chờ kết nối ổn định (tối đa {int(self.timeout)}s)...")
            start_time = time.time()
            connected = False

            while time.time() - start_time < self.timeout:
                if self.process and self.process.poll() is not None:
                    stderr_msg = ""
                    if self.process.stderr:
                        try:
                            stderr_msg = self.process.stderr.read().decode("utf-8", errors="replace")
                        except Exception:
                            pass
                    raise RuntimeError(
                        f"Tiến trình VPN dừng bất ngờ với mã lỗi {self.process.returncode}: {stderr_msg[:500]}"
                    )

                # Kiểm tra log OpenVPN nếu có
                ovpn_log = Path("/tmp/openvpn_hrm.log")
                if ovpn_log.exists():
                    try:
                        content = ovpn_log.read_text(errors="replace")
                        if "AUTH_FAILED" in content or "auth-failure" in content:
                            raise RuntimeError(
                                "Xác thực OpenVPN thất bại (AUTH_FAILED). "
                                "Vui lòng kiểm tra lại tài khoản, mật khẩu hoặc mã OTP."
                            )
                        if "Initialization Sequence Completed" in content:
                            connected = True
                            break
                    except RuntimeError:
                        raise
                    except Exception:
                        pass

                if check_internal_network(timeout=1.5):
                    connected = True
                    break
                time.sleep(1.2)

            if not connected:
                ovpn_detail = ""
                ovpn_log = Path("/tmp/openvpn_hrm.log")
                if ovpn_log.exists():
                    try:
                        recent = ovpn_log.read_text(errors="replace").splitlines()[-8:]
                        ovpn_detail = "\nLog OpenVPN gần nhất:\n  " + "\n  ".join(recent)
                    except Exception:
                        pass

                self.stop()
                raise TimeoutError(
                    f"Quá thời gian ({self.timeout}s) nhưng không thể kết nối tới site nội bộ HRM qua VPN. "
                    f"Vui lòng kiểm tra lại tài khoản, mật khẩu, mã OTP, hoặc quyền mạng.{ovpn_detail}"
                )

            self.connected_by_us = True
            print("[HRM-VPN] ✓ Kết nối VPN thành công! Mạng nội bộ HRM đã sẵn sàng.")
            return True

        except Exception as e:
            self.stop()
            print(f"[HRM-VPN] ❌ Kích hoạt VPN thất bại: {e}", file=sys.stderr)
            raise

    # ─── OpenVPN Connect (csocvpn.fpt.net) ────────────────────────────────────

    def _resolve_openvpn_config(self) -> str:
        """Tìm file config .ovpn có sẵn hoặc tự động tạo cấu hình mẫu cho csocvpn.fpt.net."""
        project_root = Path(__file__).resolve().parents[3]

        # 1. Nếu chỉ định cụ thể qua HRM_VPN_CONFIG_PATH
        if self.config_path:
            p = Path(self.config_path)
            if p.is_absolute() and p.exists():
                return str(p)
            if (Path.cwd() / p).exists():
                return str((Path.cwd() / p).resolve())
            for candidate in [project_root / p, Path(__file__).resolve().parents[2] / p]:
                if candidate.exists():
                    return str(candidate.resolve())

        # 2. Tìm trong các thư mục mặc định của dự án
        search_candidates = [
            Path.cwd() / "data" / "client.ovpn",
            Path.cwd() / "data" / "csocvpn.ovpn",
            project_root / "data" / "client.ovpn",
            project_root / "data" / "csocvpn.ovpn",
            project_root / "client.ovpn",
            project_root / "csocvpn.ovpn",
            Path.cwd() / "csocvpn.ovpn",
            Path.cwd() / "client.ovpn",
        ]
        for candidate in search_candidates:
            if candidate.exists():
                print(f"[HRM-VPN] Tìm thấy file config OpenVPN: {candidate}")
                return str(candidate.resolve())

        # 3. Tự động sinh config cho csocvpn.fpt.net
        print(f"[HRM-VPN] Chưa có file .ovpn sẵn, tự động tạo cấu hình OpenVPN cho {self.host}...")
        cfg_fd, cfg_path = tempfile.mkstemp(prefix="openvpn_csoc_", suffix=".ovpn")
        self.temp_files.append(Path(cfg_path))

        port = self.port or 443
        ovpn_content = (
            f"client\n"
            f"dev tun\n"
            f"proto tcp\n"
            f"remote {self.host} {port}\n"
            f"resolv-retry infinite\n"
            f"nobind\n"
            f"persist-key\n"
            f"persist-tun\n"
            f"remote-cert-tls server\n"
            f"cipher AES-256-GCM\n"
            f"data-ciphers AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305\n"
            f"auth-nocache\n"
            f"verb 3\n"
        )
        with os.fdopen(cfg_fd, "w", encoding="utf-8") as f:
            f.write(ovpn_content)
        os.chmod(cfg_path, 0o600)
        return cfg_path

    def _start_openvpn(self) -> None:
        """Kích hoạt OpenVPN (hỗ trợ csocvpn.fpt.net, account FPT, pass, và OTP)."""
        bin_path = shutil.which("openvpn") or "/usr/sbin/openvpn"
        if not os.path.exists(bin_path):
            raise FileNotFoundError(
                "Không tìm thấy OpenVPN trên hệ thống. "
                "Cài đặt bằng lệnh: sudo apt-get install -y openvpn"
            )

        config_file = self._resolve_openvpn_config()
        otp = self.resolve_otp()

        # Xây dựng lệnh openvpn
        cmd: List[str] = []
        if self.use_sudo:
            if self.sudo_password:
                cmd.extend(["sudo", "-S"])
            else:
                cmd.extend(["sudo", "-n"])
        cmd.extend([bin_path, "--config", config_file])

        # Quản lý file xác thực auth-user-pass
        if self.username:
            auth_fd, auth_path = tempfile.mkstemp(prefix="openvpn_auth_", suffix=".txt")
            self.temp_files.append(Path(auth_path))

            # Trong OpenVPN Access Server và PAM 2FA:
            # - Mode 'append' (phổ biến nhất): Password được nối trực tiếp với OTP: <password><otp>
            # - Mode 'separate' / 'static_challenge': dòng 1 username, dòng 2 password, dòng 3 otp
            effective_password = self.password
            if otp:
                if self.otp_mode == "append":
                    effective_password = f"{self.password}{otp}"
                elif self.otp_mode in ("separate", "static_challenge"):
                    cmd.extend(["--static-challenge", "OTP", "1"])

            with os.fdopen(auth_fd, "w", encoding="utf-8") as f:
                f.write(f"{self.username}\n{effective_password}\n")
                if otp and self.otp_mode in ("separate", "static_challenge"):
                    f.write(f"{otp}\n")

            os.chmod(auth_path, 0o600)
            cmd.extend(["--auth-user-pass", auth_path])

        # Ghi log chi tiết ra file tạm để chẩn đoán khi gặp sự cố
        log_path = "/tmp/openvpn_hrm.log"
        cmd.extend(["--mute-replay-warnings", "--log", log_path])

        masked_user = self._mask_user(self.username)
        has_otp_str = "Có OTP" if otp else "Không có OTP"
        print(f"[HRM-VPN] Khởi chạy OpenVPN ({self.host}, user={masked_user}, {has_otp_str})...")

        stdin_mode = subprocess.PIPE if (self.use_sudo and self.sudo_password) else None

        self.process = subprocess.Popen(
            cmd,
            stdin=stdin_mode,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != "nt" else None,
        )

        # Truyền sudo password vào stdin nếu cần
        if self.use_sudo and self.sudo_password and self.process.stdin:
            try:
                self.process.stdin.write(f"{self.sudo_password}\n".encode("utf-8"))
                self.process.stdin.flush()
            except Exception:
                pass

    # ─── OpenConnect (Cisco / Fortinet / GP) ──────────────────────────────────

    def _start_openconnect(self) -> None:
        """Kích hoạt VPN qua OpenConnect (Cisco / Fortinet / GP / Pulse)."""
        bin_path = shutil.which("openconnect")
        if not bin_path:
            raise FileNotFoundError(
                "Không tìm thấy công cụ 'openconnect' trên hệ thống. "
                "Cài đặt bằng lệnh: sudo apt-get install -y openconnect"
            )

        if not self.host:
            raise ValueError("Thiếu cấu hình HRM_VPN_HOST cho openconnect.")

        cmd: List[str] = []
        if self.use_sudo:
            if self.sudo_password:
                cmd.extend(["sudo", "-S"])
            else:
                cmd.extend(["sudo", "-n"])
        cmd.append(bin_path)

        if self.protocol:
            cmd.extend(["--protocol", self.protocol])

        if self.username:
            cmd.extend(["--user", self.username])

        cmd.append("--passwd-on-stdin")

        if os.environ.get("HRM_VPN_INSECURE_SSL", "").lower() in ("true", "1"):
            cmd.append("--no-cert-check")

        server_target = f"{self.host}:{self.port}" if self.port != 443 else self.host
        cmd.append(server_target)

        masked_user = self._mask_user(self.username)
        print(f"[HRM-VPN] Khởi chạy OpenConnect (protocol={self.protocol}, host={server_target}, user={masked_user})...")

        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != "nt" else None,
        )

        if self.process.stdin:
            otp = self.resolve_otp()
            effective_password = f"{self.password}{otp}" if otp else self.password
            pwd_input = f"{effective_password}\n".encode("utf-8")
            self.process.stdin.write(pwd_input)
            self.process.stdin.flush()
            self.process.stdin.close()

    # ─── OpenFortiVPN (Fortinet SSL-VPN) ──────────────────────────────────────

    def _start_openfortivpn(self) -> None:
        """Kích hoạt VPN qua OpenFortiVPN (Fortinet SSL-VPN)."""
        bin_path = shutil.which("openfortivpn")
        if not bin_path:
            raise FileNotFoundError(
                "Không tìm thấy công cụ 'openfortivpn' trên hệ thống. "
                "Cài đặt bằng lệnh: sudo apt-get install -y openfortivpn"
            )

        if not self.host:
            raise ValueError("Thiếu cấu hình HRM_VPN_HOST cho openfortivpn.")

        otp = self.resolve_otp()
        effective_password = f"{self.password}{otp}" if otp else self.password

        conf_fd, conf_path = tempfile.mkstemp(prefix="openfortivpn_", suffix=".conf")
        self.temp_files.append(Path(conf_path))

        with os.fdopen(conf_fd, "w", encoding="utf-8") as f:
            f.write(f"host = {self.host}\n")
            f.write(f"port = {self.port}\n")
            if self.username:
                f.write(f"username = {self.username}\n")
            if effective_password:
                f.write(f"password = {effective_password}\n")
            if otp:
                f.write(f"otp = {otp}\n")
            trusted_cert = os.environ.get("HRM_VPN_TRUSTED_CERT", "")
            if trusted_cert:
                f.write(f"trusted-cert = {trusted_cert}\n")
            f.write("set-dns = 1\n")
            f.write("set-routes = 1\n")

        os.chmod(conf_path, 0o600)

        cmd: List[str] = []
        if self.use_sudo:
            if self.sudo_password:
                cmd.extend(["sudo", "-S"])
            else:
                cmd.extend(["sudo", "-n"])
        cmd.extend([bin_path, "-c", conf_path])

        masked_user = self._mask_user(self.username)
        print(f"[HRM-VPN] Khởi chạy OpenFortiVPN (host={self.host}:{self.port}, user={masked_user})...")

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != "nt" else None,
        )

    # ─── WireGuard / SSH Tunnel / Custom ─────────────────────────────────────

    def _start_wireguard(self) -> None:
        """Kích hoạt WireGuard qua wg-quick."""
        bin_path = shutil.which("wg-quick")
        if not bin_path:
            raise FileNotFoundError("Không tìm thấy công cụ 'wg-quick' trên hệ thống.")

        target = self.config_path or "wg0"
        cmd: List[str] = []
        if self.use_sudo:
            cmd.extend(["sudo", "-n"])
        cmd.extend([bin_path, "up", target])

        print(f"[HRM-VPN] Khởi chạy WireGuard ({target})...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Lỗi khởi chạy WireGuard: {res.stderr}")

    def _start_ssh_tunnel(self) -> None:
        """Khởi tạo SSH Dynamic SOCKS5 Proxy vào mạng nội bộ (không cần quyền root)."""
        bin_path = shutil.which("ssh")
        if not bin_path:
            raise FileNotFoundError("Không tìm thấy lệnh 'ssh' trên hệ thống.")

        if not self.ssh_host:
            raise ValueError("Thiếu cấu hình HRM_VPN_SSH_HOST cho kết nối SSH tunnel.")

        cmd = [
            bin_path,
            "-D", str(self.socks_port),
            "-N",
            "-q",
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-o", "StrictHostKeyChecking=accept-new",
            "-p", str(self.ssh_port),
        ]
        if self.ssh_key:
            cmd.extend(["-i", self.ssh_key])

        target = f"{self.ssh_user}@{self.ssh_host}" if self.ssh_user else self.ssh_host
        cmd.append(target)

        print(f"[HRM-VPN] Khởi chạy SSH SOCKS5 Tunnel (127.0.0.1:{self.socks_port} -> {target})...")
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != "nt" else None,
        )

        proxy_url = f"socks5h://127.0.0.1:{self.socks_port}"
        os.environ["HRM_PROXY_URL"] = proxy_url

    def _start_custom(self) -> None:
        """Chạy lệnh bật VPN tùy chỉnh của người dùng."""
        if not self.up_command:
            raise ValueError("Thiếu cấu hình HRM_VPN_UP_COMMAND cho chế độ 'custom'.")

        print(f"[HRM-VPN] Chạy lệnh VPN tùy biến: {self.up_command}")
        self.process = subprocess.Popen(
            self.up_command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != "nt" else None,
        )

    # ─── Dừng và dọn dẹp VPN ──────────────────────────────────────────────────

    def stop(self) -> None:
        """Ngắt kết nối VPN và dọn dẹp các tài nguyên tạm thời."""
        if not self.connected_by_us and not self.process:
            self._cleanup_temp_files()
            return

        print("[HRM-VPN] Đang ngắt kết nối VPN và phục hồi trạng thái mạng...")

        if self.vpn_type == "custom" and self.down_command:
            try:
                subprocess.run(self.down_command, shell=True, timeout=10, capture_output=True)
            except Exception as e:
                print(f"[HRM-VPN] Cảnh báo lỗi lệnh down tùy chỉnh: {e}", file=sys.stderr)

        elif self.vpn_type == "wireguard":
            target = self.config_path or "wg0"
            cmd = ["sudo", "-n", "wg-quick", "down", target] if self.use_sudo else ["wg-quick", "down", target]
            try:
                subprocess.run(cmd, timeout=10, capture_output=True)
            except Exception:
                pass

        if self.process:
            try:
                if os.name != "nt":
                    os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                else:
                    self.process.terminate()
                self.process.wait(timeout=5)
            except (subprocess.TimeoutExpired, ProcessLookupError, OSError):
                try:
                    if os.name != "nt":
                        os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                    else:
                        self.process.kill()
                except Exception:
                    pass
            finally:
                self.process = None

        if self.vpn_type == "ssh_tunnel" and "HRM_PROXY_URL" in os.environ:
            del os.environ["HRM_PROXY_URL"]

        self._cleanup_temp_files()
        self.connected_by_us = False
        print("[HRM-VPN] ✓ Đã ngắt kết nối VPN thành công.")

    def _cleanup_temp_files(self) -> None:
        for p in self.temp_files:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        self.temp_files.clear()

    def _setup_signal_handlers(self) -> None:
        def _handler(signum: int, frame: Any) -> None:
            self.stop()
            sys.exit(128 + signum)

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, _handler)
            except (ValueError, OSError):
                pass


# ─── Context Manager ──────────────────────────────────────────────────────────

@contextlib.contextmanager
def managed_vpn(
    config: Optional[Dict[str, Any]] = None,
    force: bool = False,
) -> Generator[VPNManager, None, None]:
    """Context manager tự động kết nối VPN khi vào block và ngắt khi thoát ra."""
    vpn = VPNManager(config)
    try:
        vpn.start(force=force)
        yield vpn
    finally:
        if vpn.auto_disconnect:
            vpn.stop()
        else:
            print("[HRM-VPN] Giữ kết nối VPN hoạt động theo cấu hình (HRM_VPN_AUTO_DISCONNECT=false).")
