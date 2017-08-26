try:
	from setuptools import setup
except ImportError:
	from distutils.core import setup

config = {
	'description': 'Source code for /u/RedditAnalysisBot',
	'author': '/u/atomar94',
	'url': 'https://github.com/atomar94/SubredditAnalysis',
	'download_url': 'https://github.com/atomar94/SubredditAnalysis/archive/master.zip',
	'version': '1.1',
	'install_requires': ['praw', 'requests', 'simpleconfigparser'],
	'packages': [],
	'scripts': [],
	'name': 'SubredditAnalysis'
}

setup(**config)
