import os
from glob import glob
import shutil
import json
from discord import *
from Saturn import STORAGE
from typing import IO


def _create_file(filename):
    """
    Create a JSON loadable file
    :param filename:
    Name of the file to be created
    """
    with open(filename, 'w') as file_:
        file_.write("{}")


def _check_storage():
    """
    Create the storage directory
    """
    if not os.path.exists(STORAGE):
        os.mkdir(STORAGE)


class Clam:
    """
    A Clam is just a glorified JSON file with a nice handle
    """
    def __init__(self, name: str, bucket):
        self.name = name
        self.bucket = bucket
        self.path = self.bucket.join(self.name)
        # Create file if it does not yet exist
        if not os.path.exists(self.path):
            _create_file(self.path)

    def _handle(self, mode) -> IO:
        return open(self.path, mode)

    def exports(self, key: str, value: str):
        """
        Set <key> to <value>
        If <key> does not yet exist, it is newly created
        :param key:
        Key to write to
        :param value:
        Value to set to
        """
        obj = self.loads()
        obj[key] = value
        self.dumps(obj)

    def imports(self, key: str) -> str:
        """
        Get the value behind <key>
        :param key:
        The key to get the value of
        :return:
        Value behind <key>, None if <key> does
        not exist
        """
        return self.loads().get(key)

    def deletes(self, key: str):
        """
        Delete <key> and its value
        :param key:
        The key to delete
        """
        obj = self.loads()
        if key in obj:
            del obj[key]
        self.dumps(obj)

    def loads(self) -> dict:
        """
        Return full dict representation of this Clam
        """
        with self._handle("r") as h:
            return json.loads(h.read())

    def dumps(self, obj: dict):
        """
        Change all of this Clams data
        :param obj:
        The object to change to
        """
        with self._handle("w") as h:
            h.write(json.dumps(obj))


class Bucket:
    """
    A bucket is a group of Clams
    """
    def __init__(self, path: str, *, std_mode='r'):
        self.path = path
        self.files = {}
        self.std_mode = std_mode
        self._create()

    def __del__(self):
        """
        Alias for Fclose_all
        """
        self.file_close_all()

    def join(self, *names) -> str:
        """
        Like os.join, just with the path of this bucket
        :param names:
        Names to join together
        :return:
        Joint path
        """
        if names[0].replace("\\", "/").startswith(self.path.replace("\\", "/")):
            return os.path.join(*names).replace("\\", "/")
        return os.path.join(self.path, *names).replace("\\", "/")

    def _create(self):
        """
        Create the buckets directory if it does not yet exist
        """
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    def files_retrieve(self) -> list[str]:
        """
        Get all files under the buckets directory
        :return:
        A list of files
        """
        return glob(self.join("*"))

    def files_make(self):
        """
        Get all files in the buckets directory,
        close them and then open them again
        This is the same as Frefresh_all, except that it also opens
        handles for not yet registered files
        """
        self.file_close_all()
        for _name in self.files_retrieve():
            self.file_open(os.path.basename(_name))

    def list_files(self) -> Any:
        """
        List all allocated files
        :return:
        A list of files (as dict_keys)
        """
        return self.files.keys()

    def delete(self):
        """
        Completely delete entire bucket
        """
        shutil.rmtree(self.path)

    def file_close(self, name: str):
        """
        Close a handle
        :param name:
        Name of the file handle
        """
        name = self.join(name)
        if name not in self.files:
            return
        if (obj := self.files[name]) is not None:
            obj.close()
        del self.files[name]

    def file_close_all(self):
        """
        Close all handles
        """
        for name in list(self.files.keys()):
            self.file_close(name)

    def file_delete(self, name: str):
        """
        Delte a file and close its handle
        :param name:
        Name of the file
        """
        name = self.join(name)
        self.file_close(name)
        if os.path.exists(name):
            os.remove(name)

    def file_open(self, name: str):
        """
        Open a new handle for a file
        :param name:
        Name of the file
        """
        name = self.join(name)
        if name in self.files.keys():
            self.file_close(name)
        self.files[name] = open(name, self.std_mode)

    def file_refresh(self, name: str):
        """
        Close and reopen a handle
        :param name:
        Name of the file handle
        """
        name = self.join(name)
        self.file_close(name)
        self.file_open(name)

    def file_refresh_all(self):
        """
        Close and reopen all handles
        """
        for name in self.files.keys():
            self.file_refresh(name)

    def puts(self, name: str, content: str):
        """
        Write <content> to file <name>
        :param name:
        Name of the file to write to
        :param content:
        Content to write to file
        :return:
        """
        name = self.join(name)
        self.files[name].write(content)

    def gets(self, name, limit=-1):
        """
        Get content of a file
        :param name:
        Name of the file
        :param limit:
        Limit of bytes to read (-1 to read all of it)
        :return:
        Content of the file
        """
        name = self.join(name)
        return self.files[name].read(limit)

    def move(self, path: str):
        """
        Move an entity to <path>
        :param path:
        The path to move to
        """
        shutil.move(self.path, path)
        self.path = path

    def file_rename(self, name: str, new_name: str):
        """
        Rename a file
        :param name:
        Original name of the file
        :param new_name:
        New name of the file
        """
        name = self.join(name)
        new_name = self.join(new_name)
        self.file_close(name)
        shutil.copy(name, new_name)
        os.remove(name)
        self.file_open(new_name)

    def exists(self, name: str) -> bool:
        """
        Check whether a file exists
        :param name:
        Name of the file
        :return:
        Whether it exists
        """
        return name in self.files

    def get_handle(self, name: str, auto_open=True):
        """
        Get a file handle
        :param name:
        Name of the file
        :param auto_open:
        Whether to automatically open the file
        :return:
        Return the file handle
        """
        if not self.exists(name) and auto_open:
            self.file_open(name)
        return self.files[name]

    def alloc_file(self, name: str, overwrite=False):
        """
        Pretend like a file exists
        This does NOT affect Bucket.exists
        :param name:
        Name of the file
        :param overwrite:
        Whether to overwrite the file if it already exists
        :return:
        The full path of the allocated file
        """
        n = self.join(name)
        if not overwrite and self.exists(name):
            return n
        self.files[name] = None
        return n

    def is_clam(self, name: str):
        """
        Check if a file is a Clam
        :param name:
        Name of the file
        :return:
        Whether the file is a Clam
        """
        return type(self.files[name]) == Clam

    def clam(self, name: str):
        """
        Create a clam out of the file
        :param name:
        Name of the file
        :return:
        Created clam
        """
        clam = Clam(name, self)
        self.files[name] = clam
        return clam

    def add_clam(self, clam: Clam):
        """
        Add a clam to the bucket
        :param clam:
        The clam to add
        """
        self.files[clam.name] = clam

    def get_item(self, name: str):
        """
        Get an item out of the list of files
        :param name:
        Name of the item (file)
        :return:
        The handle
        """
        return self.files[name]

    def from_member(self, member_: Member):
        """
        Create a new Clam for a member
        :param member_:
        The member
        :return:
        The Clam for the member
        """
        name = f'mem_{member_.id}'
        if not self.exists(name):
            return self.get_item(name)
        return self.clam(name)


