#!/usr/bin/env python
from distutils.core import setup

DESCRIPTION = (
        "Togepy is a collection of tools to assist with developing games\n"
        "under python. It is intended to be used with the game programming\n"
        "library pyglet (http://www.pyglet.org) and provides a number of\n"
        "useful extensions to its API."
)

METADATA = {
    "name"             : "togepy",
    "version"          : "0.1",
    "license"          : "BSD",
    "url"              : "",
    "author"           : "Adam Biltcliffe, Martin O'Leary, Richard Thomas",
    "author_email"     : "",
    "description"      : "Tools for Game Engines in Python",
    "long_description" : DESCRIPTION,
}

PACKAGEDATA = {
    "packages"         : ["togepy"],
    "package_dir"      : {
                            "togepy"      : "togepy",
                         },
    "package_data"     : {
                            "togepy"      : "../html",
                         },
}

PACKAGEDATA.update(METADATA)
setup(**PACKAGEDATA)
