class StepsLoader(object):
    @staticmethod
    def dependencies():
        deps = {}

        deps['python-docker'] = {
            'library': 'docker',
            'package': 'python-docker-py',
            'command': 'rpm -q python-docker-py',
            'fedora': {
                'package': 'python3-docker',
                'command': 'rpm -q python3-docker'
            }
        }

        deps['behave'] = {
            'library': 'behave',
            'package': 'python2-behave',
            'command': 'rpm -q python2-behave',
            'fedora': {
                'package': 'python3-behave',
                'command': 'rpm -q python3-behave'
            }
        }

        deps['requests'] = {
            'library': 'requests',
            'package': 'python-requests',
            'command': 'rpm -q python-requests',
            'fedora': {
                'package': 'python3-requests',
                'command': 'rpm -q python3-requests'
            }
        }

        deps['lxml'] = {
            'library': 'lxml',
            'package': 'python-lxml',
            'command': 'rpm -q python-lxml',
            'fedora': {
                'package': 'python3-lxml',
                'command': 'rpm -q python3-lxml'
            }
        }

        deps['s2i'] = {
            'binary': 's2i',
            'command': 's2i version'
        }

        return deps
