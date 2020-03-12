from pybuilder.resources.pyfmu.fmi2logging import Fmi2Logger, Fmi2LogMessage, Fmi2StdLogCats
from pybuilder.resources.pyfmu.fmi2types import Fmi2Status

def test_categoryNotRegistered_notLogged():
    
    logged = False

    def logging_callback(msg : Fmi2LogMessage):
        nonlocal logged 
        logged = True

    logger = Fmi2Logger(callback=logging_callback)
    logger.log("test")

    assert(not logged)

def test_customCategoryRegistered_logged():

    logged = False

    def logging_callback(msg : Fmi2LogMessage):
        nonlocal logged 
        logged = True

    logger = Fmi2Logger(callback=logging_callback)
    logger.register_log_category('a')
    logger.log("hello world!",'a')

    assert(logged)

def test_registerAlias_logged():
    
    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = Fmi2Logger(callback=logging_callback)
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

    logger = Fmi2Logger(callback=logging_callback)
    logger.register_log_category('all',predicate=log_all_predicate)
    
    # different categories
    logger.log('test','a')
    logger.log('test','b')

    # different status
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)

    assert(count == 4)

# standard categories

def test_registerEvents_logEvent_logged():
    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = Fmi2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logEvents])
    
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 6)

def test_registerSingularLinearSystems_logSls_logged():
    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = Fmi2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logSingularLinearSystems])
    
    logger.log('test',category="SingularLinearSystem")
    logger.log('test',category="singularlinearsystem")
    logger.log('test',category="sls")



    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 3)

def test_registerNonLinearSystems_lognls_logged():
    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = Fmi2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logNonlinearSystems])
    
    logger.log('test',category="NonLinearSystems")
    logger.log('test',category="nonlinearsystems")
    logger.log('test',category="nls")

    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 3)

def test_registerLogDynamicStateSelection_logDss_logged():
    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = Fmi2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logDynamicStateSelection])
    
    logger.log('test',category="DynamicStateSelection")
    logger.log('test',category="dynamicstateselection")
    logger.log('test',category="dss")
    
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 3)

def test_registerWarning_logWarning_logged():

    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = Fmi2Logger(callback=logging_callback)
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

    logger = Fmi2Logger(callback=logging_callback)
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

    logger = Fmi2Logger(callback=logging_callback)
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

    logger = Fmi2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logStatusPending])
    
    
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 1)

def test_registerall_logsAll():

    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = Fmi2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logAll])
    
    
    logger.log('test',status=Fmi2Status.ok)
    logger.log('test',status=Fmi2Status.warning)
    logger.log('test',status=Fmi2Status.error)
    logger.log('test',status=Fmi2Status.discard)
    logger.log('test',status=Fmi2Status.fatal)
    logger.log('test',status=Fmi2Status.pending)
    
    assert(count == 6)

# defaults

def test_logDefaultCategory_loggedWithEvent():
    count = 0

    def logging_callback(msg):
        nonlocal count
        count += 1

    logger = Fmi2Logger(callback=logging_callback)
    logger.register_standard_categories([Fmi2StdLogCats.logEvents])
    logger.log('test')


# message stack

def test_len_logIncreasesLength():
    logger = Fmi2Logger()
    logger.register_standard_categories([Fmi2StdLogCats.logAll])

    assert(len(logger) == 0)

    logger.log('test')

    assert(len(logger) == 1)

    logger.log('test')

    assert(len(logger) == 2)

def test_len_popDecreasesLength():
    logger = Fmi2Logger()
    logger.register_standard_categories([Fmi2StdLogCats.logAll])

    assert(len(logger) == 0)

    logger.log('test')

    assert(len(logger) == 1)

    logger.log('test')

    assert(len(logger) == 2)

    logger.pop_messages(1)

    assert(len(logger) == 1)

    logger.pop_messages(1)

    assert(len(logger) == 0)

def test_pop_returnsMessagesFifo():
    logger = Fmi2Logger()
    logger.register_standard_categories([Fmi2StdLogCats.logAll])

    logger.log("a")
    logger.log("b")

    messages = logger.pop_messages(2)
    messages = [m.message for m in messages]
    
    assert(messages == ['a','b'])