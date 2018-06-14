#coding:utf-8
"""
Provide functions for Java Card.
"""

import zipfile


class CapFile:
    def __init__(self, cap_path):
        zf = zipfile.ZipFile(cap_path, 'r')
        try:
            names = zf.namelist()
            self.__content = {
                'Header': b'',
                'Directory': b'',
                'Import': b'',
                'Applet': b'',
                'Class': b'',
                'Method': b'',
                'StaticField': b'',
                'ConstantPool': b'',
                'RefLocation': b'',
                'Debug': b'',
                'Export': b'',
                'Descriptor': b'',
            }
            self.__pkg_name = ''
            for name in names:
                if 'javacard' in name and '.cap' in name:
                    if not self.__pkg_name:
                        self.__pkg_name = name[:name.rfind(
                            "/javacard/")].replace('/', '.')
                    self.__content[name[name.rfind('/') +
                                        1:-4]] = zf.read(name)

            #package aid
            header = self.__content["Header"]
            pkgaidlen = header[12]
            self.__pkg_aid = header[13:pkgaidlen + 13]

            #applet aids
            aids = []
            applet = self.__content["Applet"]
            length = len(applet)
            index = 4
            while index < length:
                aid_len = applet[index]
                aids.append(applet[index + 1:index + 1 + aid_len])
                index += 3 + aid_len
            self.__app_aids = tuple(aids)
        finally:
            zf.close()

    @property
    def pkg_name(self):
        return self.__pkg_name

    @property
    def pkg_aid(self):
        return self.__pkg_aid

    @property
    def app_aids(self):
        return self.__app_aids

    def __getattr__(self, name):
        if name in self.__content:
            return self.__content[name]
        else:
            raise AttributeError('class CapFile has no attr: %s' % name)

    def getattr(self, name):
        if name in self.__content:
            return self.__content[name]
        else:
            raise AttributeError('class CapFile has no attr: %s' % name)


__all__ = ["CapFile"]
