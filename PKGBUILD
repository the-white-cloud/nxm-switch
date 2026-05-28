# Maintainer: supss <https://github.com/the-white-cloud>
pkgname=nxm-switch
pkgver=0.5.7
pkgrel=1
pkgdesc="A rules-based nexus mod manager (nxm) launcher for Linux."
arch=('any')
url="https://github.com/the-white-cloud/nxm-switch"
license=('AGPL-3.0-only')

depends=('python' 'pyside6')
makedepends=('uv' 'python-installer' 'python-wheel')

source=(
    "$pkgname-$pkgver.tar.gz::https://github.com/the-white-cloud/nxm-switch/archive/refs/tags/v$pkgver.tar.gz"
)
sha256sums=('SKIP')

build() {
    cd "$pkgname-$pkgver"
    uv build --wheel
}

package() {
    cd "$pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl
    install -Dm644 "nxm-switch.desktop" \
        "$pkgdir/usr/share/applications/nxm-switch.desktop"
}