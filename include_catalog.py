from src.Models import Catalog_List, Catalog_Files
import os
import mimetypes

def set_list():
    name = input("Nome:")

    while True:
        random = input("Random (Y,N):").lower()
        if (random in ('y', '1', 'yes', 's', 'sim', 'n', '0', 'no', 'não', 'nao')):
            random = False if random in ('n', '0', 'no', 'n') else True
            break
    return Catalog_List.create(name=name,random=random,path_personality_opening=None)

def set_files(id_list):
    path_principal=input("Pasta Principa dos Aquivos:")
    
    def search_files(path):
        path=path.replace("\\","/")
        if path[-1]!='/':
            path=path+"/"

        list_path=sorted(os.listdir(path),key=len)
        files=[]
        for list in list_path:
            list=path+list
            if os.path.isdir(list):
                files=files+search_files(list)
            elif os.path.isfile(list) and mimetypes.guess_type(list)[0].startswith('video'):
                files.append(list)
        return files
    files=search_files(path_principal)
    for file in files:
        files_exist=Catalog_Files.select().where(Catalog_Files.path==file).dicts()
        if len(files_exist)==0:
            Catalog_Files.create(catalog_id=id_list,watched=0,path=file,cutoffs='{"opening":{"time-start":"00:00:00","time-end":"00:00:00"}}')
if __name__ == "__main__":
    id_list=1
    # id_list=set_list()
    set_files(id_list)
