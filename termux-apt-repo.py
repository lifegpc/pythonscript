#!/usr/bin/env python3

import datetime, hashlib, os, re, shutil, subprocess, sys, glob, argparse

COMPONENTS = []
supported_arches = ['all', 'arm', 'i686', 'aarch64', 'x86_64']
encountered_arches = set()
hashes = ['md5', 'sha1', 'sha256', 'sha512']

def get_package_name(filename):
    # Expects the 'name_version_arch.deb' naming scheme.
    return filename.split('_')[0]

def run_shell_command(cmd):
    print(cmd)
    try:
        return subprocess.check_output(["cmd", "/C", cmd], shell=True).strip()
    except subprocess.CalledProcessError:
        return None

def control_file_contents(debfile):
    file_list = run_shell_command("ar t {}".format(debfile))
    if file_list is None:
        sys.exit("Error listing contents of '{}'".format(debfile))
    
    file_list = file_list.decode().split("\r\n")
    print(file_list)

    if "control.tar.gz" in file_list:
        control_filename = "control.tar.gz"
        tar_args = "-z"
    elif "control.tar.xz" in file_list:
        control_filename = "control.tar.xz"
        tar_args = "-J"
    else:
        sys.exit("Failed to find control file in '{}'".format(debfile))

    re = run_shell_command("7z x {} {}".format(debfile, control_filename))
    if re is None:
        sys.exit(-1)
    contents = run_shell_command("tar -O {} -xf {} ./control".format(tar_args, control_filename))
    os.remove(control_filename)
    if contents is None:
        sys.exit("Error extracting control file from '{}'".format(debfile))
    
    return contents

def list_package_files(debfile):
    run_shell_command("7z x -y " + debfile + " data.tar.xz")
    all_content = run_shell_command("bsdtar -tJf data.tar.xz").decode()
    os.remove('data.tar.xz')
    return [files.strip("./") for files in all_content.splitlines() if not files[-1] == "/"]

def add_deb(deb_to_add_path, component, use_hard_links):
    deb_to_add_control_file = control_file_contents(deb_to_add_path).decode()
    print(deb_to_add_control_file)
    deb_to_add_pkg_name = re.search('Package: (.*)', deb_to_add_control_file).group(1)
    deb_to_add_pkg_version = re.search('Version: (.*)', deb_to_add_control_file).group(1)
    deb_arch = re.search('Architecture: (.*)', deb_to_add_control_file).group(1)

    if not deb_arch in supported_arches:
        sys.exit('Unsupported arch "' + deb_arch + '" in ' + os.path.basename(deb_to_add_path))
    encountered_arches.add(deb_arch)

    package_name = get_package_name(os.path.basename(deb_to_add_path))
    arch_dir_path = os.path.join(distribution_path, component, 'binary-' + deb_arch)

    if not os.path.isdir(arch_dir_path):
        os.makedirs(arch_dir_path)

    # Add .deb file:
    print('Adding deb file: ' + os.path.basename(deb_to_add_path) + '...')
    dest_deb_dir_path = os.path.join(distribution_path, component, 'binary-' + deb_arch)
    if not os.path.isdir(dest_deb_dir_path): os.makedirs(dest_deb_dir_path)
    destination_deb_file = os.path.join(dest_deb_dir_path, os.path.basename(deb_to_add_path))

    if use_hard_links:
        os.link(deb_to_add_path, destination_deb_file)
    else:
        shutil.copy2(deb_to_add_path, destination_deb_file)

    with open(os.path.join(distribution_path, component, 'Contents-' + deb_arch), 'a') as contents_file:
        for f in list_package_files(destination_deb_file):
            print("%-80s %s" % (f, deb_to_add_pkg_name), file=contents_file)

parser = argparse.ArgumentParser(description='Create a repository with deb files')
parser.add_argument('input', metavar='input', type=str,
                    help='folder where .deb files are located')
parser.add_argument('output', metavar='output', type=str,
                    help='folder with repository tree')
parser.add_argument('distribution', metavar='dist', type=str, nargs='?', default='termux',
                    help='name of distribution folder. deb files are put into output/dists/distribution/component/binary-$ARCH/')
parser.add_argument('component', metavar='comp', type=str, nargs='?', default='extras',
                    help='name of component folder. deb files are put into output/dists/distribution/component/binary-$ARCH/')
parser.add_argument('--use-hard-links', default=False, action='store_true',
                    help='use hard links instead of copying deb files. Will not work on an android device')

args = parser.parse_args()
input_path = args.input
output_path = args.output
DISTRIBUTION = args.distribution
default_component = args.component
use_hard_links = args.use_hard_links
distribution_path = os.path.join(output_path, 'dists', DISTRIBUTION)

if not os.path.isdir(input_path):
    sys.exit("'" + input_path + '" does not exist')

debs_in_path = glob.glob(os.path.join(input_path, "*.deb"))
debs_in_path += glob.glob(os.path.join(input_path, "*/*.deb"))
if not debs_in_path:
    sys.exit('No .deb file found in ' + input_path)
