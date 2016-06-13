import logging, sys

LO = logging.getLogger('')
LO.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")  
ch = logging.StreamHandler(sys.stderr)
ch.setFormatter(formatter)  
LO.addHandler(ch)
log = LO.info

