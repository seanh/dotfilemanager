#!/usr/bin/env python
"""dotfilemanager.py - a dotfiles manager script. See --help for usage
and command-line arguments.

"""
import os,sys,platform

# TODO: allow setting hostname as a command-line argument also?
try:
    HOSTNAME = os.environ['DOTFILEMANAGER_HOSTNAME']
except KeyError:
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
            target_path = os.path.abspath(os.path.expanduser(target_path))
            if not os.path.exists(target_path):                
                # This is a broken symlink.
                if report:
                    print 'tidy would delete broken symlink: %s->%s' % (path,target_path)                    
                else:
                    print 'Deleting broken symlink: %s->%s' % (path,target_path)
                    os.remove(path)                    

def get_target_paths(to_dir,report=False):
    """Return the list of absolute paths to link to for a given to_dir.
    
    This handles skipping various types of filename in to_dir and
    resolving host-specific filenames.
    
    """
    paths = []
    filenames = os.listdir(to_dir)
    for filename in filenames:
        path = os.path.join(to_dir,filename)
        if filename.endswith('~'):
            if report:
                print 'Skipping %s' % filename
            continue            
        elif (not os.path.isfile(path)) and (not os.path.isdir(path)):
            if report:
                print 'Skipping %s (not a file or directory)' % filename
            continue
        elif filename.startswith('.'):
            if report:
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
                    paths.append(path)
                else:
                    if report:
                        print 'Skipping %s (different hostname)' % filename
                    continue                    
            else:
                # This appears to be a filename without a trailing
                # hostname.
                if filename + HOSTNAME_SEPARATOR + HOSTNAME in filenames: 
                    if report:
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
    to_paths = get_target_paths(to_dir,report)
    
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
            existing_to_path = os.path.abspath(os.path.expanduser(existing_to_path))
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
                print 'link would make symlink: %s->%s' % (from_path,to_path)
            else:
                print 'Making symlink %s->%s' % (from_path,to_path)
                os.symlink(to_path,from_path)

def usage():
    return """Usage:

dotfilemanager link|tidy|report [FROM_DIR [TO_DIR]]
    
Commands:
   link -- make symlinks in FROM_DIR to files and directories in TO_DIR
   tidy -- remove broken symlinks from FROM_DIR
   report -- report on symlinks in FROM_DIR and files and directories in TO_DIR
   
FROM_DIR defaults to ~ and TO_DIR defaults to ~/.dotfiles.
   """


def main():
    try:
        ACTION = sys.argv[1]
    except IndexError:
        print usage()
        sys.exit(2)

    try:
        FROM_DIR = sys.argv[2]
    except IndexError:
        FROM_DIR = '~'
    FROM_DIR = os.path.abspath(os.path.expanduser(FROM_DIR))

    if not os.path.isdir(FROM_DIR):
        print "FROM_DIR %s is not a directory!" % FROM_DIR
        print usage()
        sys.exit(2)

    if ACTION == 'tidy':
        tidy(FROM_DIR)
    else:

        try:
            TO_DIR = sys.argv[3]
        except IndexError:
            TO_DIR = os.path.join('~','.dotfiles')
        TO_DIR = os.path.abspath(os.path.expanduser(TO_DIR))

        if not os.path.isdir(TO_DIR):
            print "TO_DIR %s is not a directory!" % TO_DIR
            print usage()
            sys.exit(2)

        if ACTION == 'link':
            link(FROM_DIR,TO_DIR)
        elif ACTION == 'report':
            link(FROM_DIR,TO_DIR,report=True)
            tidy(FROM_DIR,report=True)
        else:
            print usage()
            sys.exit(2)


if __name__ == "__main__":
    main()
