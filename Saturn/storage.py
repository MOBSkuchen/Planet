import os
from glob import glob
import shutil

class Bucket:
    def __init__(self, path: str, *, std_mode='r'):
        self.path = path
        self.files = {}
        self.std_mode = std_mode
        self._create()

    def join(self, name):
        return os.path.join(self.path, name)

    def _create(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    def files_retrieve(self):
        return glob(self.join("*"))

    def files_make(self):
        self.Fclose_all()
        for _name in self.files_retrieve():
            self.Fopen(os.path.basename(_name))

    def list_files(self):
        return self.files.keys()

    def delete(self):
        shutil.rmtree(self.path)

    def Fclose(self, name: str):
        name = self.join(name)
        if obj:=self.files[name] is not None:
            obj.close()
        del self.files[name]

    def Fclose_all(self):
        for name in self.files.keys(): self.Fclose(name)

    def Fdel(self, name):
        name = self.join(name)
        self.Fclose(name)
        if os.path.exists(name):
            os.remove(name)

    def Fopen(self, name: str):
        name = self.join(name)
        if name in self.files.keys():
            self.Fclose(name)
        self.files[name] = open(name, self.std_mode)

    def Frefresh(self, name: str):
        name = self.join(name)
        self.Fclose(name)
        self.Fopen(name)

    def Frefresh_all(self):
        for name in self.files.keys(): self.Frefresh(name)

    def puts(self, name, content):
        name = self.join(name)
        self.files[name].write(content)

    def gets(self, name, limit=-1):
        name = self.join(name)
        return self.files[name].read(limit)

    def move(self, path):
        shutil.move(self.path, path)
        self.path = path

    def Frename(self, name, new_name):
        name = self.join(name)
        new_name = self.join(new_name)
        self.Fclose(name)
        shutil.copy(name, new_name)
        os.remove(name)
        self.Fopen(new_name)

    def exists(self, name: str):
        return name in self.files

    def get_handle(self, name, auto_open=True):
        if not self.exists(name) and auto_open:
            self.Fopen(name)
        return self.files[name]

    def alloc_file(self, name, overwrite=False):
        if not overwrite and self.exists(name): return
        self.files[name] = None


def get_bucket(*args, **kwargs) -> Bucket:
    bucket = Bucket(*args, **kwargs)
    bucket.files_make()
    return bucket
