import Modrinth
import customtkinter as ctk
import os

class Modpack():
    pth:str
    mods:list[tuple[Modrinth.slug,bool]] = []
    loaders:list[Modrinth.valid_loaders] = []
    mcversions:list[str] = []
    def __repr__(self) -> str:
        return f"<Modpack '{self.pth}'>"

    @classmethod
    def from_file(cls,pth:str):
        self = cls()
        self.mods = []
        self.loaders = []
        self.mcversions = []
        self.pth = pth

        raw:str
        with open(self.pth,'r') as f:
            raw = f.read().split('\n',1)
        _ = raw[0].split(',')
        self.loaders,self.mcversions = [_[0]],[_[1]] #type:ignore # loader doesnt really have to be a valid one

        required,optional = raw[1].split('\n[preference]\n')

        #could do this better but this is fine
        for slug in required.strip().split('\n'):
            self.mods.append((slug,True))
        for slug in optional.strip().split('\n'):
            self.mods.append((slug,False))
        
        return self

class App(ctk.CTk):
    modpack:Modpack
    selected_modpack:ctk.StringVar
    modpack_selector:ctk.CTkComboBox
    selectable_mods:dict = {}
    selectable_mods_frame:ctk.CTkFrame
    
    
    def __init__(self):
        super().__init__()
        self.title("LegoLoader")
        self.resizable(False,False)

        self.rowconfigure(0,weight=1)
        self.rowconfigure(1,weight=4)
        self.columnconfigure(0,weight=1)
        self.columnconfigure(1,weight=1)

        mptext = ctk.CTkLabel(self,text="modpack: ")
        self.selected_modpack = ctk.StringVar()
        self.modpack_selector = ctk.CTkComboBox(self,values=['error'],state='readonly',command=self.select_modpack)
        self.modpack_selector.set("Modpack")
        self.modpack_selector_refresh()

        self.selectable_mods_frame = ctk.CTkFrame(self)

        self.control_frame = ctk.CTkFrame(self)
        
        mptext.grid(row=0,column=0)
        self.modpack_selector.grid(row=0,column=1,sticky=ctk.NW)
        self.selectable_mods_frame.grid(row=1,column=1,padx=5,pady=5)

        self.control_frame.grid(row=1,column=0,sticky=ctk.NSEW,padx=5,pady=5)

        self.loader_label = ctk.CTkLabel(self.control_frame,text="Loader: ",state='disabled',height=20)
        self.version_label = ctk.CTkLabel(self.control_frame,text="Version: ",state='disabled',height=20)
        self.download_button = ctk.CTkButton(self.control_frame,text='Download',state='disabled',command=self.download_mods)
        self.install_button = ctk.CTkButton(self.control_frame,text='Install',state='disabled')
        self.progress_bar = ctk.CTkProgressBar(self.control_frame)
        self.progress_bar.set(1)

        self.loader_label.pack(side=ctk.TOP,padx=5,pady=5)
        self.version_label.pack(side=ctk.TOP,padx=5,pady=2)
        self.download_button.pack(side=ctk.TOP,padx=5,pady=2)
        self.install_button.pack(side=ctk.TOP,padx=5,pady=2)
        self.progress_bar.pack()
        
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

        self.loader_label.configure(state='normal',text=f"Loader: {self.modpack.loaders[0]}")
        self.version_label.configure(state='normal',text=f"Version: {self.modpack.mcversions[0]}")
        
        for ckbox in self.selectable_mods_frame.pack_slaves():
            ckbox.destroy()
        self.selectable_mods = {}

        sluglen = 0
        for slug,_ in self.modpack.mods:
            if len(slug)>sluglen:
                sluglen = len(slug)
        for slug,default in self.modpack.mods:
            self.selectable_mods[slug] = ctk.CTkCheckBox(self.selectable_mods_frame,text=slug,width=300)
            if default:
                self.selectable_mods[slug].select()
            self.selectable_mods[slug].pack()
        self.download_button.configure(state='default')
        self.install_button.configure(state='default')

    def download_mods(self):
        self.modpack_selector.configure(state='disabled')
        self.download_button.configure(state='disabled')
        self.install_button.configure(state='disabled')
        install:list[Modrinth.slug] = []
        for slug,ckbox in self.selectable_mods.items():
            if ckbox.get():
                install.append(slug)
        for c,slug in enumerate(install):
            self.progress_bar.set((c+1)/(len(install)+1))
            self.update()
            print(f'downloading {slug}...')
            Modrinth.download_mod(slug,self.modpack.loaders,self.modpack.mcversions)
        print('done!')
        self.progress_bar.set(1)
        self.modpack_selector.configure(state='readonly')
        self.download_button.configure(state='normal')
        self.install_button.configure(state='normal')

    


if __name__=='__main__':
    app = App()
    app.mainloop()