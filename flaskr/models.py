from flask_login import UserMixin, user_logged_in
from flaskr import db
from datetime import datetime
from sqlalchemy.ext.associationproxy import association_proxy


STUDENT_ID = 1
STAFF_ID = 2
ADMIN_ID = 3


class GroupMembers(db.Model):
    __tablename__ = "group_members"
    user_id = db.Column('user_id', db.String, db.ForeignKey('user.user_id'), primary_key=True)
    group_id = db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
    group_hours = db.Column('group_hours', db.Numeric())

    user = db.relationship("User", back_populates="groups")
    group = db.relationship("Group", back_populates="users")

    @classmethod
    def load(cls, user_id, group_id):
        return cls.query.filter_by(user_id=user_id, group_id=group_id).first()

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column("user_id", db.String(), primary_key=True)
    google_id = db.Column(db.String(), unique=True)
    first_name = db.Column(db.String())
    last_name = db.Column(db.String())
    email = db.Column(db.String())
    form_class = db.Column(db.String())
    role_id = db.Column("role", db.Integer(), db.ForeignKey('user_role.id'))
    is_active = db.Column(db.Boolean())
    photo = db.Column(db.String())
    total = db.Column(db.Numeric())

    role = db.relationship("UserRole", back_populates="role_group")
    hours = db.relationship("Log", back_populates="user", foreign_keys="Log.user_id")
    groups = db.relationship("GroupMembers", back_populates="user")

    groups_proxy = association_proxy('groups', 'group') #bypass GroupMember objects to get a list of user's groups
    #ERASE IF NO LONGER NEEDED
    log_group_proxy = association_proxy('hours', 'group') #bypass Log objects to get a list of groups in user's log

    @classmethod
    def load(cls, email):
        """Loads a user from the database using their email."""
        return cls.query.filter_by(email=email).first()

    @staticmethod
    def enrol(user_id, email, role, form_class=None):
        """Adds a user to the database so that they can then sign in with Google."""
        #NOT TESTED
        new_user = User(id=user_id, email=email, role_id=role, form_class=form_class, total=0)
        db.session.add(new_user)
        db.session.commit()
        return

    @staticmethod
    def is_user(email):
        """Checks to see if the user attempting to log in to the site is authorised and in the database.
        Does not check whether the user has logged in before."""
        person = User.load(email)
        return person != None
        #CHECK IF THE != NONE CAN BE DONE NICELY

    @classmethod
    def get_teachers(cls):
        """Returns a list of all teachers in the database."""
        return cls.query.filter(cls.role_id.in_((STAFF_ID, ADMIN_ID))).order_by(cls.last_name)

    def update(self, unique_id, first_name, last_name, picture):
        """Updates a user's record in the database with account information retrieved from Google"""
        self.google_id = unique_id
        self.is_active = True
        self.first_name, self.last_name = (first_name, last_name)
        self.photo = picture
        db.session.commit()
        return
    
    def name(self):
        return f"{self.first_name} {self.last_name}"

    def get_group_options(self):
        """returns a list of the groups a user is in as (id, name) tuples for use in forms"""
        return [(group_assoc.group.id, group_assoc.group.name) for group_assoc in self.groups]

    @classmethod
    def get_teacher_options(cls):
        """returns a list of all teachers in the school as (id, name) tuples for use in forms"""
        return [(teacher.id, f"{teacher.first_name} {teacher.last_name}") for teacher in cls.get_teachers()]

    def get_disabled_groups(self):
        """returns a list of the ids of groups which a user has logged hours under. We don't want them to be
        able to be removed from the group if they've logged hours under it"""
        group_ids = []
        for item in self.hours:
            group_ids.append(item.group_id)
        return group_ids
    
    def join_groups(self, groups_join):
        """takes a list of group ids and a user and adds a new GroupMember object to the database for each one,
         adding them to those groups"""
        for group_id in groups_join:
            group = GroupMembers(group_id=int(group_id), user_id=self.id, group_hours=0)
            db.session.add(group)
        db.session.commit()

    def leave_groups(self, groups_leave):
        """takes a list of group ids and a user and removes their GroupMember object to the 
        database for each one, removing them from those groups"""
        for group_id in groups_leave:
            group = GroupMembers.load(group_id=int(group_id), user_id=self.id)
            db.session.delete(group)
        db.session.commit()

