import json
import warnings

import contextlib2 as contextlib

import fabricio

from fabricio import utils

from .base import BaseService, Option, Attribute, ServiceError


class ContainerError(ServiceError):
    pass


class ContainerNotFoundError(ContainerError):
    pass


class Container(BaseService):

    command = Attribute()

    stop_timeout = Attribute(default=10)

    user = Option(safe=True)
    publish = Option()
    env = Option(safe=True)
    label = Option(safe=True)
    volume = Option(safe=True)
    link = Option(safe=True)
    add_host = Option(name='add-host', safe=True)
    network = Option(name='net', safe=True)
    restart = Option()
    stop_signal = Option(name='stop-signal', safe=True)

    @utils.default_property
    def info(self):
        command = 'docker inspect --type container {container}'
        info = fabricio.run(
            command.format(container=self),
            abort_exception=ContainerNotFoundError,
        )
        return json.loads(info)[0]

    def delete(
        self,
        delete_image=False,
        delete_dangling_volumes=None,  # deprecated
        **options
    ):
        options = utils.Options(options)

        if delete_dangling_volumes is not None:  # pragma: no cover
            warnings.warn(
                '`delete_dangling_volumes` parameter is deprecated '
                'and will be removed in v0.6, use `volumes` instead',
                RuntimeWarning, stacklevel=2,
            )
            options.setdefault('volumes', delete_dangling_volumes)

        delete_image_callback = delete_image and self.image.get_delete_callback()

        options.setdefault('volumes', True)  # default option
        fabricio.run('docker rm {options} {container}'.format(
            container=self,
            options=options,
        ))

        if delete_image_callback:
            delete_image_callback()

    def run(self, tag=None, registry=None, account=None):
        self.image[registry:tag:account].run(
            command=self.command,
            temporary=False,
            name=self,
            options=self.options,
        )

    def execute(
        self,
        command=None,
        quiet=True,
        use_cache=False,
        options=(),
    ):
        if not command:
            raise ValueError('Must provide command to execute')

        options = utils.Options(options)
        options.setdefault('tty', True)
        options.setdefault('interactive', True)

        exec_command = 'docker exec {options} {container} {command}'
        return fabricio.run(
            exec_command.format(
                container=self,
                command=command,
                options=options,
            ),
            quiet=quiet,
            use_cache=use_cache,
        )

    def start(self):
        command = 'docker start {container}'
        fabricio.run(command.format(container=self))

    def stop(self, timeout=None):
        if timeout is None:
            timeout = self.stop_timeout
        command = 'docker stop --time {timeout} {container}'
        fabricio.run(command.format(container=self, timeout=timeout))

    def reload(self, timeout=None):
        if timeout is None:
            timeout = self.stop_timeout
        command = 'docker restart --time {timeout} {container}'
        fabricio.run(command.format(container=self, timeout=timeout))

    def rename(self, new_name):
        command = 'docker rename {container} {new_name}'
        fabricio.run(command.format(container=self, new_name=new_name))
        self.name = new_name

    def signal(self, signal):
        command = 'docker kill --signal {signal} {container}'
        fabricio.run(command.format(container=self, signal=signal))

    @property
    def image_id(self):
        return self.info['Image']

    def update(self, tag=None, registry=None, account=None, force=False):
        if not force:
            try:
                if self.image_id == self.image[registry:tag:account].info['Id']:
                    self.start()  # force starting container
                    return False
            except ContainerNotFoundError:
                pass
        obsolete_container = self.get_backup_version()
        with contextlib.suppress(fabricio.Error):
            obsolete_container.delete(delete_image=True)
        try:
            backup_container = self.fork()
            backup_container.rename(obsolete_container.name)
        except fabricio.Error:
            pass  # current container not found
        else:
            backup_container.stop()
        self.run(tag=tag, registry=registry, account=account)
        return True

    def revert(self):
        backup_container = self.get_backup_version()
        try:
            backup_container.info
        except ContainerNotFoundError:
            raise ContainerError('backup container not found')
        self.stop()
        backup_container.start()
        self.delete(delete_image=True)
        backup_container.rename(self.name)

    def get_backup_version(self):
        return self.fork(name='{container}_backup'.format(container=self))

    def destroy(self):
        self.delete(force=True, delete_image=True)
        with contextlib.suppress(fabricio.Error):
            self.get_backup_version().delete(force=True, delete_image=True)
