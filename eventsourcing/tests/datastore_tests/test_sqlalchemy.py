from tempfile import NamedTemporaryFile
from uuid import uuid4

from sqlalchemy.exc import OperationalError, ProgrammingError

from eventsourcing.infrastructure.datastore import DatastoreTableError
from eventsourcing.infrastructure.sqlalchemy.records import IntegerSequencedRecord, \
    TimestampSequencedRecord, SnapshotRecord, Base
from eventsourcing.infrastructure.sqlalchemy.datastore import DEFAULT_SQLALCHEMY_DB_URI, SQLAlchemyDatastore, \
    SQLAlchemySettings
from eventsourcing.tests.datastore_tests.base import AbstractDatastoreTestCase, DatastoreTestCase


class SQLAlchemyDatastoreTestCase(AbstractDatastoreTestCase):
    use_named_temporary_file = False
    connection_strategy = 'plain'

    def construct_datastore(self):
        if self.use_named_temporary_file:
            self.temp_file = NamedTemporaryFile('a', delete=True)
            uri = 'sqlite:///' + self.temp_file.name
        else:
            uri = DEFAULT_SQLALCHEMY_DB_URI

        # kwargs = {}
        # if not self.use_named_temporary_file:
            # kwargs['connect_args'] = {'check_same_thread':False}
            # kwargs['poolclass'] = StaticPool

        return SQLAlchemyDatastore(
            base=Base,
            settings=SQLAlchemySettings(uri=uri),
            tables=(IntegerSequencedRecord, TimestampSequencedRecord, SnapshotRecord),
            connection_strategy=self.connection_strategy,
            # **kwargs
        )


class TestSQLAlchemyDatastore(SQLAlchemyDatastoreTestCase, DatastoreTestCase):
    def list_records(self):
        try:
            query = self.datastore.session.query(IntegerSequencedRecord)
            return list(query)
        except (OperationalError, ProgrammingError) as e:
            # OperationalError from sqlite, ProgrammingError from psycopg2.
            self.datastore.session.rollback()
            raise DatastoreTableError(e)
        finally:
            self.datastore.session.close()

    def create_record(self):
        try:
            record = IntegerSequencedRecord(
                sequence_id=uuid4(),
                position=0,
                topic='topic',
                data='{}'
            )
            self.datastore.session.add(record)
            self.datastore.session.commit()
        except (OperationalError, ProgrammingError) as e:
            self.datastore.session.rollback()
            raise DatastoreTableError(e)
        return record