class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), unique=True)
    access_code = db.Column(db.String(), unique=True)

    hours = db.relationship("Log", back_populates="group")
    users = db.relationship("GroupMembers", back_populates="group")

    def user_total(self, user):
        """Takes a user object and finds how many hours the user has completed in that group."""
        group_user = GroupMembers.load(user.id, self.id)
        return group_user.group_hours

    @classmethod
    def load(cls, id):
        """Loads a group from the database using its ID"""
        return cls.query.filter_by(id=id).first()

    @classmethod
    def get_all(cls):
        """Loads all groups in the database"""
        return cls.query.all()

    @classmethod
    def get_group_options(cls):
        """returns a sorted list of the groups in the database (id, name) tuples for use in forms"""
        groups = [(group.id, group.name) for group in cls.get_all()]
        #sort the values alphabetically by their name 
        groups.sort(key = lambda x: x[1])
        return groups

    def get_teachers(self):
        """Uses the group ID to return a list of user objects of the teachers in a particualr group"""
        teachers = User.query.join(User.groups).filter(GroupMembers.group_id == self.id, User.role_id.in_((STAFF_ID, ADMIN_ID))).all()
        return teachers

    def get_teachers_string(self):
        """Gives the teachers of a group in a format suitable for display"""
        teachers = self.get_teachers()
        teacher_names = []
        for teacher in teachers:
            teacher_names.append(teacher.first_name + " " + teacher.last_name)
        return ", ".join(teacher_names)

    def get_user_log(self, user):
        """takes a user object and returns a list of all of a users hours in that group"""
        logged_items = Log.query.filter(Log.user_id == user.id, Log.group_id==self.id).all()
        return logged_items


class UserRole(db.Model):
    __tablename__ = 'user_role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    role_group = db.relationship("User", back_populates="role")


class Log(db.Model):
    __tablename__ = "log"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.String(), db.ForeignKey('user.user_id'))
    group_id = db.Column(db.Integer(), db.ForeignKey('group.id'))
    teacher_id = db.Column(db.String(), db.ForeignKey('user.user_id'))
    time = db.Column(db.Numeric()) #this is the hours which the user has spent doing this work
    status_id = db.Column("status", db.Integer(), db.ForeignKey('log_status.id'))
    date = db.Column(db.Date()) #this is the date when the work was completed
    log_time = db.Column(db.DateTime()) #this is the date/time when the item was logged
    description = db.Column(db.String())

    user = db.relationship("User", foreign_keys=[user_id], back_populates="hours")
    teacher = db.relationship("User", foreign_keys=[teacher_id])
    group = db.relationship("Group", back_populates="hours")
    status = db.relationship("LogStatus", back_populates="hours")

    @classmethod
    def load(cls, id):
        """Loads a previous log from the database using its ID"""
        return cls.query.filter_by(id=id).first()

    @classmethod
    def add_hours(cls, user, group_id, teacher_id, time, description, date):
        """Another super cool function"""
        new_hours = cls(
            user_id=user.id, 
            group_id=group_id, 
            time=time, 
            description=description,
            date=date,
            log_time=datetime.now(),
            status_id = 1
            )
        db.session.add(new_hours)
        user.total += new_hours.time

        if group_id != "None":
            group_member = GroupMembers.load(user_id=user.id, group_id=group_id)
            group_member.group_hours += new_hours.time
        else:
            new_hours.teacher_id = teacher_id
            new_hours.group_id = None
            
        db.session.commit()
        return
    
    def edit_hours(self, group_id, teacher_id, time, description, date):
        """Something cool"""
        old_time = self.time
        old_group = self.group
        difference = time - old_time

        self.group_id = group_id
        self.time = time
        self.description = description
        self.date = date
        self.log_time = datetime.now()
        self.status_id = 1
        self.teacher_id = None

        self.user.total += difference

        if old_group:
            old_group_member = GroupMembers.load(self.user_id, old_group.id)
            old_group_member.group_hours -= old_time
        
        if group_id == "None":
            self.teacher_id = teacher_id
            self.group_id = None
        else:
            group_member = GroupMembers.load(self.user_id, group_id)
            group_member.group_hours += self.time

        db.session.commit()
        return

    def delete(self):
        """an even cooler function"""
        self.user.total -= self.time

        if self.group:
            group_member = GroupMembers.load(self.user_id, self.group.id)
            group_member.group_hours -= self.time

        db.session.delete(self)
        db.session.commit()
        return


class LogStatus(db.Model):
    __tablename__ = "log_status"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    
    hours = db.relationship("Log", back_populates="status")


class Award(db.Model):
    __tablename__ = "award"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String())
    colour = db.Column(db.String())
    threshold = db.Column(db.Integer())

    @staticmethod
    def get_awards():
        return Award.query.order_by(Award.threshold).all()

    @staticmethod
    def get_current_award(hours):
        """Takes the current amount of hours and returns an award object with the current award earned by the user."""
        awards = Award.get_awards()

        current_award = None
        for i in range(len(awards)):
            if hours >= awards[i].threshold:
                current_award = awards[i]
        
        return current_award

    @staticmethod
    def get_next_award(hours):
        awards = Award.get_awards()
        current_award = Award.get_current_award(hours)
        if current_award != None:
            index = awards.index(current_award)
            if index < len(awards) - 1:
                next_award = awards[index + 1]
            else:
                next_award = None
        else:
            next_award = awards[0]

        return next_award
