#!/usr/bin/env python3
"""Script kiểm tra trạng thái mạng nội bộ FPT (apis.fpt.net / hrm.fpt.net) và chẩn đoán VPN.

Dùng để kiểm tra nhanh khả năng kết nối mạng nội bộ từ môi trường hiện tại:
    python3 scripts/test_vpn.py
    python3 scripts/test_vpn.py --test-connect
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from pathlib import Path

# Đảm bảo nạp đúng .env từ root
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[2]
sys.path.insert(0, str(_HERE))

for env_candidate in [_ROOT / ".env", Path.cwd() / ".env"]:
    if env_candidate.exists():
        try:
            with open(env_candidate, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                            v = v[1:-1]
                        elif " #" in v or "\t#" in v:
                            import re
                            v = re.split(r"\s+#", v, 1)[0].strip()
                        v = v.strip().strip("'\"")
                        os.environ[k] = v
        except Exception:
            pass
        break

import vpn_manager


def diagnose_network() -> dict:
    results = {}
    targets = [
        ("apis.fpt.net", 443),
        ("hrm.fpt.net", 443),
    ]

    for host, port in targets:
        info = {"host": host, "port": port, "ip": None, "reachable": False, "error": None}
        try:
            ip = socket.gethostbyname(host)
            info["ip"] = ip
            with socket.create_connection((host, port), timeout=3.0):
                info["reachable"] = True
        except Exception as e:
            info["error"] = str(e)
        results[host] = info

    is_accessible = any(r["reachable"] for r in results.values())

    vpn_type = os.environ.get("HRM_VPN_TYPE", "")
    vpn_host = os.environ.get("HRM_VPN_HOST", "") or os.environ.get("HRM_VPN_SERVER", "")
    if not vpn_type:
        vpn_type = "openvpn" if "csocvpn" in vpn_host.lower() else "openvpn"

    has_totp_secret = bool(os.environ.get("HRM_VPN_TOTP_SECRET") or os.environ.get("HRM_TOTP_SECRET"))
    totp_preview = None
    if has_totp_secret:
        try:
            totp_preview = vpn_manager.generate_totp(os.environ.get("HRM_VPN_TOTP_SECRET") or os.environ.get("HRM_TOTP_SECRET"))
        except Exception:
            totp_preview = "Lỗi sinh TOTP"

    vpn_info = {
        "enabled": os.environ.get("HRM_VPN_ENABLED", "auto"),
        "type": vpn_type,
        "host": vpn_host or ("csocvpn.fpt.net" if vpn_type == "openvpn" else ""),
        "user": os.environ.get("HRM_VPN_USERNAME", "") or os.environ.get("HRM_USERNAME", ""),
        "has_password": bool(
            os.environ.get("HRM_VPN_PASSWORD")
            or os.environ.get("HRM_VPN_PASSWORD_ENC")
            or os.environ.get("HRM_PASSWORD")
            or os.environ.get("HRM_PASSWORD_ENC")
        ),
        "has_totp_secret": has_totp_secret,
        "totp_sample_otp": f"{totp_preview[:2]}****" if totp_preview else None,
        "config_path": os.environ.get("HRM_VPN_CONFIG_PATH", ""),
    }

    return {
        "accessible": is_accessible,
        "targets": results,
        "vpn_config": vpn_info,
    }


def main():
    parser = argparse.ArgumentParser(description="Kiểm tra kết nối mạng nội bộ HRM và chẩn đoán VPN")
    parser.add_argument("--test-connect", action="store_true", help="Thử kích hoạt kết nối VPN thực tế")
    parser.add_argument("--force", action="store_true", help="Bắt buộc kết nối VPN kể cả khi mạng nội bộ đã thông")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả định dạng JSON")
    args = parser.parse_args()

    diag = diagnose_network()

    if args.test_connect:
        mode_label = "Bắt buộc kết nối (force=True)" if args.force else "Tự động (auto)"
        print(f"[TEST] Bắt đầu thử nghiệm kết nối VPN ({mode_label})...")
        try:
            with vpn_manager.managed_vpn(force=args.force):
                print("[TEST] Đã vào trong context VPN. Kiểm tra lại kết nối...")
                diag_after = diagnose_network()
                diag["after_vpn"] = diag_after
                if diag_after["accessible"]:
                    print("[TEST] ✓ Kết nối mạng nội bộ qua VPN thành công!")
                else:
                    print("[TEST] ✗ Kết nối VPN bật được nhưng chưa thông tới site HRM.", file=sys.stderr)
        except Exception as e:
            diag["vpn_error"] = str(e)
            print(f"[TEST] ✗ Lỗi kích hoạt VPN: {e}", file=sys.stderr)

    if args.json or not sys.stdout.isatty():
        print(json.dumps(diag, ensure_ascii=False, indent=2))
    else:
        print("=== KẾT QUẢ KIỂM TRA MẠNG NỘI BỘ HRM ===")
        status_text = "✓ KHẢ DỤNG (Đang trong mạng FPT hoặc VPN)" if diag["accessible"] else "✗ CHƯA KẾT NỐI (Cần bật VPN)"
        print(f"Trạng thái chung: {status_text}\n")
        print("Chi tiết các host nội bộ:")
        for host, r in diag["targets"].items():
            icon = "✓" if r["reachable"] else "✗"
            ip_str = f"({r['ip']})" if r['ip'] else "(Không phân giải được DNS)"
            print(f"  [{icon}] {host}:443 {ip_str} - {'Thành công' if r['reachable'] else r['error']}")

        print("\nCấu hình VPN hiện tại:")
        v = diag["vpn_config"]
        print(f"  - HRM_VPN_ENABLED   : {v['enabled']}")
        print(f"  - HRM_VPN_TYPE      : {v['type']}")
        print(f"  - HRM_VPN_HOST      : {v['host'] or '(Chưa thiết lập)'}")
        print(f"  - HRM_VPN_USER      : {v['user'] or '(Chưa thiết lập)'}")
        print(f"  - Có Password       : {'Có' if v['has_password'] else 'Chưa cấu hình'}")
        print(f"  - TOTP 2FA Secret   : {'Có (' + v['totp_sample_otp'] + ')' if v['has_totp_secret'] else 'Chưa cấu hình (cần nhập OTP tay)'}")
        print(f"  - File Config .ovpn : {v['config_path'] or '(Dùng tự động / data/csocvpn.ovpn)'}")


if __name__ == "__main__":
    main()
