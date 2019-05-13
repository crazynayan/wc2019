from firebase_admin import firestore
from google.cloud.exceptions import NotFound


class FirestoreModel:
    # COLLECTION should ALWAYS be overridden by the base class with the collection name
    COLLECTION = 'firestore'
    # DEFAULT FIELD can be overridden if the default name of the field needs a change
    DEFAULT = 'name'
    BATCH = None
    ORDER_ASCENDING = firestore.Query.ASCENDING
    ORDER_DESCENDING = firestore.Query.DESCENDING
    try:
        db = firestore.client()
    except ValueError:
        db = None

    def __init__(self, field_value=None):
        self.doc_id = None
        setattr(self, self.DEFAULT, field_value)

    def __repr__(self):
        return f'<{self.DEFAULT}: {getattr(self, self.DEFAULT)}>'

    @classmethod
    def init_db(cls, db_app=None):
        try:
            cls.db = firestore.client(db_app)
        except ValueError:
            return False
        return True

    def to_dict(self):
        model_dict = self.__dict__.copy()
        try:
            del model_dict['doc_id']
        except KeyError:
            pass
        return model_dict

    @classmethod
    def from_dict(cls, source):
        if cls.DEFAULT not in source:
            return None
        model = cls(source[cls.DEFAULT])
        for field in model.__dict__:
            if field in source:
                setattr(model, field, source[field])
        return model

    def create(self):
        doc = self.db.collection(self.COLLECTION).add(self.to_dict())
        self.doc_id = doc[1].id
        return self

    def update(self, doc_id=None):
        if doc_id:
            self.doc_id = doc_id
        elif not self.doc_id:
            return None
        self.db.collection(self.COLLECTION).document(self.doc_id).set(self.to_dict())
        return self

    @classmethod
    def read(cls, doc_id=None):
        if not doc_id:
            return None
        try:
            doc = cls.db.collection(cls.COLLECTION).document(doc_id).get()
        except NotFound:
            return None
        if not doc.exists:
            return None
        model = cls.from_dict(doc.to_dict())
        model.doc_id = doc.id
        return model

    def refresh(self):
        if not self.doc_id:
            return False
        try:
            doc = self.db.collection(self.COLLECTION).document(self.doc_id).get()
        except NotFound:
            return False
        if not doc.exists:
            return False
        doc_dict = doc.to_dict()
        for field in doc_dict:
            if field in self.__dict__:
                setattr(self, field, doc_dict[field])
        return True

    def get_doc(self, transaction=None):
        # Returns the document reference if no transaction provided else it will provided a transactional doc
        if not self.doc_id:
            return None, None
        doc_ref = self.db.collection(self.COLLECTION).document(self.doc_id)
        doc = None
        if transaction:
            try:
                doc = self.db.collection(self.COLLECTION).document(self.doc_id).get(transaction=transaction)
            except NotFound:
                pass
            if doc and not doc.exists:
                doc = None
        return doc_ref, doc

    def delete(self, doc_id=None):
        if doc_id:
            self.doc_id = doc_id
        elif not self.doc_id:
            return None
        self.db.collection(self.COLLECTION).document(self.doc_id).delete()
        self.doc_id = None
        return self

    @classmethod
    def get_all(cls):
        docs = cls.db.collection(cls.COLLECTION).stream()
        models = list()
        for doc in docs:
            model = cls.from_dict(doc.to_dict())
            model.doc_id = doc.id
            models.append(model)
        return models

    @classmethod
    def query(cls, **kwargs):
        doc_ref = cls.db.collection(cls.COLLECTION)
        for field in kwargs:
            if field in cls().__dict__ and field != 'doc_id':
                doc_ref = doc_ref.where(field, '==', kwargs[field])
        docs = doc_ref.stream()
        models = list()
        for doc in docs:
            model = cls.from_dict(doc.to_dict())
            model.doc_id = doc.id
            models.append(model)
        return models

    @classmethod
    def order_by(cls, *criteria, query={}):
        doc_ref = cls.db.collection(cls.COLLECTION)
        if query:
            for field in query:
                if field in cls().__dict__ and field != 'doc_id':
                    doc_ref = doc_ref.where(field, '==', query[field])
        for criterion in criteria:
            field = None
            order = None
            if isinstance(criterion, str):
                field = criterion
                order = cls.ORDER_ASCENDING
            elif isinstance(criterion, tuple) and \
                    len(criterion) >= 2 and \
                    isinstance(criterion[0], str) and \
                    criterion[1] in (cls.ORDER_DESCENDING, cls.ORDER_ASCENDING):
                field = criterion[0]
                order = criterion[1]
            if order:
                doc_ref = doc_ref.order_by(field, direction=order)
        # Multiple criteria for order will raise an exception if composite index not defined.
        # The exception is NOT caught here since it will help the developer to create the composite index
        # All scenarios for multiple order_by is recommended to be tested in unittest.
        docs = doc_ref.stream()
        models = list()
        for doc in docs:
            model = cls.from_dict(doc.to_dict())
            model.doc_id = doc.id
            models.append(model)
        return models

    @classmethod
    def query_first(cls, **kwargs):
        doc_ref = cls.db.collection(cls.COLLECTION)
        for field in kwargs:
            if field in cls().__dict__ and field != 'doc_id':
                doc_ref = doc_ref.where(field, '==', kwargs[field])
        docs = doc_ref.limit(1).stream()
        try:
            doc = next(docs)
        except StopIteration:
            return None
        model = cls.from_dict(doc.to_dict())
        model.doc_id = doc.id
        return model

    @classmethod
    def delete_all(cls):
        for doc in cls.db.collection(cls.COLLECTION).stream():
            doc.reference.delete()

    @classmethod
    def init_batch(cls):
        cls.BATCH = cls.db.batch()

    def update_batch(self):
        if not self.doc_id:
            return None
        if not self.BATCH:
            self.BATCH = self.db.batch()
        model_ref = self.db.collection(self.COLLECTION).document(self.doc_id)
        self.BATCH.set(model_ref, self.to_dict())
        return self

    @classmethod
    def commit_batch(cls):
        if not cls.BATCH:
            return False
        cls.BATCH.commit()
        cls.BATCH = None
        return True



