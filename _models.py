class Glo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    desc = db.Column(db.String)

class Slo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    glo_id = db.Column(db.Integer, db.ForeignKey('glo.id'))
    ss_id = db.Column(db.Integer, db.ForeignKey('substrand.id'))
    desc = db.Column(db.String)

    glo = db.relationship('Glo', backref='slos')
    substrand = db.relationship('Substrand', backref='slos')

class LearningArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    la_name = db.Column(db.String(128), unique=True)

    __table_args__ = (db.Index('idx_la_name', 'la_name'), )

class Grade(db.Model):
    gr_num = db.Column(db.Integer, primary_key=True)
    la_id = db.Column(db.Integer, db.ForeignKey('learning_area.id'))

    learning_area = db.relationship('LearningArea', backref='grades')

    __table_args__ = (db.Index('idx_gr_num', 'gr_num'), )

class Strand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gr_num = db.Column(db.Integer, db.ForeignKey('grade.gr_num'))
    st_name = db.Column(db.String(256))

    grade = db.relationship('Grade', backref='strands')

class Substrand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    st_id = db.Column(db.Integer, db.ForeignKey('strand.id'))
    ss_name = db.Column(db.String(256))

    strand = db.relationship('Strand', backref='substrands')

class Indicator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ss_id = db.Column(db.Integer, db.ForeignKey('substrand.id'))
    code = db.Column(db.String(256), unique=True)
    desc = db.Column(db.String)

    substrand = db.relationship('Substrand', backref='indicators')

class StudentAsst(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asst_type = db.Column(db.String(256))
    ref = db.Column(db.String(256))
    level = db.Column(db.String(256))
    co_id = db.Column(db.Integer, db.ForeignKey('content_obj.id'))

    content_obj = db.relationship('ContentObj', backref='student_assts')
    indicators = db.relationship('Indicator', secondary='sa_ind', backref='student_assts')

class Publisher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pu_name = db.Column(db.String(128))
    email = db.Column(db.String(128), unique=True)
    address = db.Column(db.String)
    desc = db.Column(db.String)

    __table_args__ = (db.Index('idx_pu_name', 'pu_name'), )

class TechnicalEval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_available = db.Column(db.Boolean)
    aggregate = db.Column(db.Integer)
    notes = db.Column(db.String)
    added = db.Column(db.DateTime, server_default=db.func.now())
    modified = db.Column(db.DateTime, onupdate=db.func.now())

class ContentEval(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    difficulty = db.Column(db.String(256))
    interactive = db.Column(db.String(256))
    assessment_feedback = db.Column(db.String(256))
    outcomes = db.Column(db.String(256))
    pictures = db.Column(db.String(256))
    teachers_guide = db.Column(db.String(256))
    kicd = db.Column(db.String(256))
    navigation = db.Column(db.String(256))
    aggregate = db.Column(db.String(256))
    added = db.Column(db.DateTime, server_default=db.func.now())
    modified = db.Column(db.DateTime, onupdate=db.func.now())
    status = db.Column(db.String(256), default='under_review')

    __table_args__ = (db.Index('idx_added', 'added'), db.Index('idx_status', 'status'), db.Index('idx_aggregate', 'aggregate'), )

class ContentObj(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    co_type = db.Column(db.String(256))
    pu_id = db.Column(db.Integer, db.ForeignKey('publisher.id'))
    title = db.Column(db.String(256))
    ref = db.Column(db.String(256))
    curr_type = db.Column(db.String(256))
    published = db.Column(db.DateTime)
    added = db.Column(db.DateTime, server_default=db.func.now())
    modified = db.Column(db.DateTime, onupdate=db.func.now())

    publisher = db.relationship('Publisher', backref='content_objs')
    slos = db.relationship('Slo', secondary='co_slo', backref='content_objs')
    technical_evals = db.relationship('TechnicalEval', secondary='co_te', backref='content_objs')
    content_evals = db.relationship('ContentEval', secondary='co_ce', backref='content_objs')

    __table_args__ = (db.Index('idx_pu_id', 'pu_id'), db.Index('idx_published', 'published'), )

co_slo = db.Table('co_slo', 
    db.Column('co_id', db.Integer, db.ForeignKey('content_obj.id')),
    db.Column('slo_id', db.Integer, db.ForeignKey('slo.id'))
)

co_te = db.Table('co_te', 
    db.Column('co_id', db.Integer, db.ForeignKey('content_obj.id')),
    db.Column('te_id', db.Integer, db.ForeignKey('technical_eval.id'))
)

co_ce = db.Table('co_ce', 
    db.Column('co_id', db.Integer, db.ForeignKey('content_obj.id')),
    db.Column('ce_id', db.Integer, db.ForeignKey('content_eval.id'))
)

sa_ind = db.Table('sa_ind', 
    db.Column('sa_id', db.Integer, db.ForeignKey('student_asst.id')),
    db.Column('ind_id', db.Integer, db.ForeignKey('indicator.id'))
)

