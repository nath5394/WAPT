# -*- coding: utf-8 -*-
from setuphelpers import *
import os
import _winreg
import tempfile


# registry key(s) where WAPT will find how to remove the application(s)
uninstallkey = []

def update_sources():
    files = [
         'common.py',
         'setuphelpers.py',
         'wapt-get.exe',
         'wapt-get.exe.manifest',
         'wapt-get.py',
         'waptdevutils.py',
         'waptpackage.py',
         'wapttray.exe',
         'keyfinder.py',
         'COPYING.txt',
         'version',
         'templates',
         'waptconsole.exe',
         'waptconsole.exe.manifest',
         'waptservice',
    ]

    def ignore(src,names):
        result = []
        for name in names:
            for pattern in ['*.pyc','*.exe']:
                if glob.fnmatch.fnmatch(name,pattern):
                    result.append(name)
        return result

    checkout_dir = os.path.abspath(os.path.join(os.getcwd(),'..'))

    # cleanup patchs dir
    shutil.rmtree(os.path.join(checkout_dir,'waptupgrade','patchs'))
    os.makedirs(os.path.join(checkout_dir,'waptupgrade','patchs'))
    for f in files:
        fn = os.path.join(checkout_dir,f)
        target_fn = os.path.join(checkout_dir,'waptupgrade','patchs',f)
        if os.path.isfile(fn):
            filecopyto(fn,target_fn)
        elif os.path.isdir(fn):
            copytree2(
                src=fn,
                dst=target_fn,
                onreplace = default_overwrite,
                ignore=ignore)


def update_control(entry):
    """Update package control file before build-upload"""
    update_sources()
    waptget = get_file_properties(r'patchs\wapt-get.exe')
    rev = open('../version').read().strip()
    entry.version = '%s-%s' % (waptget['FileVersion'],rev)

def oncopy(msg,src,dst):
    print(u'%s : "%s" to "%s"' % (ensure_unicode(msg),ensure_unicode(src),ensure_unicode(dst)))
    return True

def update_registry_version(version):
    # updatethe registry
    with _winreg.CreateKeyEx(HKEY_LOCAL_MACHINE,r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WAPT_is1',\
            0, _winreg.KEY_READ| _winreg.KEY_WRITE ) as waptis:
        reg_setvalue(waptis,"DisplayName","WAPT %s" % version)
        reg_setvalue(waptis,"DisplayVersion","WAPT %s" % version)
        reg_setvalue(waptis,"InstallDate",currentdate())

def install():
    # if you want to modify the keys depending on environment (win32/win64... params..)
    print(u'Partial upgrade of WAPT  client')
    killalltasks('wapttray.exe')
    copytree2('patchs',WAPT.wapt_base_dir, onreplace = default_overwrite,oncopy=oncopy)
    update_registry_version(control.version)
    # restart of service can not be done by service...
    if service_installed('waptservice') and service_is_running('waptservice'):
        import requests,json
        try:
            res = json.loads(requests.get('http://127.0.0.1:8088/waptservicerestart.json').text)
        except:
            tmp_bat = tempfile.NamedTemporaryFile(prefix='waptrestart',suffix='.cmd',mode='wt',delete=False)
            tmp_bat.write('ping -n 2 127.0.0.1 >nul\n')
            tmp_bat.write('net stop waptservice\n')
            tmp_bat.write('net start waptservice\n')
            tmp_bat.write('del "%s"\n'%tmp_bat.name)
            tmp_bat.close()
            shell_launch(tmp_bat.name)

    print(u'Upgrade done')

