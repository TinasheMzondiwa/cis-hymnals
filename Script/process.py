import json
from bs4 import BeautifulSoup as bs
import os

def process_songBook(book):
    my_json = json.load(book)

    for song in my_json:
        soup = bs(song['content'],'html.parser')
        my_song = ""
        
        try:
            my_song = "# " + str(soup.h1.text) + "\n\n "
            soup.h1.decompose()
        except:
            pass
        
        try:
            my_song = "### " + str(soup.h3.text) + "\n\n "
            soup.h3.decompose()
        except:
            pass
             

        for x in soup.find_all('p'):
            try:
                my_song += x.text + "\n"
            except:
                pass 
        
        song['content'] = my_song
    
    return my_json

new_dir = "New_Files"
path_ = os.getcwd()
my_files = os.listdir(path_)

for f in my_files:
    if f[-4:] == "json" and f != "config.json" and f != "xitsonga.json": 
        file_path = os.path.join(path_,f)        
        my_file = open(file_path,'r')
        new_json = process_songBook(my_file)
        new_file_path = os.path.join(path_,new_dir,f)
        with open(new_file_path,'w',encoding='utf8') as x:
            json.dump(new_json,x,indent=1)







