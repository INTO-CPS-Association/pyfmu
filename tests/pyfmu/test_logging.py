from pybuilder.resources.pyfmu.fmi2logging import FMI2Logger, FMI2LogMessage, Fmi2StdLogCats
from pybuilder.resources.pyfmu.fmi2types import Fmi2Status

def test_categoryNotRegistered_notLogged():
    
    logged = False

    def logging_callback(msg : FMI2LogMessage):
        nonlocal logged 
        logged = True

    logger = FMI2Logger(callback=logging_callback)
    logger.log("test")

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

def test_registerAlias_logged():
    
    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = FMI2Logger(callback=logging_callback)
    logger.register_log_category('ab',aliases={'a','b'})
    logger.log('test','a')
    logger.log('test','b')
    
    assert(count == 2)



def test_logAllPredicate_allLogged():

    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1
    
    def log_all_predicate(category : str) -> bool:
        return True

    logger = FMI2Logger(callback=logging_callback)
    logger.register_log_category('all',predicate=log_all_predicate)
    
    # different categories
    logger.log('test','a')
    logger.log('test','b')

    # different status
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)

    assert(count == 4)

# standard categories

def test_registerWarning_logWarning_logged():

    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = FMI2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logStatusWarning])
    
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 1)

def test_registerError_logError_logged():

    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = FMI2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logStatusError])
    
    
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 1)

def test_registerFatal_logFatal_logged():

    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = FMI2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logStatusError])
    
    
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 1)

def test_registerPending_logPending_logged():

    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = FMI2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logStatusPending])
    
    
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 1)

def test_logDefaultCategory_loggedWithEvent():
    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = FMI2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logEvents])
    logger.log('test')