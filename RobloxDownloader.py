import hashlib
import requests
import os
import json
import zipfile

session = requests.Session()

def parseRbxManifest(rbxManifest:str):
    hashTable = {}

    linenum = 0
    currentfile = ""
    for line in rbxManifest.split('\r\n'):
        linenum+=1
        if line=="":
            continue
        if linenum % 2:
            if line.find('\\') != -1 and line.startswith('Qt5'):
                line = f'Plugins\\{line}'
            elif line.find('\\') != -1 and line.startswith('Qt'):
                line = f'Qml\\{line}'
            currentfile = line
        else:
            hashTable[line] = currentfile
    return hashTable

def parseRbxPkgManifest(rbxPkgManifest:str):
    files = {
        'zips':[],
        'normal':[]
    }
    
    
    for line in rbxPkgManifest.split('\r\n'):
        if line.find(".") == -1:
            continue
        if line.find(".zip") != -1:
            files["zips"].append(line)
        else:
            files["normal"].append(line)
        
        
    return files

def getChecksum(nig:bytes):
    return hashlib.md5(nig).hexdigest()

def _extract_member(self, member, lookuptable, zipname:str, targetpath=None, pwd=None): # basically _extract_member from zipfile but made to use hashlookup
    if targetpath is None:
        targetpath = os.getcwd()
    else:
        targetpath = os.fspath(targetpath)
    
    if not isinstance(member, zipfile.ZipInfo):
        member = self.getinfo(member)

    if not member.is_dir():
        with self.open(member, pwd=pwd) as source:
            sourcebytes = source.read()
            checksum = getChecksum(sourcebytes)
            pathfromfile = os.path.join(os.getcwd(),zipname.replace('.zip','/').replace('-','/'))
            
            if checksum in lookuptable:
                targetpath = os.path.join(os.getcwd(),lookuptable[checksum])
                dirpath = os.path.dirname(targetpath)
            elif member.filename.find("/")!=-1 and os.path.exists(os.path.join(os.getcwd(),member.filename.split('/')[0])):
                targetpath = os.path.join(os.getcwd(),member.filename)
                dirpath = os.path.dirname(targetpath)
            elif os.path.exists(pathfromfile) or member.filename.find('.robloxrc') !=-1:
                targetpath = os.path.join(pathfromfile,member.filename)
                dirpath = os.path.dirname(targetpath)
            else:
                targetpath = os.path.join(os.getcwd(),member.filename)
                dirpath = os.path.dirname(targetpath)

            if not os.path.exists(dirpath):
                os.makedirs(dirpath)
            with open(targetpath, "wb") as target:
                target.write(sourcebytes)

def download(version,mac=False,channel='LIVE',basepath='https://setup.rbxcdn.com',ClientAppSettings={
        "FFlagHandleAltEnterFullscreenManually": "False",
        "FLogNetwork": "7",
        "DFIntTaskSchedulerTargetFps": "120"
    }):
    firstdir = os.getcwd()
    
    if channel == "LIVE":
        channelPath = basepath
    else:
        channelPath = f'{basepath}/channel/{channel}'

    blobDir = '/'
    
    if mac:
        blobDir = '/mac/'
    
    versionPath = f'{channelPath}{blobDir}{version}-'
    rbxManifestPath = versionPath+'rbxManifest.txt'
    rbxPkgManifestUrl = f'{versionPath}rbxPkgManifest.txt'
    
    try:
        os.mkdir(version)
    except Exception as e:
        print(e)

    os.chdir(version)

    with open("AppSettings.xml", "w") as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
    <Settings>
        <ContentFolder>content</ContentFolder>
        <BaseUrl>http://www.roblox.com</BaseUrl>
    </Settings>''')

    try:
        os.mkdir("ClientSettings")
    except Exception as e:
        print(e)

    with open("ClientSettings/ClientAppSettings.json", "w") as f:
        f.write(json.dumps(ClientAppSettings,indent=2))

    hashTable = parseRbxManifest(session.get(rbxManifestPath).text) # not a hash table lol
    files = parseRbxPkgManifest(session.get(rbxPkgManifestUrl).text)

    for file in files['zips']:
        with open(file,'wb') as f:
            f.write(session.get(versionPath+file).content)
        with zipfile.ZipFile(file,'a') as zip_ref:
            for zipinfo in zip_ref.namelist():
                if not zipinfo.endswith("/"):
                    _extract_member(zip_ref,zipinfo,hashTable,file)
        os.remove(file)
        
    for file in files['normal']:
        with open(file,'wb') as f:
            f.write(session.get(versionPath+file).content)
            
    versiondir = os.getcwd()
    os.chdir(firstdir)
    return versiondir