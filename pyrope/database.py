
from datetime import datetime

from sqlalchemy import (
    CheckConstraint, create_engine, DateTime, Float, ForeignKey, Integer,
    NVARCHAR, String
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
)

from pyrope import config


class Base(DeclarativeBase):

    pass


class User(Base):

    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    results: Mapped[list['Result']] = relationship(
        back_populates='user', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'User(name={self.name})'


class Exercise(Base):

    __tablename__ = 'exercise'

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source: Mapped[str] = mapped_column(NVARCHAR(), nullable=False)
    label: Mapped[str] = mapped_column(String(64), nullable=False)
    score_maximum: Mapped[float] = mapped_column(Float(), nullable=False)
    results: Mapped[list['Result']] = relationship(
        back_populates='exercise', cascade='all, delete-orphan'
    )

    __table_args__ = (
        CheckConstraint(
            score_maximum > 0, name='Maximal score must be positive.'
        ),
    )

    def __repr__(self):
        return (
            f'Exercise(label={self.label}, score_maximum={self.score_maximum})'
        )


class Result(Base):

    __tablename__ = 'result'

    id: Mapped[int] = mapped_column(primary_key=True)
    exercise_id: Mapped[str] = mapped_column(
        String(64), ForeignKey('exercise.id')
    )
    exercise: Mapped['Exercise'] = relationship(back_populates='results')
    user_id: Mapped[int] = mapped_column(
        Integer(), ForeignKey('user.id')
    )
    user: Mapped['User'] = relationship(back_populates='results')
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    score_given: Mapped[float] = mapped_column(Float(), nullable=True)

    def __repr__(self):
        return (
            f'Result(user_name={self.user.name}, '
            f'exercise_label={self.exercise.label}, '
            f'started_at={self.started_at}, '
            f'submitted_at={self.submitted_at}, '
            f'score_given={self.score_given})'
        )


engine = create_engine(f'{config.dialect}{config.db_file}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
