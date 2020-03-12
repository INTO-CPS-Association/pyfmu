from pybuilder.resources.pyfmu.fmi2logging import FMI2Logger, FMI2LogMessage
from pybuilder.resources.pyfmu.fmi2types import Fmi2Status

def test_categoryNotRegistered_notLogged():
    
    logged = False

    def logging_callback(msg : FMI2LogMessage):
        nonlocal logged 
        logged = True

    logger = FMI2Logger(callback=logging_callback)
    logger.log(Fmi2Status.ok,'pyfmu',"test")

    assert(not logged)

def test_customCategoryRegistered_logged():

    logged = False

    def logging_callback(msg : FMI2LogMessage):
        nonlocal logged 
        logged = True

    logger = FMI2Logger(callback=logging_callback)
    logger.register_log_category('a')
    logger.log("hello world!",'a')

    assert(logged)

def test_alias_logged():
    
    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = FMI2Logger(callback=logging_callback)
    logger.register_log_category('ab',aliases={'a','b'})
    logger.log('test','a')

