#!/usr/bin/env python
"""dotfilemanager.py - a dotfiles manager script. See --help for usage
and command-line arguments.

The idea is that you have some folder called the TO_DIR (defaults to
~/.dotfiles), where you move all the dotfiles that you want to manage,
e.g.

    ~/.dotfiles/
    ~/.dotfiles/_muttrc
    ~/.dotfiles/_nanorc
    ...

You can backup and synchronise this directory between multiple hosts
using rsync, unison, a version-control system, Dropbox, or whatever you
want. When you run `dotfilemanager link` it will create symlinks in a
folder called the FROM_DIR (defaults to ~), e.g.

    ~/.muttrc -> ~/.dotfiles/_muttrc 
    ~/.nanorc -> ~/.dotfiles/_nanorc
    ...

Leading underscores in the filenames in TO_DIR will be converted to
leading dots for the symlinks. You can also link files without leading
underscores, and you can link directories too, just place them in TO_DIR
and run `dotfilemanager link`.

Per-host configuration is supported by putting __hostname at the end of
file and directory names in TO_DIR. For example if TO_DIR contains files
named:

    _muttrc
    _muttrc__kisimul
    _muttrc__dulip
    
Then on the host dulip a symlink FROM_DIR/.muttrc will be created to
TO_DIR/_muttrc__dulip. On a host named kisimul _muttrc__kisimul will be
linked to. On other hosts _muttrc will be linked to.

(To discover the hostname of your machine run `uname -n`.)

`dotfilemanager tidy` will remove any dangling symlinks in FROM_DIR, and
`dotfilemanager report` will just report on what link or tidy would do
without actually making any changes to the filesystem.

Tip: handle directories like ~/.config separately
-------------------------------------------------

On my system a lot of config files are stored in ~/.config. I want to
manage some of the files in ~/.config but not all of them. I have
host-specific version of some files in ~/.config but not others. I
wouldn't want to move ~/.config to ~/.dotfiles/_config and have
dotfilemanager.py make a symlink ~/.config -> ~/.dotfiles/_config
because that would be putting _all_ the files in ~/config into
~/.dotfiles, and dotfilemanager.py would make the same symlink for every
host, if I wanted a host-specific version of ~/.config I'd have to put
_another_ complete copy of the directory into ~/.dotfiles with a
__hostname at the end.

What you can to do is have a ~/config directory separate from
~/.dotfiles, move the files from ~/.config that you want to manage into
~/config, make host-specific versions if you want, then run both
commands:

    dotfilemanager.py link ~ ~/.dotfiles
    dotfilemanager.py link ~/.config ~/config

TODO
----

Support hostname as a command-line argument, overriding the system
hostname. This might be useful for accounts on networked systems where
you login to the same user account from different computers, the system
hostname will be different each time you switch computers but you want
to use the same config files whenever you login to this account. So just
make up a name for the account and pass it as a command-line argument
overriding the system hostname.

"""
import os,sys,platform

HOSTNAME = platform.node()
HOSTNAME_SEPARATOR = '__'
    
def tidy(d,report=False):
    """Find and delete any broken symlinks in directory d.
    
    Arguments:
    d -- The directory to consider (absolute path)
    
    Keyword arguments:
    report -- If report is True just report on what broken symlinks are
              found, don't attempt to delete them (default: False)
    
    """
    for f in os.listdir(d):
        path = os.path.join(d,f)
        if os.path.islink(path):
            target_path = os.readlink(path)            
            if not os.path.isabs(target_path):
                # This is a relative symlink, resolve it.
                target_path = os.path.join(os.path.dirname(path),target_path)             
            if not os.path.exists(target_path):                
                # This is a broken symlink.
                if report:
                    print 'Broken symlink will be deleted: %s->%s' % (path,target_path)                    
                else:
                    print 'Deleting broken symlink: %s->%s' % (path,target_path)
                    os.remove(path)                    