class Group:
    """
    A group of buckets
    """
    def __init__(self, path: str):
        self.path = path
        self.buckets = {}

        self._create()

    def join(self, *names: str):
        """
        Like os.join, just with the path of this Group
        :param names:
        Names to join together
        :return:
        Joint path
        """
        return os.path.join(self.path, *names)

    def _create(self):
        """
        Create the bucket directory
        """
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    # Currently has no effect
    def _init_bucket(self, bucket: Bucket): pass

    def get_bucket(self, name: str, *, std_mode='r') -> Bucket:
        """
        Get a bucket from the group
        :param name:
        Name of the bucket
        :param std_mode:
        Standard read mode
        :return:
        The bucket
        """
        bucket = Bucket(self.join(name), std_mode=std_mode)
        bucket.files_make()
        self._init_bucket(bucket)
        self.buckets[name] = bucket
        return bucket


def get_bucket(name: str, *, std_mode='r') -> Bucket:
    """
    Create a bucket from a directory
    :param name:
    Name of the bucket (directory)
    :param std_mode:
    Standard read mode
    :return:
    Bucket
    """
    bucket = Bucket(name, std_mode=std_mode)
    bucket.files_make()
    return bucket


def bucket_exists(name: str) -> bool:
    """
    Check if the bucket exists
    :param name:
    Name of the bucket (directory)
    :return:
    Whether this bucket exists
    """
    return os.path.exists(servers.join(name))


# Get the guild ID of a guild
guid = lambda guild_: guild_.id if isinstance(guild_, Guild) else guild_


class Servers(Group):
    @staticmethod
    def get_guild_name(guild_: Guild | int) -> str: return f"g_{guid(guild_)}"

    @staticmethod
    def guild_exists(guild_: Guild | int) -> bool: return bucket_exists(Servers.get_guild_name(guild_))

    def get_guild_bucket(self, guild_: Guild | int, **kwargs) -> Bucket:
        return self.get_bucket(self.get_guild_name(guild_), **kwargs)

    def _init_bucket(self, bucket: Bucket):
        """
        Init a new bucket
        :param bucket:
        The bucket to init
        """
        bucket.clam("settings")
        bucket.clam("users")

    def init_server(self, guild_: Guild | int):
        """
        Init a server bucket
        :param guild_:
        The server (guild)
        """
        self.set_server_setting(guild_, "report_channel_id", -1)
        self.set_server_setting(guild_, "lang", "English")

    def set_server_setting(self, guild_: Guild | int, key: str, value: str | int | bool):
        """
        Set a certain setting from a server
        :param guild_:
        The server (guild)
        :param key:
        Setting to set
        :param value:
        The value to set to
        """
        bucket = self.init_and_get(guild_)
        c = bucket.clam("settings")
        c.exports(key, value)

    def get_server_setting(self, guild_: Guild | int, key: str) -> str:
        """
        Get a certain setting from a server
        :param guild_:
        The server (guild)
        :param key:
        Setting to get
        :return
        The value of the setting
        """
        bucket = self.init_and_get(guild_)
        c = bucket.clam("settings")
        return c.imports(key)

    def init_and_get(self, guild_: Guild | int) -> Bucket:
        """
        Get a server and init it before if it hasn't already been
        :param guild_:
        The server (guild)
        :return:
        The server bucket
        """
        exists = self.guild_exists(guild_)
        x = self.get_guild_bucket(guild_)
        if not exists:
            self.init_server(guild_)
        return x


_check_storage()
servers = Servers(os.path.join(STORAGE, "servers"))
