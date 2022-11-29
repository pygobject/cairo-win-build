import logging
import os
import re
import shutil
import struct
import subprocess
import sys
import typing as T
import argparse

from pathlib import Path

DEFAULT_PREFIX = Path("C:/prefix") if sys.platform == "win32" else sys.prefix

log = logging.getLogger(__name__)
ENVIRON = os.environ.copy()


def get_python_arch() -> int:
    return struct.calcsize("P") * 8


def run_command(
    args: T.List[str],
    env: T.Dict[str, str] = ENVIRON,
    cwd: T.Optional[T.Union[str, Path]] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    kwargs = {"check": check}
    if env:
        kwargs["env"] = env
    if cwd:
        kwargs["cwd"] = cwd

    return subprocess.run(args, **kwargs)


def get_meson_executable(build_dir) -> Path:
    def create_venv_and_install_meson(venv_location: Path) -> None:
        log.info("Creating a venv at %s", venv_location.absolute())
        run_command(
            [
                sys.executable,
                "-m",
                "venv",
                os.fspath(venv_location),
            ]
        )
        log.info("Installing meson and ninja using pip")
        if (venv_location / "Scripts").is_dir():
            python = venv_location / "Scripts" / "python"
        else:
            python = venv_location / "bin" / "python"
        run_command(
            [
                os.fspath(python),
                "-m",
                "pip",
                "install",
                "ninja",
                "meson",
            ],
            env=ENVIRON,
        )

    log.info("Checking if meson and ninja are installed")
    meson = shutil.which("meson")
    ninja = shutil.which("ninja")
    if meson is None or ninja is None:
        log.warning("Meson or Ninja isn't installed. Installing using an Venv.")
        venv_location = build_dir / "meson_venv"
        ENVIRON[
            "PATH"
        ] = f"{(venv_location / 'Scripts').absolute()}{os.pathsep}{(venv_location / 'bin').absolute()}{os.pathsep}{ENVIRON['PATH']}"  # noqa
        if not venv_location.exists():
            create_venv_and_install_meson(venv_location)
        else:
            log.info("Venv already exists. Checking if it is usable.")
            ninja = shutil.which("ninja", path=ENVIRON["PATH"])
            meson = shutil.which("meson", path=ENVIRON["PATH"])
            if meson is None or ninja is None:
                log.info("Creating new venv.")
                create_venv_and_install_meson(venv_location)
    ninja = shutil.which("ninja", path=ENVIRON["PATH"])
    meson = shutil.which("meson", path=ENVIRON["PATH"])
    log.info("Found meson at %s", meson)
    log.info("Found ninja at %s", ninja)
    return meson


def run_meson(meson_args, **kwargs):
    log.info("Running meson with arguments: %s", " ".join(meson_args))
    run_command(meson_args, **kwargs)


def build_pkgconf(
    arch: int = get_python_arch(),
    build_dir: T.Optional[Path] = None,
    prefix: Path = None,
    build_type: str = "static",
):
    log.info("Building Pkgconf")
    if build_dir is None:
        build_dir = Path(f"./build-pkgconf-x{arch}")
    if build_dir.exists():
        log.info("%s exists. Skipping build.", build_dir.absolute())
        return
    build_dir.mkdir()
    log.info("Using %s as build directory.", build_dir.absolute())

    if prefix is None:
        if sys.platform == "win32":
            prefix = Path(rf"C:\build-x{arch}")
        else:
            prefix = Path(f"~/build-x{arch}")
    log.info("Using %s as prefix", prefix)

    root_dir = Path(__file__).parent / "pkgconf-build"

    meson = get_meson_executable(build_dir)

    meson_build_dir = (root_dir / f"build-x{arch}").absolute()
    if meson_build_dir.exists():
        shutil.rmtree(meson_build_dir)

    log.info("Configuring using Meson...")
    run_meson(
        [
            meson,
            "setup",
            os.fspath(meson_build_dir),
            f"--default-library={build_type}",
            f"--prefix={prefix}",
        ],
        cwd=root_dir,
        env=ENVIRON,
    )

    log.info("Compiling now...")
    run_meson(
        [meson, "compile", "-C", os.fspath(meson_build_dir)],
        cwd=root_dir,
    )

    log.info("Installing Pkgconf...")
    run_meson(
        [
            meson,
            "install",
            "--no-rebuild",
            "-C",
            os.fspath(meson_build_dir),
        ]
    )

    log.info("Sucessfully build Pkgconf")


def build_cairo(
    arch: int = get_python_arch(),
    build_dir: T.Optional[Path] = None,
    prefix: Path = None,
    build_type: str = "static",
):
    log.info("Buidling Cairo")
    if build_dir is None:
        build_dir = Path(f"./build-cairo-x{arch}")
    if not build_dir.exists():
        build_dir.mkdir()
    log.info("Using %s as build directory.", build_dir.absolute())

    if prefix is None:
        if sys.platform == "win32":
            prefix = Path(rf"C:\build-x{arch}")
        else:
            prefix = Path(f"~/build-x{arch}")
    log.info("Using %s as prefix", prefix)

    meson = get_meson_executable(build_dir)

    root_dir = Path(__file__).parent / "cairo-build"
    meson_build_dir = (root_dir / f"build-x{arch}").absolute()
    if meson_build_dir.exists():
        shutil.rmtree(meson_build_dir)

    # Static build is broken with Meson on Windows without these CFLAGS
    # See https://gitlab.freedesktop.org/cairo/cairo/-/issues/461
    # if sys.platform == "win32":
    #    ENVIRON["CFLAGS"] = "-DCAIRO_WIN32_STATIC_BUILD -DXML_STATIC"

    # Just so that meson doesn't try to link with system
    # stuff.
    ENVIRON["PKG_CONFIG_PATH"] = ""
    ENVIRON["PKG_CONFIG"] = "invalid-executable"

    run_meson(
        [
            meson,
            "setup",
            os.fspath(meson_build_dir),
            f"--default-library={build_type}",
            f"--prefix={prefix}"
        ],
        cwd=root_dir,
        env=ENVIRON,
    )

    log.info("Compiling now...")
    run_meson(
        [meson, "compile", "-C", os.fspath(meson_build_dir)]
    )

    log.info("Installing Cairo.")
    run_meson(
        [
            meson,
            "install",
            "--no-rebuild",
            "-C",
            os.fspath(meson_build_dir),
        ]
    )

    # On MSVC, meson would create static libraries as
    # libcairo.a but setuptools doens't know about it.
    # So, we are copying every lib*.a to *.lib so that
    # setuptools can use it.
    if build_type == "static":
        libreg = re.compile(r"lib(?P<name>\S*)\.a")
        libdir = prefix / "lib"
        for lib in libdir.glob("lib*.a"):
            name = libreg.match(lib.name).group("name") + ".lib"
            shutil.copyfile(lib, libdir / name)

    log.info("Sucessfully build Cairo")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--build-dir",
        required=False,
        type=Path,
        help="Build directory. (default: ./build*)",
    )
    parser.add_argument(
        "--prefix",
        default=DEFAULT_PREFIX,
        type=Path,
        help=f"Installation prefix. (default: {DEFAULT_PREFIX})",
    )
    parser.add_argument(
        "--arch",
        default=get_python_arch(),
        help=f"Arch to build. (default: {get_python_arch()})",
        type=int,
    )
    parser.add_argument(
        "--build-pkgconf",
        action=argparse.BooleanOptionalAction,
        help="Whether to build pkgconf. (default: False)",
        dest="build_pkgconf"
    )
    parser.add_argument(
        "--build-cairo",
        action=argparse.BooleanOptionalAction,
        help="Whether to build cairo. (default: True)",
        dest="build_cairo",
        default=True
    )
    op = parser.parse_args()
    if op.build_pkgconf:
        build_pkgconf(
            arch=op.arch,
            build_dir=op.build_dir,
            prefix=op.prefix.absolute(),
        )
    if op.build_cairo:
        build_cairo(
            arch=op.arch,
            build_dir=op.build_dir,
            prefix=op.prefix.absolute(),
        )
