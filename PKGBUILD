# Maintainer: supss <https://github.com/the-white-cloud>
pkgname=nxm-switch
pkgver=0.5.5
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
sha256sums=('79e830711bb857c718bc34637c58f885b03703f3f48ea02761df32b83ba970e8')

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