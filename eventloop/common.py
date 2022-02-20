import os
import glob

def debug_print_on(*args):
    print(*args)

def debug_print_off(*args):
    pass

if 'DEBUG_EVENTLOOP' in os.environ and os.environ['DEBUG_EVENTLOOP'] == "1":
    debug_print = debug_print_on
else:
    debug_print = debug_print_off

def path_matches(path, include, exclude):
    name = os.path.basename(path)
    if include is not None and len(include) > 0:
        ok = False
        for pat in include:
            if glob.fnmatch.fnmatch(name, pat) or glob.fnmatch.fnmatch(path, pat):
                ok = True
                break
        if not ok:
            return False
    if exclude is not None:
        for pat in exclude:
            if glob.fnmatch.fnmatch(name, pat) or glob.fnmatch.fnmatch(path, pat):
                return False
    return True

def walk(path, include, exclude, all_dirs = False, recursive=True):
    """
    Examples:
        return only cpp files that don't start with moc_:
            include = ["*.cpp"] exclude = ["moc_*"]
        return all files and directories but .git and node_modules:
            include = [] exclude = [".git", "node_modules"]
        return all files and directories:
            include = [] exclude = []
    Initial path is not checked and always returned.
    """

    if glob.has_magic(path):
        paths = glob.glob(path)
    else:
        paths = [path]

    queue = []
    dirs = []
    files = []

    for path in paths:
        if os.path.isfile(path):
            files.append(path)
        else:
            dirs.append(path)
            queue.append(path)

    while len(queue) > 0:
        path = queue.pop(0)
        try:
            for n in os.listdir(path):
                path_ = os.path.join(path, n)
                is_dir = os.path.isdir(path_)
                if path_matches(path_, include, exclude):
                    if is_dir:
                        dirs.append(path_)
                        queue.append(path_)
                    else:
                        files.append(path_)
                elif all_dirs and is_dir:
                    dirs.append(path_)
                if is_dir and recursive:
                    queue.append(path_)
        except PermissionError as e:
            debug_print(e)
        except FileNotFoundError as e:
            debug_print(e)
        except NotADirectoryError as e:
            debug_print(e)
    return dirs, files

(
    EVENT_RENAME,
    EVENT_CHANGE
) = range(2)

