from setuptools import setup

setup(
    name='BlackJack',
    version='',
    packages=['venv.lib.python3.6.site-packages.jws', 'venv.lib.python3.6.site-packages.rsa',
              'venv.lib.python3.6.site-packages.idna', 'venv.lib.python3.6.site-packages.click',
              'venv.lib.python3.6.site-packages.flask', 'venv.lib.python3.6.site-packages.flask.json',
              'venv.lib.python3.6.site-packages.tests', 'venv.lib.python3.6.site-packages.tests.common',
              'venv.lib.python3.6.site-packages.tests.asyncio', 'venv.lib.python3.6.site-packages.Crypto',
              'venv.lib.python3.6.site-packages.Crypto.IO', 'venv.lib.python3.6.site-packages.Crypto.Hash',
              'venv.lib.python3.6.site-packages.Crypto.Math', 'venv.lib.python3.6.site-packages.Crypto.Util',
              'venv.lib.python3.6.site-packages.Crypto.Cipher', 'venv.lib.python3.6.site-packages.Crypto.Random',
              'venv.lib.python3.6.site-packages.Crypto.Protocol', 'venv.lib.python3.6.site-packages.Crypto.SelfTest',
              'venv.lib.python3.6.site-packages.Crypto.SelfTest.IO',
              'venv.lib.python3.6.site-packages.Crypto.SelfTest.Hash',
              'venv.lib.python3.6.site-packages.Crypto.SelfTest.Math',
              'venv.lib.python3.6.site-packages.Crypto.SelfTest.Util',
              'venv.lib.python3.6.site-packages.Crypto.SelfTest.Cipher',
              'venv.lib.python3.6.site-packages.Crypto.SelfTest.Random',
              'venv.lib.python3.6.site-packages.Crypto.SelfTest.Protocol',
              'venv.lib.python3.6.site-packages.Crypto.SelfTest.PublicKey',
              'venv.lib.python3.6.site-packages.Crypto.SelfTest.Signature',
              'venv.lib.python3.6.site-packages.Crypto.PublicKey', 'venv.lib.python3.6.site-packages.Crypto.Signature',
              'venv.lib.python3.6.site-packages.gcloud', 'venv.lib.python3.6.site-packages.gcloud.dns',
              'venv.lib.python3.6.site-packages.gcloud.pubsub', 'venv.lib.python3.6.site-packages.gcloud.logging',
              'venv.lib.python3.6.site-packages.gcloud.storage', 'venv.lib.python3.6.site-packages.gcloud.bigquery',
              'venv.lib.python3.6.site-packages.gcloud.bigtable',
              'venv.lib.python3.6.site-packages.gcloud.bigtable.happybase',
              'venv.lib.python3.6.site-packages.gcloud.bigtable._generated',
              'venv.lib.python3.6.site-packages.gcloud.datastore',
              'venv.lib.python3.6.site-packages.gcloud.datastore._generated',
              'venv.lib.python3.6.site-packages.gcloud.streaming', 'venv.lib.python3.6.site-packages.gcloud.translate',
              'venv.lib.python3.6.site-packages.gcloud.monitoring',
              'venv.lib.python3.6.site-packages.gcloud.error_reporting',
              'venv.lib.python3.6.site-packages.gcloud.resource_manager', 'venv.lib.python3.6.site-packages.google.api',
              'venv.lib.python3.6.site-packages.google.rpc', 'venv.lib.python3.6.site-packages.google.type',
              'venv.lib.python3.6.site-packages.google.logging.type',
              'venv.lib.python3.6.site-packages.google.protobuf',
              'venv.lib.python3.6.site-packages.google.protobuf.util',
              'venv.lib.python3.6.site-packages.google.protobuf.pyext',
              'venv.lib.python3.6.site-packages.google.protobuf.compiler',
              'venv.lib.python3.6.site-packages.google.protobuf.internal',
              'venv.lib.python3.6.site-packages.google.protobuf.internal.import_test_package',
              'venv.lib.python3.6.site-packages.google.longrunning', 'venv.lib.python3.6.site-packages.jinja2',
              'venv.lib.python3.6.site-packages.pyasn1', 'venv.lib.python3.6.site-packages.pyasn1.type',
              'venv.lib.python3.6.site-packages.pyasn1.codec', 'venv.lib.python3.6.site-packages.pyasn1.codec.ber',
              'venv.lib.python3.6.site-packages.pyasn1.codec.cer', 'venv.lib.python3.6.site-packages.pyasn1.codec.der',
              'venv.lib.python3.6.site-packages.pyasn1.codec.native', 'venv.lib.python3.6.site-packages.pyasn1.compat',
              'venv.lib.python3.6.site-packages.certifi', 'venv.lib.python3.6.site-packages.chardet',
              'venv.lib.python3.6.site-packages.chardet.cli', 'venv.lib.python3.6.site-packages.urllib3',
              'venv.lib.python3.6.site-packages.urllib3.util', 'venv.lib.python3.6.site-packages.urllib3.contrib',
              'venv.lib.python3.6.site-packages.urllib3.contrib._securetransport',
              'venv.lib.python3.6.site-packages.urllib3.packages',
              'venv.lib.python3.6.site-packages.urllib3.packages.backports',
              'venv.lib.python3.6.site-packages.urllib3.packages.ssl_match_hostname',
              'venv.lib.python3.6.site-packages.engineio', 'venv.lib.python3.6.site-packages.engineio.async_drivers',
              'venv.lib.python3.6.site-packages.httplib2', 'venv.lib.python3.6.site-packages.pyrebase',
              'venv.lib.python3.6.site-packages.requests', 'venv.lib.python3.6.site-packages.socketio',
              'venv.lib.python3.6.site-packages.werkzeug', 'venv.lib.python3.6.site-packages.werkzeug.debug',
              'venv.lib.python3.6.site-packages.werkzeug.contrib', 'venv.lib.python3.6.site-packages.markupsafe',
              'venv.lib.python3.6.site-packages.python_jwt', 'venv.lib.python3.6.site-packages.itsdangerous',
              'venv.lib.python3.6.site-packages.oauth2client', 'venv.lib.python3.6.site-packages.oauth2client.contrib',
              'venv.lib.python3.6.site-packages.oauth2client.contrib.django_util',
              'venv.lib.python3.6.site-packages.flask_socketio', 'venv.lib.python3.6.site-packages.pyasn1_modules',
              'venv.lib.python3.6.site-packages.requests_toolbelt',
              'venv.lib.python3.6.site-packages.requests_toolbelt.auth',
              'venv.lib.python3.6.site-packages.requests_toolbelt.utils',
              'venv.lib.python3.6.site-packages.requests_toolbelt.cookies',
              'venv.lib.python3.6.site-packages.requests_toolbelt.adapters',
              'venv.lib.python3.6.site-packages.requests_toolbelt.threaded',
              'venv.lib.python3.6.site-packages.requests_toolbelt.multipart',
              'venv.lib.python3.6.site-packages.requests_toolbelt.downloadutils',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.idna',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.pytoml',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.certifi',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.chardet',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.chardet.cli',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.distlib',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.distlib._backport',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.msgpack',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.urllib3',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.urllib3.util',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.urllib3.contrib',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.urllib3.contrib._securetransport',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.urllib3.packages',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.urllib3.packages.backports',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.urllib3.packages.ssl_match_hostname',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.colorama',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.html5lib',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.html5lib._trie',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.html5lib.filters',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.html5lib.treewalkers',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.html5lib.treeadapters',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.html5lib.treebuilders',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.lockfile',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.progress',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.requests',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.packaging',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.cachecontrol',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.cachecontrol.caches',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.webencodings',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._vendor.pkg_resources',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._internal',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._internal.req',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._internal.vcs',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._internal.utils',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._internal.models',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._internal.commands',
              'venv.lib.python3.6.site-packages.pip-10.0.1-py3.6.egg.pip._internal.operations'],
    url='',
    license='',
    author='admin',
    author_email='',
    description=''
)