def get_target_paths(to_dir):
    """Return the list of absolute paths to link to for a given to_dir.
    
    This handles skipping various types of filename in to_dir and
    resolving host-specific filenames.
    
    """
    paths = []
    filenames = os.listdir(to_dir)
    for filename in filenames:
        path = os.path.join(to_dir,filename)
        if filename.endswith('~'):
            print 'Skipping %s' % filename
            continue            
        elif (not os.path.isfile(path)) and (not os.path.isdir(path)):
            print 'Skipping %s (not a file or directory)' % filename
            continue
        elif filename.startswith('.'):
            print 'Skipping %s (filename has a leading dot)' % filename
            continue
        else:
            if HOSTNAME_SEPARATOR in filename:
                # This appears to be a filename with a trailing
                # hostname, e.g. _muttrc__dulip. If the trailing
                # hostname matches the hostname of this host then we
                # link to it.
                hostname = filename.split(HOSTNAME_SEPARATOR)[-1]
                if hostname == HOSTNAME:
                    path = os.path.join(to_dir,filename)
                    paths.append(path)
                else:
                    print 'Skipping %s (different hostname)' % filename
                    continue                    
            else:
                # This appears to be a filename without a trailing
                # hostname.
                if filename + HOSTNAME_SEPARATOR + HOSTNAME in filenames: 
                    print 'Skipping %s (there is a host-specific version of this file for this host)' % filename
                    continue
                else:                                            
                    paths.append(path)    
    return paths

def link(from_dir,to_dir,report=False):
    """Make symlinks in from_dir to each file and directory in to_dir.

    This handles converting leading underscores in to_dir to leading
    dots in from_dir.
    
    Arguments:
    from_dir -- The directory in which symlinks will be created (string,
                absolute path)
    to_dir   -- The directory containing the files and directories that
                will be linked to (string, absolute path)
    
    Keyword arguments:
    report   -- If report is True then only report on the status of
                symlinks in from_dir, don't actually create any new
                symlinks (default: False)
    
    """
    # The paths in to_dir that we will be symlinking to.
    to_paths = get_target_paths(to_dir)
    
    # Dictionary of symlinks we will be creating, from_path->to_path
    symlinks = {}
    for to_path in to_paths:
        to_directory, to_filename = os.path.split(to_path)
        # Change leading underscores to leading dots.        
        if to_filename.startswith('_'):
            from_filename = '.' + to_filename[1:]
        else:
            from_filename = to_filename
        # Remove hostname specifiers.
        parts = from_filename.split(HOSTNAME_SEPARATOR)
        assert len(parts) == 1 or len(parts) == 2
        from_filename = parts[0]
        from_path = os.path.join(from_dir,from_filename)        
        symlinks[from_path] = to_path

    # Attempt to create the symlinks that don't already exist.
    for from_path,to_path in symlinks.items():                        
        # Check that nothing already exists at from_path.
        if os.path.islink(from_path):
            # A link already exists.
            existing_to_path = os.readlink(from_path) 
            if  existing_to_path == to_path:
                # It's already a link to the intended target. All is
                # well.
                continue
            else:
                # It's a link to somewhere else.
                print from_path+" => is already symlinked to "+existing_to_path
        elif os.path.isfile(from_path):
            print "There's a file in the way at "+from_path
        elif os.path.isdir(from_path):
            print "There's a directory in the way at "+from_path
        elif os.path.ismount(from_path):
            print "There's a mount point in the way at "+from_path
        else:
            # The path is clear, make the symlink.
            if report:
                print 'A symlink will be made: %s->%s' % (from_path,to_path)
            else:
                print 'Making symlink %s->%s' % (from_path,to_path)
                os.symlink(to_path,from_path)

def usage():
    return """Usage:

makelinks link|tidy|report [FROM_DIR [TO_DIR]]
    
Commands:
   link -- make symlinks in FROM_DIR to files and directories in TO_DIR
   tidy -- remove broken symlinks from FROM_DIR
   report -- report on symlinks in FROM_DIR and files and directories in TO_DIR
   
FROM_DIR defaults to ~ and TO_DIR defaults to ~/.dotfiles.
   """

if __name__ == "__main__":
    try:
        ACTION = sys.argv[1]
    except IndexError:
        print usage()
        sys.exit(2)
    try:
        FROM_DIR = sys.argv[2]
    except IndexError:
        FROM_DIR = os.path.expanduser('~')
    if not os.path.isdir(FROM_DIR):
        print "FROM_DIR %s is not a directory!" % FROM_DIR
        print usage()
        sys.exit(2)
    try:
        TO_DIR = sys.argv[3]
    except IndexError:
        TO_DIR = os.path.join(os.path.expanduser('~'),'.dotfiles')
    if not os.path.isdir(TO_DIR):
        print "TO_DIR %s is not a directory!" % TO_DIR
        print usage()
        sys.exit(2)

    if ACTION == 'link':
        link(FROM_DIR,TO_DIR)
    elif ACTION == 'tidy':
        tidy(FROM_DIR)
    elif ACTION == 'report':
        link(FROM_DIR,TO_DIR,report=True)
        tidy(FROM_DIR,report=True)
    else:
        print usage()
        sys.exit(2)
