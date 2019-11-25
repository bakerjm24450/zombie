General Information
===================

This is the code for our escape room zombie.

Author: Mac Baker

Revisions:
	1.0 -- Initial version
	1.0.1 -- changes to web page
	1.0.2 -- added casket and candle info to web page

Installation and update instructions:

To update the web pages, do the following:
1. Activte the virtual environment for development:
	~/.virtualenvs/zombieweb/bin/activate
2. Update the version number in setup.py
3. Make a wheel for distribution
	python setup.py bdist_wheel
4. Copy to /var/www for installation 
	sudo -u www-data cp dist/zombieweb-<ver>.whl /var/www/zombieweb
5. From another window, go to /var/www/zombieweb
6. Activate the venv there
	. venv/bin/activate
7. Uninstall old version
	sudo -u www-data /var/www/zombieweb/venv/bin/pip uninstall zombieweb
8. Install new version
	sudo -u www-data /var/www/zombieweb/venv/bin/pip install zombieweb-<ver>.whl
9. Restart apache server
	sudo systemctl restart apache2
