[![Latest Version](https://pypip.in/version/dotfilemanager/badge.svg)](https://pypi.python.org/pypi/dotfilemanager/)
[![Downloads](https://pypip.in/download/dotfilemanager/badge.svg)](https://pypi.python.org/pypi/dotfilemanager/)
[![Supported Python versions](https://pypip.in/py_versions/dotfilemanager/badge.svg)](https://pypi.python.org/pypi/dotfilemanager/)
[![Development Status](https://pypip.in/status/dotfilemanager/badge.svg)](https://pypi.python.org/pypi/dotfilemanager/)
[![License](https://pypip.in/license/dotfilemanager/badge.svg)](https://pypi.python.org/pypi/dotfilemanager/)

dotfilemanager.py
=================

A dotfiles manager script.

This is similar to [Steve Kemp's dotfile manager][] but I rewrote it in
Python and tweaked the behaviour a bit.

[Steve Kemp's dotfile manager]: http://blog.steve.org.uk/i_ve_got_a_sick_friend__i_need_her_help_.html


Requirements
------------

Python 2.7. It might work (or could easily be made to work) with 2.6 and 3.x
as well but I haven't tried.


Installation
------------

    pip install dotfilemanager


Usage
-----

`dotfilemanager link` Make a symlink in your homedir to each top-level
file and directory in `~/.dotfiles`.

`dotfilemanager tidy` Delete any broken symlinks in your homedir.

`dotfilemanager report` Report on what link or tidy would do, but don't
actually create or delete any symlinks.

Optionally you can specify the directories to link from and to as 
arguments, usage:

    dotfilemanager link|tidy|report [FROM_DIR [TO_DIR]]

* * *

The idea is that you have some folder called the `TO_DIR` (defaults to
`~/.dotfiles`), where you move all the dotfiles that you want to manage,
e.g.

    ~/.dotfiles/
    ~/.dotfiles/_muttrc
    ~/.dotfiles/_nanorc
    ...

You can backup and synchronise this directory between multiple hosts
using rsync, unison, a version-control system, Dropbox, or whatever you
want. When you run `dotfilemanager link` it will create symlinks in a
folder called the `FROM_DIR` (defaults to `~`), e.g.

    ~/.muttrc -> ~/.dotfiles/_muttrc 
    ~/.nanorc -> ~/.dotfiles/_nanorc
    ...

Leading underscores in the filenames in `TO_DIR` will be converted to
leading dots for the symlinks. You can also link files without leading
underscores, and you can link directories too, just place them in
`TO_DIR` and run `dotfilemanager link`.

Per-host configuration is supported by putting `__hostname` at the end
of file and directory names in `TO_DIR`. For example if `TO_DIR`
contains files named:

    _muttrc
    _muttrc__kisimul
    _muttrc__dulip
    
Then on the host dulip a symlink `FROM_DIR/.muttrc` will be created to
`TO_DIR/_muttrc__dulip`. On a host named kisimul `_muttrc__kisimul` will be
linked to. On other hosts `_muttrc` will be linked to.

(To discover the hostname of your machine run `uname -n`.)

Tip: handle directories like `~/.config` separately
-------------------------------------------------

On my system a lot of config files are stored in `~/.config`. I want to
manage some of the files in `~/.config` but not all of them. I have
host-specific versions of some files in `~/.config` but not others. I
wouldn't want to move `~/.config` to `~/.dotfiles/_config` and have
dotfilemanager make a symlink `~/.config -> ~/.dotfiles/_config` because
that would be putting _all_ the files in `~/.config` into `~/.dotfiles`,
and dotfilemanager would make the same symlink for every host, if I
wanted a host-specific version of a file in `~/.config` I'd have to put
_another_ complete copy of the directory into `~/.dotfiles` with a
`__hostname` at the end.

What you can do instead is have a `~/config` directory separate from
`~/.dotfiles`, move the files from `~/.config` that you want to manage
into `~/config`, make host-specific versions if you want, then run both
commands:

    dotfilemanager.py link ~ ~/.dotfiles
    dotfilemanager.py link ~/.config ~/config

Tip: override hostname with `DOTFILEMANAGER_HOSTNAME` environment variable
------------------------------------------------------------------------

If the `DOTFILEMANAGER_HOSTNAME` environment variable is set then it is
used instead of your real hostname to resolve hostname-specific files in
`TO_DIR`.  This is useful for accounts on networked systems where you
login to the same user account from different computers, the system
hostname will be different each time you switch computers but you want
to use the same config files whenever you login to this account. So just
make up a name for the account and set it as the value of
`DOTFILEMANAGER_HOSTNAME`.
