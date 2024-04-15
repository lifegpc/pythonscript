from argparse import ArgumentParser
from os.path import isabs, join, abspath, dirname, exists, isdir, basename
from os import listdir, makedirs, remove
from typing import List
import uuid
from xml.sax.saxutils import escape
from math import floor
from base64 import b64encode
from subprocess import run
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
try:
    import fontforge
    have_fontforge = True
except ImportError:
    have_fontforge = False


p = ArgumentParser()
p.add_argument('input', help='Input config file', nargs='+', type=str)


def get_path(path: str, input: str):
    if isabs(path):
        return path
    return abspath(join(input, path))


def get_input(input: str, input_dir: str, temp_dir: str) -> List[str]:
    dinput = get_path(input, input_dir)
    if not exists(dinput):
        raise FileNotFoundError(dinput)
    if isdir(dinput):
        files = listdir(dinput)
        output = []
        for file in files:
            output.extend(get_input(join(input, file), input_dir, temp_dir))
        return output
    linput = input.lower()
    if linput.endswith('.ttf') or linput.endswith('.otf'):
        return [dinput]
    if linput.endswith('.ttc'):
        if not have_fontforge:
            print('FontForge is not installed, skipping', dinput)
            return []
        fonts = fontforge.fontsInFile(dinput)
        paths = []
        for i in fonts:
            font_path = get_path(f"{i}.ttf", temp_dir)
            if not exists(font_path):
                font = fontforge.open(f"{dinput}({i})")
                font.generate(font_path)
                font.close()
            paths.append(font_path)
        return paths
    return []


def replace(m):
    return "-".join([m.group(1), m.group(2), '5' + m.group(3),
                     '8' + m.group(5), m.group(5)])


def main(args=None):
    args = p.parse_args(args)
    for input in args.input:
        with open(input, 'r', encoding='UTF-8') as f:
            config = load(f, Loader=Loader)
        input_dir = dirname(input)
        temp_dir = 'tmp'
        if 'temp_dir' in config and config['temp_dir']:
            temp_dir = config['temp_dir']
        temp_dir = get_path(temp_dir, input_dir)
        output = 'output.mobileconfig'
        if 'output' in config and config['output']:
            output = config['output']
        output = get_path(output, input_dir)
        if 'cert_file' not in config or not config['cert_file']:
            raise ValueError('cert_file is required')
        cert_file = get_path(config['cert_file'], input_dir)
        if not exists(cert_file):
            raise FileNotFoundError(cert_file)
        if 'chain_file' not in config or not config['chain_file']:
            raise ValueError('chain_file is required')
        chain_file = get_path(config['chain_file'], input_dir)
        if not exists(chain_file):
            raise FileNotFoundError(chain_file)
        if 'privkey_file' not in config or not config['privkey_file']:
            raise ValueError('privkey_file is required')
        privkey_file = get_path(config['privkey_file'], input_dir)
        if not exists(privkey_file):
            raise FileNotFoundError(privkey_file)
        if 'input' not in config or not config['input']:
            raise ValueError('input is required')
        if not isinstance(config['input'], list):
            raise ValueError('input must be a list')
        input_files = []
        makedirs(temp_dir, exist_ok=True)
        for input in config['input']:
            input_files.extend(get_input(input, input_dir, temp_dir))
        input_files = {i for i in input_files}
        name = 'Custom Fonts'
        if 'name' in config and config['name']:
            name = config['name']
        uuid_str = str(uuid.uuid4())
        identifier = 'com.example-' + uuid_str
        if 'identifier' in config and config['identifier']:
            identifier = config['identifier']
        description = 'Make the font available to iOS applications.'
        if 'description' in config and config['description']:
            description = config['description']
        organization = 'Font Profile'
        if 'organization' in config and config['organization']:
            organization = config['organization']
        temp_output = get_path(basename(output), temp_dir)
        with open(temp_output, 'w', encoding='UTF-8') as f:
            f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>PayloadUUID</key>
    <string>{uuid_str}</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
    <key>PayloadIdentifier</key>
    <string>{identifier}</string>
    <key>PayloadDisplayName</key>
    <string>{escape(name)}</string>
    <key>PayloadOrganization</key>
    <string>{escape(organization)}</string>
    <key>PayloadDescription</key>
    <string>{escape(description)}</string>
    <key>PayloadContent</key>
    <array>""")
            for i in input_files:
                uuid2 = str(uuid.uuid4())
                f.write(f"""
      <dict>
        <key>PayloadVersion</key>
        <integer>1</integer>
        <key>PayloadType</key>
        <string>com.apple.font</string>
        <key>PayloadIdentifier</key>
        <string>{uuid2}</string>
        <key>PayloadUUID</key>
        <string>{uuid2}</string>
        <key>Font</key>
        <data>""")
                with open(i, 'rb') as inp:
                    t = b''
                    t += inp.read(4096)
                    while len(t) >= 3:
                        read_len = floor(len(t) / 3) * 3
                        buf = t[:read_len]
                        t = t[read_len:]
                        f.write(b64encode(buf).decode())
                        t += inp.read(4096)
                    if t:
                        f.write(b64encode(t).decode())
                f.write(f"""</data>
      </dict>""")
            f.write("""
    </array>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadRemovalDisallowed</key>
    <false/>
  </dict>
</plist>""")
        run(['openssl', 'smime', '-sign', '-in', temp_output, '-out', output,
             '-signer', cert_file, '-inkey', privkey_file,
             '-certfile', chain_file, '-outform', 'der', '-nodetach'])
        remove(temp_output)


if __name__ == '__main__':
    main()
