from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from logging import Logger
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from collections.abc import Callable
from injector import inject, singleton, Module, provider

from server import Configuration
from .db_model import _Table

type OrmSessionFactory = Callable[..., Session]

class BindDbClient(Module):
	@provider
	@singleton
	def orm_session_factory(self, db_client: Engine) -> OrmSessionFactory:
		return lambda : Session(db_client)

	@provider
	@singleton
	def db_client(self, config: Configuration, log: Logger) -> Engine:
		engine = create_engine(f"sqlite:///{config.sqlite_path()}")

		SQLAlchemyInstrumentor().instrument(
			engine = engine,
		)
		return engine

@inject
def migrate_db(engine: Engine, config: Configuration, log: Logger):
	try:
		_Table.metadata.create_all(engine, checkfirst = False)
	except OperationalError as e:
		log.warning(f"Could not migrate db schema. Reason: {e._message()}")
	
	# this allows adding new items to the config w/o deleting the sqlite file (not deleting)
	for item in config.item_list():
		try:
			with Session(engine) as session, session.begin():
				session.add(item)
				session.commit()
		except IntegrityError as e:
			log.warning(f"Could not add an item from config. Reason: {e._message()}")


