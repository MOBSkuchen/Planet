import os
from glob import glob
import shutil
import json
from discord import *


class Clam:
    def __init__(self, name: str, bucket):
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
        return json.loads(self._handle.read())

    def dumps(self, obj: dict):
        self._handle.write(json.dumps(obj))

    def close(self):
        self._handle.close()


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

    def add_clam(self, clam: Clam):
        self.files[clam.name] = clam

    def get_item(self, name: str):
        return self.files[name]

    def from_member(self, member_: Member):
        name = f'mem_{member_.id}'
        if not self.exists(name):
            return self.get_item(name)
        c = Clam(name, self)
        self.add_clam(c)
        return c


class Group:
    def __init__(self, path: str):
        self.path = path
        self.buckets = {}

        self._create()

    def join(self, *names):
        return os.path.join(self.path, *names)

    def _create(self):
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    def _init_bucket(self, bucket: Bucket): pass

    def get_bucket(self, name: str, *, std_mode='r') -> Bucket:
        bucket = Bucket(self.join(name), std_mode=std_mode)
        bucket.files_make()
        self._init_bucket(bucket)
        self.buckets[name] = bucket
        return bucket


def get_bucket(name: str, *, std_mode='r') -> Bucket:
    bucket = Bucket(name, std_mode=std_mode)
    bucket.files_make()
    return bucket


class Servers(Group):
    @staticmethod
    def get_guild_name(guild_: Guild | int):
        if type(guild_) == Guild:
            guild_ = guild_.id
        return f"g_{guild_}"

    def get_guild_bucket(self, guild_: Guild | int, **kwargs):
        return self.get_bucket(self.get_guild_name(guild_), **kwargs)

    def _init_bucket(self, bucket: Bucket):
        bucket.clam("settings")
        bucket.clam("users")

    def init_server(self, guild_: Guild | int):
        self.set_server_setting(guild_, "reports", 0)
        self.set_server_setting(guild_, "lang", "English")

    def add(self, guild_: Guild | int):
        return self.get_bucket(self.get_guild_name(guild_))

    def set_server_setting(self, guild_: Guild | int, key: str, value: str | int | bool):
        bucket = self.get_guild_bucket(guild_)
        c = bucket.clam("settings")
        c.exports(key, value)

    def get_server_setting(self, guild_: Guild | int, key: str):
        bucket = self.get_guild_bucket(guild_)
        c = bucket.clam("settings")
        return c.imports(key)

    def add_and_init(self, guild_: Guild | int):
        x = self.add(guild_)
        self.init_server(guild_)
        return x


servers = Servers("storage/servers")

