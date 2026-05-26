# Maintainer: supss (aur) / the-white-cloud (github)
pkgname=nxm-switch
pkgver=$(grep -m1 '^version' pyproject.toml | tr -d '" ' | cut -d= -f2)
pkgrel=1
pkgdesc=$(grep -m1 '^description' pyproject.toml | sed -E 's/^description[[:space:]]*=[[:space:]]*"?(.*)"?/\1/')
arch=('any')
license=('AGPL-3.0-only')
depends=('python' 'pyside6')

package() {
    install -d "$pkgdir/usr/lib/nxm-switch"
    for f in "$startdir"/*.py; do
        install -Dm644 "$f" "$pkgdir/usr/lib/nxm-switch/$(basename "$f")"
    done
    install -Dm755 /dev/stdin "$pkgdir/usr/bin/nxm_switch" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 /usr/lib/nxm-switch/main.py "$@"
EOF
    install -Dm644 "$startdir/nxm-switch.desktop" "$pkgdir/usr/share/applications/nxm-switch.desktop"
}
