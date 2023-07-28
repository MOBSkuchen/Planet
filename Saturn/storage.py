import os
from glob import glob
import shutil
import json


class Bucket:
    def __init__(self, path: str, *, std_mode='r'):
        self.path = path
        self.files = {}
        self.std_mode = std_mode
        self._create()

    def join(self, *names):
        return os.path.join(self.path, *names).replace("\\", "/")

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
        if obj := self.files[name] is not None:
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
        n = self.join(name)
        if not overwrite and self.exists(name): return n
        self.files[name] = None
        return n

    def is_clam(self, name: str):
        return type(self.files[name]) == Clam

    def clam(self, name: str):
        clam = Clam(name, self)
        self.files[name] = clam
        return clam


class Clam:
    def __init__(self, name: str, bucket: Bucket):
        self.name = name
        self.bucket = bucket
        self.path = self.bucket.join(self.name)
        self._handle = open(self.path, 'r+')
        if not os.path.exists(self.path):
            self.dumps(self.path)

    def exports(self, key: str, value: str):
        obj = self.loads()
        obj[key] = value
        self.dumps(obj)

    def imports(self, key: str):
        return self.loads().get(key)

    def deletes(self, key: str):
        obj = self.loads()
        if key in obj:
            del obj[key]
        self.dumps(obj)

    def loads(self):
        return json.load(self._handle)

    def dumps(self, obj: dict):
        json.dump(obj, self._handle)


def get_bucket(*args, **kwargs) -> Bucket:
    bucket = Bucket(*args, **kwargs)
    bucket.files_make()
    return bucket
