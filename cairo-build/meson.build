project('cairo-build', 'c', 'cpp',
    default_options: [
        'default_library=static',
        'buildtype=release',
        'wrap_mode=nopromote',
        'force_fallback_for=expat,freetype2,libpng,pixman,zlib',
        'cairo:tee=enabled', # this is needed for pycairo tests to pass
        'cairo:glib=disabled', # doesn't build statically in Windows
        'cairo:tests=disabled', # We don't need tests
    ],
)

subproject('cairo')
