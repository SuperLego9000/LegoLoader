import requests,json,hashlib,os
request_headers = {
    'User-Agent': 'SuperLego9000/legoloader/3.1.0', # TODO make an email i can give out to companies that isnt my full name lol
    }

import typing
slug:typing.TypeAlias = str
mod_version_descriptor:typing.TypeAlias = dict
valid_loaders = typing.Literal['fabric','quilt','forge','neoforge']

def request_with_cache(url,modal=requests.get,headers=request_headers):
    OFFLINE = False

    hashed = hashlib.sha1(url.encode()).hexdigest()
    hashedpath = f"./cache/{hashed}.jsonc"
    req:dict|list = []
    if os.path.isfile(hashedpath): # TODO consider cache expiration
        with open(hashedpath,'r') as f:
            req = json.loads(f.read())
    else:
        if OFFLINE:
            req = ['dummydata']
        else:
            res = modal(url,headers=headers)
            match res.status_code:
                case 200:
                    req = res.json()
                case 410:
                    raise NotImplementedError(f"Modrinth API depricated! path: {url}")
                case 400:
                    errordesc = res.json()
                    raise PermissionError(f"request error occured! Modrinth API: {errordesc['error']}:{errordesc['description']}")
                case _:
                    raise NotImplementedError(f"received status code:{res.status_code} from path '{url}'. unhandleable error please report.")

        with open(hashedpath,'w') as f:
            f.write(json.dumps(req))
    
    return req

def get_mod_versions(mod:slug,loaders:list[valid_loaders],mcversions:list[str]) -> list[mod_version_descriptor]:
    '''gets the mods version; sorted newest first'''
    ureloaders = str(loaders).replace("'",'"')
    uremcversions = str(mcversions).replace("'",'"') # url queries dont like single qoutes

    url = f"https://api.modrinth.com/v2/project/{mod}/version?loaders={ureloaders}&game_versions={uremcversions}"
     
    return request_with_cache(url,requests.get,request_headers) #type:ignore
def download_mod(mod:slug,loaders:list[valid_loaders],mcversions:list[str],dependRecursion:int=5,index:int=0) -> str:
    '''gets the latest version from cache or internet and downloads it'''
    mod = 'fabric-api' if mod =='9CJED7xi' else mod
    modsfolder = f"./mods/{','.join(loaders)};{','.join(mcversions)}"
    if not os.path.isdir(modsfolder):
        os.mkdir(modsfolder)
    vers:list[mod_version_descriptor] = get_mod_versions(mod,loaders,mcversions)
    assert len(vers)>0,KeyError(f"mod has no versions matching requirements {mod,loaders,mcversions}")
    ver:mod_version_descriptor = vers[index]

    assert len(ver['files'])>0,KeyError("tried downloading a mod with no files")

    if dependRecursion>0 and\
    not ver['author_id'] in ['8a7Nm6u3'] and\
    not ver['project_id'] in ['simple-voice-chat','9eGKb6K1']:
        for depend in ver['dependencies']:
            if depend['project_id']!=mod: #requiring yourself like wtf
                print(f'   depending on {depend["project_id"]}')
                download_mod(depend['project_id'],loaders,mcversions,dependRecursion=dependRecursion-1)
    
    for file in ver['files']:
        if file['filename'].endswith(".jar"):
            downloadedmodpath = f"{modsfolder}/{file['filename']}"
            if os.path.isfile(downloadedmodpath):return file['filename'] # already have it
            print(f"downloading {file['filename']}")
            res = requests.get(file['url'],request_headers)
            assert res.status_code==200,PermissionError(f"downloading {file['url']} resulted status code:{res.status_code}")
            with open(downloadedmodpath,'wb') as f:
                f.write(res.content)
            return file['filename']
        else:
            raise IndexError(f"no jar files found for version in mod {ver['project_id']}")
    raise NotImplementedError(f"failed to download slug {slug} for {loaders,mcversions}")
    