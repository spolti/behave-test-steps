class StepsLoader(object):
    @staticmethod
    def dependencies(params=None):
        deps = {}

        deps['python-docker'] = {
            'library': 'docker',
            'package': 'python-docker-py',
            'fedora': {
                'package': 'python3-docker',
            }
        }

        deps['behave'] = {
            'library': 'behave',
            'package': 'python2-behave',
            'fedora': {
                'package': 'python3-behave',
            }
        }

        deps['requests'] = {
            'library': 'requests',
            'package': 'python-requests',
            'fedora': {
                'package': 'python3-requests',
            }
        }

        deps['lxml'] = {
            'library': 'lxml',
            'package': 'python-lxml',
            'fedora': {
                'package': 'python3-lxml',
            }
        }

        deps['s2i'] = {
            'executable': 's2i'
        }

        return deps
