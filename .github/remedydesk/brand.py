"""Bakt de RemedyDesk-instellingen in de RustDesk-broncode (voor de build).

Leest .github/remedydesk/server.env en past aan:
- standaard ID-/relayserver en publieke sleutel  (libs/hbb_common/src/config.rs)
- programmanaam RemedyDesk                        (idem; daardoor ook geen update-check naar rustdesk.com)
- geen fallback naar admin.rustdesk.com           (src/common.rs)
Stopt met een fout als een vervanging niet lukt, zodat er nooit een half aangepaste build komt.
"""
import pathlib, re, sys

root = pathlib.Path(__file__).resolve().parents[2]
env = {}
for line in (root / ".github/remedydesk/server.env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
host, key, name = env.get("RD_HOST", ""), env.get("RD_KEY", ""), env.get("RD_NAME", "RemedyDesk")
if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
    sys.exit("RD_HOST ongeldig")
if not re.fullmatch(r"[A-Za-z0-9+/]{43}=", key):
    sys.exit("RD_KEY ontbreekt of is ongeldig (verwacht: inhoud van id_ed25519.pub)")
if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]{2,30}", name):
    sys.exit("RD_NAME ongeldig")


def sub(path, pattern, repl):
    p = root / path
    s = p.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, s, count=1)
    if n != 1:
        sys.exit(f"vervanging mislukt in {path}: {pattern}")
    p.write_text(new, encoding="utf-8")
    print(f"ok  {path}: {pattern[:50]}")


cfg = "libs/hbb_common/src/config.rs"
sub(cfg, r'pub const RENDEZVOUS_SERVERS: &\[&str\] = &\["[^"]*"\];',
    f'pub const RENDEZVOUS_SERVERS: &[&str] = &["{host}"];')
sub(cfg, r'pub const RS_PUB_KEY: &str = "[^"]*";', f'pub const RS_PUB_KEY: &str = "{key}";')
sub(cfg, r'pub static ref APP_NAME: RwLock<String> = RwLock::new\("RustDesk"\.to_owned\(\)\);',
    f'pub static ref APP_NAME: RwLock<String> = RwLock::new("{name}".to_owned());')
sub(cfg, r'pub static ref PROD_RENDEZVOUS_SERVER: RwLock<String> = RwLock::new\("".to_owned\(\)\);',
    f'pub static ref PROD_RENDEZVOUS_SERVER: RwLock<String> = RwLock::new("{host}".to_owned());')
sub("src/common.rs", r'"https://admin\.rustdesk\.com"\.to_owned\(\)\n\}', '"".to_owned()\n}')
print(f"RemedyDesk-instellingen ingebakken: {name} -> {host}")
