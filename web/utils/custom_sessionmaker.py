# import the scoped_session function from sqlalchemy.orm
from sqlalchemy import Engine
from sqlalchemy.orm import scoped_session
# import the sessionmaker function from sqlalchemy.orm
from sqlalchemy.orm import sessionmaker
# create a sessionmaker object with some options


# use the session in your request container
class RequestContainer(object):
    def __init__(self, request, *args, **kwargs):
        self.s = Session()

    def safe_commit(self):
        try:
            self.s.commit()
        except:
            self.s.rollback()
            raise

    def __del__(self):
        if self.s:
            try:
                self.s.commit()
            except:
                self.s.rollback()
                raise

            if not RUNNING_DEVSERVER:
                Session.remove()
                self.s = None



# create a sessionmaker object with some options
sessionmaker = sessionmaker(autoflush=True, bind=Engine, expire_on_commit=False)
# create a scoped session with expire_on_commit=False
Session = scoped_session(sessionmaker(autoflush=True, bind=Engine, expire_on_commit=False))


# create a scoped_session object using the sessionmaker object
Session = scoped_session(sessionmaker)

# use the Session object to access the session methods and attributes
session = Session() # get the current session for the current thread
session.add(some_object) # add an object to the session
session.commit() # commit the session
session.close() # close the session