# -*- coding: utf-8 -*-

'''
Basic interface to communicate with Scrivener projects

'''

import os
import xml.etree.ElementTree
from pyth.plugins.rtf15.reader import Rtf15Reader
from pyth.plugins.plaintext.writer import PlaintextWriter

class MetaData(object):
    """
    holds the metadata information
    If absent will not pass a hasattr
    """
    def __init__(self,item):
        for i in item:
            setattr(self,i.tag,i.text)

class BinderItem(object):
    """
    Contains the item information - can connect to the file    
    """
    def __init__(self,item,binder):
        self._binder = binder
        self.children = []
        self.__dict__.update(item.attrib)
        for i in item:
            if i.tag == "Title":
                self.title = i.text 
            if i.tag == "MetaData":
                self.metadata = MetaData(i)
            if i.tag == "Children":
                self.children = [BinderItem(x,self._binder) for x in i]

    def iter_text(self):
        """
        merge text for this snippet and all children
        """
        text = u""
        for ci in self:
            text += ci.get_text() + u"\n"
        return text
    
    def get_text(self):
        """
        return a unicode object from the rtf file
        """
        loc = self.get_file_loc()
        if loc:
            doc = Rtf15Reader.read(open(loc,"rb"))
            txt = PlaintextWriter.write(doc).getvalue()
            return txt.decode('utf-8')
        else:
            return u""
    
    def get_file_loc(self):
        """
        returns the file path of this snippet
        """
        if hasattr(self.metadata,"FileExtension"):
            filename = "{0}.{1}".format(self.ID,self.metadata.FileExtension)
            file_path = self._binder.folder
            return os.path.join(file_path,"files","docs",filename)
        else:
            return None
    
    def __iter__(self):
        """
        iterate through all children and their children, etc
        """
        for c in self.children:
            yield c
            for ci in c:
                yield ci
    
    def __repr__(self):
        return "[BinderItem {0}: {1}]".format(self.ID,self.title)                
            
class Binder(object):
    """
    Binder contains all snippets as self.items
    """
    def __init__(self,folder,obj):
        
        self.items = []
        self.folder = folder
        for item in obj.findall('BinderItem'):
            i = BinderItem(item,self)
            self.items.append(i)
            
    def iter_through_all(self):
        """
        iterate through every snippet and their children
        """
        for c in self.items:
            yield c
            for ci in c.children:
                yield ci
    
    def get(self,title="",id=""):
        """
        given the title or id of a snippet, return the object
        """
        for item in self.iter_through_all():
            if title:
                if item.title == title:
                    return item
            if id:
                if item.ID == id:
                    return item        

class Scrivener(object):
    """
    interfaces with scrivener folder
    """
    def __init__(self,folder):
        self.folder = folder
        self.project_file = os.path.join(self.folder,"project.scrivx")
        self.project_tree = xml.etree.ElementTree.parse(self.project_file)
        self.root = self.project_tree.getroot()
        self.binder = Binder(folder,self.root.findall('Binder')[0])
        
    def get(self,*args,**kwargs):
        return self.binder.get(*args,**kwargs)
    
    def get_autocomplete(self):
        collection = self.root.findall('AutoCompleteList')[0]
        
        return [x.text for x in collection.findall("Completion")]
            
    def add_autocomplete(self,new):
        collection = self.root.findall('AutoCompleteList')[0]
        element = xml.etree.ElementTree.Element("Completion",Scope="0")
        element.text = new
        collection.append(element)
              
    def save(self):
        self.project_tree.write(self.project_file)