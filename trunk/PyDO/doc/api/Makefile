EPYDOC=/usr/bin/epydoc

html:
	PYTHONPATH=../../src ${EPYDOC} -o html -n PyDO2 -u http://skunkweb.org/pydo.html  ../../src/PyDO/

clean:
	-rm -fR html

.PHONY: html clean