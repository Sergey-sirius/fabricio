# Fabricio: Building Docker images

This example shows how to deploy configuration consisting of a single container based on custom image which automatically built from provided [Dockerfile](Dockerfile).

## Requirements
* Fabricio 0.3.17 or greater
* [Vagrant](https://www.vagrantup.com)
* One from the [list of Vagrant supported providers](https://www.vagrantup.com/docs/providers/) (this example was tested with [VirtualBox](https://www.virtualbox.org/))
* [Docker](https://www.docker.com/products/overview) for Linux/Mac/Windows
* Docker registry which runs locally on 5000 port, this can be reached out by executing following docker command: `docker run --name registry --publish 5000:5000 --detach registry:2`

### Virtual Machine creation

Run `vagrant up` and wait until VM will be created.

## Files
* __Dockerfile__, used for building image
* __fabfile.py__, Fabricio configuration
* __README.md__, this file
* __Vagrantfile__, Vagrant config

## List of available commands

    fab --list

## Deploy

    fab my_nginx
    
At first, this will initiate creation of a new Virtual Machine (if not created yet) using `Vagrant` configuration. Then deploy itself will start.

## Parallel execution

Any Fabricio command can be executed in parallel mode. This mode provides advantages when you have more then one host to deploy to. Use `--parallel` option if you want to run command on all hosts simultaneously:

    fab --parallel my_nginx

## Customization

See also "Hello, World" [Customization](../hello_world/#customization) section.

### Custom `Dockerfile`

You can provide custom folder with `Dockerfile` by passing `build_path` parameter:

    build_path='path_to_folder_with_dockerfile'

## Issues

* If you see warnings in `Vagrant` logs about Guest Extensions version is not match VirtualBox version try to install `vagrant-vbguest` plugin that automatically installs Guest Extensions of version which corresponds to your version of VirtualBox: `vagrant plugin install vagrant-vbguest`
* Windows users may fall into trouble with `VirtualBox` and `Hyper-V`, the latter is used by "native" Docker for Windows. Try to disable Hyper-V and use [Docker Toolbox](https://www.docker.com/products/docker-toolbox) instead in such case
