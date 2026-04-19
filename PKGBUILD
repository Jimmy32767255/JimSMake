# Maintainer: Jimmy32767255 <jimmy32767255@outlook.com>
# Contributor: Jimmy32767255 <jimmy32767255@outlook.com>

pkgname=jimsmake
pkgver=1.2.0
pkgrel=1
pkgdesc="一站式潜意识音频制作工具"
arch=('any')
url="https://github.com/Jimmy32767255/JimSMake"
license=('GPL3')
depends=(
    'python'
    'python-pyqt5'
    'python-pyqt5-sip'
    'python-pyaudio'
    'python-chardet'
    'ffmpeg'
    'python-loguru'
    'python-pyttsx3'
)
makedepends=('python-setuptools')
source=("$pkgname-$pkgver.tar.gz::$url/archive/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
    cd "$srcdir/JimSMake-$pkgver"
    # 无需构建步骤
}

package() {
    cd "$srcdir/JimSMake-$pkgver"

    # 安装主程序
    install -dm755 "$pkgdir/usr/share/$pkgname"
    cp -r Src Assets Translation "$pkgdir/usr/share/$pkgname/"

    # 编译 Python 字节码
    find "$pkgdir/usr/share/$pkgname/Src" -name "*.py" -exec \
        python3 -m compileall {} \; 2>/dev/null || true

    # 安装启动脚本
    install -Dm755 Start.sh "$pkgdir/usr/bin/$pkgname"

    # 修改启动脚本以指向正确的路径
    sed -i "s|python3 -m Src.Main|python3 /usr/share/$pkgname/Src/Main.py|g" "$pkgdir/usr/bin/$pkgname"

    # 安装图标
    install -Dm644 "Assets/SMakeIcon256.png" \
        "$pkgdir/usr/share/pixmaps/$pkgname.png"
    install -Dm644 "Assets/SMakeIcon256.png" \
        "$pkgdir/usr/share/icons/hicolor/256x256/apps/$pkgname.png"

    # 安装桌面文件
    install -Dm644 /dev/stdin "$pkgdir/usr/share/applications/$pkgname.desktop" << 'EOF'
[Desktop Entry]
Name=JimSMake
Comment=一站式潜意识音频制作工具
Exec=jimsmake
Icon=jimsmake
Terminal=false
Type=Application
Categories=Utility
StartupNotify=true
EOF

    # 安装文档和许可证
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
    install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}
