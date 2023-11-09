import Modrinth
import customtkinter as ctk

class Modpack():
    pth:str
    mods:list[Modrinth.slug]
    loaders:list[Modrinth.valid_loaders]
    mcversions:list[str]

    @classmethod
    def from_file(cls,pth:str):
        pass
    def export(self):
        pass
    def download(self):
        pass

class App(ctk.CTk):
    modpack:Modpack
    def __init__(self):
        super().__init__()
        self.title("LegoLoader")


if __name__=='__main__':
    pass