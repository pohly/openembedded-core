import bb

def bblayers_conf_file(d):
    return os.path.join(d.getVar('TOPDIR'), 'conf/bblayers.conf')

def sanity_conf_read(fn):
    with open(fn, 'r') as f:
        lines = f.readlines()
    return lines

def sanity_conf_find_line(pattern, lines):
    import re
    return next(((index, line)
        for index, line in enumerate(lines)
        if re.search(pattern, line)), (None, None))

def sanity_conf_update(fn, lines, version_var_name, new_version):
    index, line = sanity_conf_find_line(r"^%s" % version_var_name, lines)
    lines[index] = '%s = "%d"\n' % (version_var_name, new_version)
    with open(fn, "w") as f:
        f.write(''.join(lines))

def sanity_update_bblayers(d, failmsg):
    current_lconf = int(d.getVar('LCONF_VERSION'))
    lconf_version = int(d.getVar('LAYER_CONF_VERSION'))

    if not current_lconf:
        return False

    lines = []

    if current_lconf < 4:
        return False

    bblayers_fn = bblayers_conf_file(d)
    lines = sanity_conf_read(bblayers_fn)

    if current_lconf == 4 and lconf_version > 4:
        topdir_var = '$' + '{TOPDIR}'
        index, bbpath_line = sanity_conf_find_line('BBPATH', lines)
        if bbpath_line:
            start = bbpath_line.find('"')
            if start != -1 and (len(bbpath_line) != (start + 1)):
                if bbpath_line[start + 1] == '"':
                    lines[index] = (bbpath_line[:start + 1] +
                                    topdir_var + bbpath_line[start + 1:])
                else:
                    if not topdir_var in bbpath_line:
                        lines[index] = (bbpath_line[:start + 1] +
                                    topdir_var + ':' + bbpath_line[start + 1:])
            else:
                return False
        else:
            index, bbfiles_line = sanity_conf_find_line('BBFILES', lines)
            if bbfiles_line:
                lines.insert(index, 'BBPATH = "' + topdir_var + '"\n')
            else:
                return False

        current_lconf += 1
        sanity_conf_update(bblayers_fn, lines, 'LCONF_VERSION', current_lconf)
        bb.note("Your conf/bblayers.conf has been automatically updated.")
        return True

    elif current_lconf == 5 and lconf_version > 5:
        # Null update, to avoid issues with people switching between poky and other distros
        current_lconf = 6
        sanity_conf_update(bblayers_fn, lines, 'LCONF_VERSION', current_lconf)
        bb.note("Your conf/bblayers.conf has been automatically updated.")
        return True

        status.addresult()

    elif current_lconf == 6 and lconf_version > 6:
        # Handle rename of meta-yocto -> meta-poky
        # This marks the start of separate version numbers but code is needed in OE-Core
        # for the migration, one last time.
        layers = d.getVar('BBLAYERS').split()
        layers = [ os.path.basename(path) for path in layers ]
        if 'meta-yocto' in layers:
            found = False
            while True:
                index, meta_yocto_line = sanity_conf_find_line(r'.*meta-yocto[\'"\s\n]', lines)
                if meta_yocto_line:
                    lines[index] = meta_yocto_line.replace('meta-yocto', 'meta-poky')
                    found = True
                else:
                    break
            if not found:
                return False
            index, meta_yocto_line = sanity_conf_find_line('LCONF_VERSION.*\n', lines)
            if meta_yocto_line:
                lines[index] = 'POKY_BBLAYERS_CONF_VERSION = "1"\n'
            else:
                return False
            with open(bblayers_fn, "w") as f:
                f.write(''.join(lines))
            bb.note("Your conf/bblayers.conf has been automatically updated.")
            return True
        current_lconf += 1
        sanity_conf_update(bblayers_fn, lines, 'LCONF_VERSION', current_lconf)
        d.setVar('LCONF_VERSION', current_lconf)
        bb.note("Your conf/bblayers.conf has been automatically updated.")
        return True
