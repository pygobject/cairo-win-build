project('cairo-build', 'c', 'cpp',
    default_options: [
        'default_library=static',
        'buildtype=release',
        'wrap_mode=nopromote',
        'force_fallback_for=libpng,pixman,zlib',
        'cairo:glib=disabled', # doesn't build statically in Windows
        'cairo:tests=disabled', # We don't need tests
    ],
)

subproject('cairo')
