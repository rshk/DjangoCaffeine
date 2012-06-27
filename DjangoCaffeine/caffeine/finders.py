"""
:author: samu
:created: 6/28/12 12:02 AM
"""

## todo: add support for coffeescript
## todo: add support collecting static files -> implement listing!
## todo: implement other methods too..

from django.contrib.staticfiles.finders import BaseFinder
from django.core.exceptions import SuspiciousOperation
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage
from django.utils._os import safe_join
import os
from django.conf import settings
from django.utils.datastructures import SortedDict

from django.contrib.staticfiles import utils
from django.utils.importlib import import_module


class CoffeeAppStaticStorage(FileSystemStorage):
    """
    A file system storage backend that takes an app module and works
    for the ``static`` directory of it.
    """
    prefix = None
    source_dir = 'static-coffee'
    build_dir = 'static-coffee/build'

    def __init__(self, app, *args, **kwargs):
        """
        Returns a static file storage if available in the given app.
        """
        # app is the actual app module
        mod = import_module(app)
        mod_path = os.path.dirname(mod.__file__)
        #self.mod_path = mod_path

        location = os.path.join(mod_path, self.build_dir)
        self.source_location = os.path.join(mod_path, self.source_dir)

        super(CoffeeAppStaticStorage, self).__init__(location, *args, **kwargs)

    def _build_file(self, name, buildfile=None):
        _sourcefile = self.path(self._get_source_path(name), self.source_location)
        _buildfile = buildfile or self.path(name, self.location)

        import subprocess
        from django.conf import settings
        ctx = {
            'src': _sourcefile,
            'dest': _buildfile,
            'destdir': os.path.dirname(_buildfile),
            }

        try:
            os.makedirs(ctx['destdir']) # make sure destination directory exists
        except OSError, e:
            if e.errno == 17: ## file exists
                pass
            else:
                raise

        if _sourcefile.endswith('.scss'):
            subprocess.call(list([x % ctx for x in settings.CAFFEINE_SCSS_COMPILER]))
        elif _sourcefile.endswith('.coffee'):
            subprocess.call(list([x % ctx for x in settings.CAFFEINE_COFFEE_COMPILER]))
        else:
            raise ValueError("Unsupported file type (cannot compile)")
        return _buildfile

    def _open(self, name, mode='rb'):
        print "Try to open %s" % name
        ## todo: compile only if source is newer!
        _sourcefile = self.path(self._get_source_path(name), self.source_location)
        _buildfile = self._build_file(name)
        return File(open(_buildfile, mode))

    def exists(self, name):
        print "Checking whether %s exists" % name

        ## This is the only place where we have the opportunity to build the goddamn file..

        #if not os.path.exists(self.path(name, self.location)):
        #    return False

        if not os.path.exists(self.path(self._get_source_path(name), self.source_location)):
            return False

        ## try to build..
        self._build_file(name, self.path(name, self.location))
        return True

    def _get_source_path(self, name):
        """
        Convert something like "path/to/file.css" to "path/to/file.scss"
        """
        if name.endswith('.css'):
            name = name[:-4] + ".scss"
        elif name.endswith('.js'):
            name = name[:-3] + ".coffee"
        return name

    def path(self, name, base=None):
        try:
            path = safe_join(base or self.location, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
        return os.path.normpath(path)


class AppDirectoriesCoffeeFinder(BaseFinder):
    """
    A static files finder that looks in the directory of each app as
    specified in the source_dir attribute of the given storage class.
    """
    storage_class = CoffeeAppStaticStorage

    def __init__(self, apps=None, *args, **kwargs):
        # The list of apps that are handled
        self.apps = []
        # Mapping of app module paths to storage instances
        self.storages = SortedDict()
        if apps is None:
            apps = settings.INSTALLED_APPS
        for app in apps:
            app_storage = self.storage_class(app)
            if os.path.isdir(app_storage.location):
                self.storages[app] = app_storage
                if app not in self.apps:
                    self.apps.append(app)
        super(AppDirectoriesCoffeeFinder, self).__init__(*args, **kwargs)

    def list(self, ignore_patterns):
        """
        List all files in all app storages.
        """
        for storage in self.storages.itervalues():
            if storage.exists(''):  # check if storage location exists
                for path in utils.get_files(storage, ignore_patterns):
                    yield path, storage

    def find(self, path, all=False):
        """
        Looks for files in the app directories.
        """
        matches = []
        for app in self.apps:
            match = self.find_in_app(app, path)
            if match:
                if not all:
                    return match
                matches.append(match)
        return matches

    def find_in_app(self, app, path):
        """
        Find a requested static file in an app's static locations.
        """
        storage = self.storages.get(app, None)
        if storage:
            if storage.prefix:
                prefix = '%s%s' % (storage.prefix, os.sep)
                if not path.startswith(prefix):
                    return None
                path = path[len(prefix):]
                # only try to find a file if the source dir actually exists
            if storage.exists(path):
                matched_path = storage.path(path)
                if matched_path:
                    return matched_path


