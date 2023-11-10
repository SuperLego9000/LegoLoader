import Modrinth
import customtkinter as ctk
import os,re
__version__ = '2.4.0'

class Modpack():
    pth:str
    mods:dict[Modrinth.slug,tuple[bool,list[Modrinth.slug]]] = {}
    loaders:list[Modrinth.valid_loaders] = []
    can_depend:bool = False
    manual_depends:bool = True
    mcversions:list[str] = []
    def __repr__(self) -> str:
        return f"<Modpack '{self.pth}'>"

    @classmethod
    def from_file(cls,pth:str):
        self = cls()
        self.mods = {}
        self.loaders = []
        self.mcversions = []
        self.can_depend = False
        self.manual_depends = True
        self.pth = pth

        raw:str
        with open(self.pth,'r') as f:
            raw = f.read().split('\n',1) #type:ignore the files output is fs a string
        _ = raw[0].split(',')
        self.loaders,self.mcversions,self.can_depend = [_[0]],[_[1]],_[2]!='nodepend' #type:ignore # loader doesnt really have to be a valid one

        required,optional = raw[1].replace('\n\n','\n').split('\n[preference]\n')[:2] #type:ignore # slugs are strings oml
        required:list[Modrinth.slug] = required.strip().split('\n') #type:ignore
        optional:list[Modrinth.slug] = optional.strip().split('\n') #type:ignore
        slugs_preference:dict[str,bool] = {}
        for mainslug in required:
            slugs_preference[mainslug] = True
        for mainslug in optional:
            if not mainslug in slugs_preference:
                slugs_preference[mainslug] = False

        for topslug,perfered in slugs_preference.items():
            mainslug = topslug.split('[')[0]
            reqslugs = []
            req_index = topslug.find('[')
            if req_index>0:
                reqslugs = topslug[req_index:].strip('[]').split(',')
            self.mods[mainslug] = (perfered,reqslugs)

        return self

