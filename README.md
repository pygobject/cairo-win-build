# cairo-win-build

`cairo-win-build` is a companion project to the
[pycairo](https://github.com/pygobject/pycairo) Python bindings for the
[cairo graphics library](https://www.cairographics.org/). It provides a static
Windows build of cairo including all its dependencies (zlib, pixman, freetype,
expat, libpng) which pycairo uses for its binary Windows wheels.

In addition to cairo it also provides a static build of
[pkgconf](https://github.com/pkgconf/pkgconf) which is required by pycairo
during its wheel build process for locating dependencies.

The build process is based on the [meson](https://mesonbuild.com/) build system
and uses Visual Studio on GitHub Actions to automatically build and publish
everything. See the [workflow file](.github/workflows/main.yml) for details. You
can of course also build everything locally yourself, see the instructions
below.

Let us know if there is anything we can do to make things better or to cover a
wider range of use cases.

## Manual build instructions

```bash
# install meson and ninja
pip install -r requirements.txt

# build cairo
cd cairo-build
meson setup buildDir --prefix=/
meson compile -C buildDir
meson install -C buildDir --destdir ../dist
# see ./dist for the result

# build pkgconf
cd ../pkgconf-build
meson setup buildDir --prefix=/
meson compile -C buildDir
meson install -C buildDir --destdir ../dist
# see ./dist for the result
```

## Updating dependencies

All dependencies and cairo itself are included via the [meson wrap
system](https://mesonbuild.com/Wrap-dependency-system-manual.html) and we depend
on the [meson WrapDB](https://github.com/mesonbuild/wrapdb) for updates. The
following is required to pull in new versions from pypi and wrapdb:

```bash
# manually update meson/ninja in requirements.txt
pip install -r requirements.txt
# update wrap files from wrapdb
meson wrap update --sourcedir cairo-build
meson wrap update --sourcedir pkgconf-build
```

## Creating a new release

* Create a new release in the GH UI
* GHA will do the rest
