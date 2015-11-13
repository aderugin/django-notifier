from setuptools import setup, find_packages


setup(
    name='django-notifier',
    version='0.1',
    author='Derugin Anton',
    author_email='anton.derugin@gmail.com',
    packages=['django_notifier'],
    include_package_data=True,
    url='https://github.com/aderugin/django-notifier',
    license='MIT',
    description='Django application for theming notifications (email or sms) in admin panel',
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