class App(ctk.CTk):
    modpack:Modpack
    modpack_selector:ctk.CTkComboBox
    selectable_mods:dict = {}
    selectable_mods_frame:ctk.CTkScrollableFrame
    
    
    def __init__(self):
        super().__init__()
        self.title(f"LegoLoader {__version__}")
        self.maxsize(2000,800)
        self.eval(f'tk::PlaceWindow {str(self)} center')
        self.update()

        self.rowconfigure(0,weight=1)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=20)

        self.control_frame = ctk.CTkFrame(self)
        self.selectable_mods_frame = ctk.CTkScrollableFrame(self)

        self.control_frame.grid(row=0,column=0,sticky=ctk.NSEW,padx=5,pady=5)
        self.selectable_mods_frame.grid(row=0,column=1,sticky=ctk.NSEW,padx=5,pady=5)

        self.modpack_selector = ctk.CTkComboBox(self.control_frame,values=['error'],state='readonly',command=self.select_modpack)
        self.modpack_selector.set("Modpack")
        self.modpack_selector_refresh()
        self.loader_label = ctk.CTkLabel(self.control_frame,text="Loader: ",state='disabled',height=20)
        self.version_label = ctk.CTkLabel(self.control_frame,text="Version: ",state='disabled',height=20)
        self.download_button = ctk.CTkButton(self.control_frame,text='Download',state='disabled',command=self.download_mods) #type:ignore # not my fault commands cant return values
        self.install_button = ctk.CTkButton(self.control_frame,text='Install',state='disabled',command=self.install_mods)
        self.progress_status = ctk.CTkLabel(self.control_frame,text="Ready",height=20)
        self.progress_bar = ctk.CTkProgressBar(self.control_frame)
        self.progress_bar.set(1)

        self.progress_status.pack(side=ctk.TOP,padx=5,pady=2,fill=ctk.X)
        self.progress_bar.pack(side=ctk.TOP,padx=5,pady=2,fill=ctk.X)
        self.modpack_selector.pack(side=ctk.TOP,padx=5,pady=5,fill=ctk.X)
        self.loader_label.pack(side=ctk.TOP,padx=5,pady=5,fill=ctk.X)
        self.version_label.pack(side=ctk.TOP,padx=5,pady=2,fill=ctk.X)
        self.install_button.pack(side=ctk.TOP,padx=5,pady=2,fill=ctk.X)
        self.download_button.pack(side=ctk.TOP,padx=5,pady=2,fill=ctk.X)
        
    def modpack_selector_refresh(self):
        '''reloads all options for the modpack selector'''
        modpacks:list[str] = []
        for (_,_,filenames) in os.walk('./modpacks/'):
            for file in filenames:
                if file.endswith(".ldr"):
                    modpacks.append(file.split('/')[-1].split('.')[0]) #filename from filepath
            del _,filenames
            break
        self.modpack_selector.configure(values=modpacks)

    def select_modpack(self,modpackname:str):
        self.modpack_selector_refresh()
        self.modpack = Modpack.from_file(f'./modpacks/{modpackname}.ldr')
        self.progress_status.configure(True,text="loading modpack...")
        self.update_idletasks()

        self.loader_label.configure(state='normal',text=f"Loader: {self.modpack.loaders[0]}")
        self.version_label.configure(state='normal',text=f"Version: {self.modpack.mcversions[0]}")
        
        for ckbox in self.selectable_mods_frame.pack_slaves():
            ckbox.destroy()
        self.selectable_mods = {}

        sluglen = 0
        for slug in self.modpack.mods.keys():
            if len(slug)>sluglen:
                sluglen = len(slug)
        for slug,(default,_) in self.modpack.mods.items():
            self.selectable_mods[slug] = ctk.CTkCheckBox(self.selectable_mods_frame,text=slug,width=300)
            if default:
                self.selectable_mods[slug].select()
            self.selectable_mods[slug].pack(side=ctk.TOP,padx=5,pady=1,fill=ctk.X)
        self.download_button.configure(state='default')
        self.install_button.configure(state='default')
        self.progress_status.configure(True,text="Ready!")
    def toggle_ui_interactions(self,can_interact:bool=True):
        state = 'normal' if can_interact else 'disabled'

        self.modpack_selector.configure(state='readonly' if can_interact else 'disabled')
        self.download_button.configure(state=state)
        self.install_button.configure(state=state)
        for slug,ckbox in self.selectable_mods.items():
            ckbox.configure(state=state)

    def download_mods(self) -> list[str]:
        self.toggle_ui_interactions(False)
        install:list[Modrinth.slug] = []
        files:list[str] = []
        for slug,ckbox in self.selectable_mods.items():
            if ckbox.get():
                install.append(slug)
                depends = self.modpack.mods[slug][1].copy()
                install.extend(depends)
                while depends!=[]:
                    for depend in depends:
                        if depend in self.modpack.mods.keys():
                            newdepends = self.modpack.mods[depend][1]
                            if not '' in newdepends:
                                depends.extend(newdepends)
                                install.extend(newdepends)
                        depends.remove(depend)
        install = list(set(install))
        for c,slug in enumerate(install):
            self.progress_bar.set((c+1)/(len(install)+1))
            self.progress_status.configure(text=f'downloading {slug[:16]}...')
            self.update()
            print(f'downloading {slug}...')
            import time
            time.sleep(0.2)
            jarfile = Modrinth.download_mod(slug,self.modpack.loaders,self.modpack.mcversions,5 if self.modpack.can_depend and not self.modpack.manual_depends else 0)
            files.append(jarfile) #
        self.progress_status.configure(text=f'Done!')
        print('done!')
        self.progress_bar.set(1)
        self.toggle_ui_interactions(True)
        return files
    def install_mods(self):
        jarstocopy = self.download_mods()
        self.toggle_ui_interactions(False)
        self.update_idletasks()

        modsfolder = f"./mods/{','.join(self.modpack.loaders)};{','.join(self.modpack.mcversions)}"
        modsfolder = os.path.abspath(modsfolder)
        minecraftmodsfolder = os.path.join(os.environ.get('userprofile'),"AppData\\Roaming\\.minecraft\\mods\\") #type:ignore # userprofile is "allways" in environ
        minecraftmodsfolder = os.path.abspath(minecraftmodsfolder)

        if not os.path.isdir(minecraftmodsfolder): #if you somehow dont have a mods folder?
            os.mkdir(minecraftmodsfolder)

        self.progress_status.configure(text='clearing old mods...')
        self.update_idletasks()

        #remove old mods
        try:
            for (cd,dirs,files) in os.walk(minecraftmodsfolder+'\\'):
                for c,file in enumerate(files):
                    self.progress_bar.set(c/len(jarstocopy))
                    self.progress_status.configure(True,text=f'removing {file[:16]}...')
                    self.update()
                    print(f'removing {file}!')
                    os.remove(os.path.abspath(os.path.join(cd,file)))

            #copy mods
            for c,file in enumerate(jarstocopy):
                self.progress_bar.set(c/len(jarstocopy))
                fpth = os.path.join(modsfolder,file)
                despth = os.path.join(minecraftmodsfolder,file)

                self.progress_status.configure(True,text=f"copying {file[:16]}...")
                print(f"copying {file}...")
                self.update()
                with open(fpth,'rb') as f:
                    data:bytes = f.read()
                    with open(despth,'ab') as d:
                        d.write(data)
            self.progress_status.configure(text=f'Done!')
        except PermissionError:
            self.progress_status.configure(text=f'permisions error!')
            print('permisions error somewhere')
        self.progress_bar.set(1)
        self.toggle_ui_interactions(True)
        print('Done!')

if __name__=='__main__':
    rd = ['mods','cache','modpacks']
    for d in rd:
        if not os.path.isdir(f"./{d}"):
            os.mkdir(d)
    app = App()
    app.mainloop()