else:
    for deb_path in sorted(debs_in_path):
        component = os.path.dirname(os.path.relpath(deb_path, input_path))
        if not component:
            component = default_component
        if component not in COMPONENTS:
            COMPONENTS.append(component)
            if os.path.isdir(os.path.join(distribution_path, component)):
                shutil.rmtree(os.path.join(distribution_path, component))
            os.makedirs(os.path.join(distribution_path, component))

        add_deb(deb_path, component, use_hard_links)

# See https://wiki.debian.org/RepositoryFormat#A.22Release.22_files for format:
release_file_path = distribution_path + '/Release'
release_file = open(release_file_path, 'w')
print("Codename: termux", file=release_file)
print("Version: 1", file=release_file)
print("Architectures: " + ' '.join(encountered_arches), file=release_file)
print("Description: " + DISTRIBUTION + " repository", file=release_file)
print("Suite: " + DISTRIBUTION, file=release_file)
print("Date: " + datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S UTC'), file=release_file)

# Create Packages files:
for component in COMPONENTS:
    for arch_dir_path in glob.glob(os.path.join(distribution_path, component, 'binary-*')):
        arch = os.path.basename(arch_dir_path).split('-')[1]
        print('Creating package file for ' + component + " and " + arch + '...')
        packages_file_path = arch_dir_path + '/Packages'
        packagesxz_file_path = packages_file_path + '.xz'
        binary_path = 'binary-' + arch
        with open(packages_file_path, 'w') as packages_file:
            for deb_to_read_path in sorted(glob.glob(os.path.join(arch_dir_path, "*.deb"))):
                # Extract the control file from the .deb:
                scanpackages_output = control_file_contents(deb_to_read_path).decode()
                package_name = re.search('Package: (.*)', scanpackages_output).group(1)
                package_arch = re.search('Architecture: (.*)', scanpackages_output).group(1)
                # Add these fields which dpkg-scanpackages would have done:
                scanpackages_output += '\nFilename: ' + os.path.join('dists', DISTRIBUTION, component, binary_path, os.path.basename(deb_to_read_path)).replace('\\', '/')
                scanpackages_output += '\nSize: ' + str(os.stat(deb_to_read_path).st_size)
                for hash in hashes:
                    if hash == "md5":
                        hash_string = hash.upper()+'Sum'
                    else:
                        hash_string = hash.upper()
                    scanpackages_output += '\n'+hash_string + ': ' + getattr(hashlib, hash)(open(deb_to_read_path, 'rb').read()).hexdigest()
                print(scanpackages_output, file=packages_file)
                print('', file=packages_file)
        # Create Packages.xz
        run_shell_command('xz -9 --keep ' + packages_file_path)
    for contents_file in glob.glob(os.path.join(distribution_path, component, 'Contents-*')):
        run_shell_command('xz -9 --keep ' + contents_file)

# Get components in output folder, we might have more folders than we are adding now
COMPONENTS = [d for d in os.listdir(distribution_path) if os.path.isdir(os.path.join(distribution_path, d))]
for hash in hashes:
    if hash == 'md5':
        hash_string = hash.upper()+'Sum'
    else:
        hash_string = hash.upper()
    print(hash_string + ':', file=release_file)

    for component in COMPONENTS:
        for arch_dir_path in glob.glob(os.path.join(distribution_path, component, 'binary-*')):
            # Write info about Packages and Packages.xz to Release file:
            for f in ['Packages', 'Packages.xz']:
                print(' '+' '.join([getattr(hashlib, hash)(open(os.path.join(arch_dir_path, f), 'rb').read()).hexdigest(),
                                    str(os.stat(os.path.join(arch_dir_path, f)).st_size),
                                    os.path.join(component, os.path.basename(arch_dir_path), f).replace('\\', '/')])
                      , file=release_file)
        # Write info about Contents and Contents.gz to Release file:
        for contents_file in glob.glob(os.path.join(distribution_path, component, 'Contents-*')):
            print(' '+' '.join([getattr(hashlib, hash)(open(contents_file, 'rb').read()).hexdigest(),
                                str(os.stat(contents_file).st_size), os.path.relpath(contents_file, distribution_path).replace('\\', '/')])
                  , file=release_file)
release_file.close()

if True:
    print('Signing with gpg...')
    run_shell_command('gpg --yes --digest-algo SHA256 --clearsign -o '
        + distribution_path + '/InRelease ' + distribution_path + '/Release')

print('Done!')
print('')
print('Make the ' + output_path + ' directory accessible at $REPO_URL')
print('')
print('Users can then access the repo by adding a file at')
print('   $PREFIX/etc/apt/sources.list.d')
print('containing:')
for component in COMPONENTS:
    print('   deb [trusted=yes] $REPO_URL '+DISTRIBUTION+' '+component)
print('')
print('[trusted=yes] is not needed if the repo has been signed with a gpg key')
