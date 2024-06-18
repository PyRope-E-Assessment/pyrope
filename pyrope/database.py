
from datetime import datetime, timedelta

from sqlalchemy import (
    create_engine, DateTime, Float, ForeignKey, Interval, PickleType, String
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
)

from pyrope import config


class Base(DeclarativeBase):

    pass


class User(Base):

    __tablename__ = 'user'

    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    attempts: Mapped[list['Attempt']] = relationship(
        back_populates='user', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'User(name={self.name})'


class Exercise(Base):

    __tablename__ = 'exercise'

    name: Mapped[str] = mapped_column(String(50), primary_key=True)
    title: Mapped[str] = mapped_column(String(80), nullable=True)
    subtitle: Mapped[str] = mapped_column(String(80), nullable=True)
    author: Mapped[str] = mapped_column(String(50), nullable=True)
    language: Mapped[str] = mapped_column(String(20), nullable=True)
    license: Mapped[str] = mapped_column(String(50), nullable=True)
    URL: Mapped[str] = mapped_column(String(200), nullable=True)
    origin: Mapped[str] = mapped_column(String(200), nullable=True)
    discipline: Mapped[str] = mapped_column(String(50), nullable=True)
    area: Mapped[str] = mapped_column(String(50), nullable=True)
    topic: Mapped[tuple] = mapped_column(PickleType(), nullable=True)
    topic_contingent: Mapped[tuple] = mapped_column(
        PickleType(), nullable=True
    )
    keywords: Mapped[tuple] = mapped_column(PickleType(), nullable=True)
    taxonomy: Mapped[tuple] = mapped_column(PickleType(), nullable=True)
    attempts: Mapped[list['Attempt']] = relationship(
        back_populates='exercise', cascade='all, delete-orphan'
    )

    def __repr__(self):
        return (
            f'Exercise(name={self.name}, title={self.title}, '
            f'author={self.author}, language={self.language})'
        )


class Attempt(Base):

    __tablename__ = 'attempt'

    exercise_name: Mapped[str] = mapped_column(
        String(50), ForeignKey('exercise.name'), primary_key=True
    )
    exercise: Mapped['Exercise'] = relationship(back_populates='attempts')
    user_name: Mapped[str] = mapped_column(
        String(50), ForeignKey('user.name'), primary_key=True
    )
    user: Mapped['User'] = relationship(back_populates='attempts')
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    duration: Mapped[timedelta] = mapped_column(Interval(), nullable=False)
    total_score: Mapped[float] = mapped_column(Float(), nullable=False)
    parameters: Mapped[dict] = mapped_column(PickleType(), nullable=False)
    scores: Mapped[dict] = mapped_column(PickleType(), nullable=False)
    answers: Mapped[dict] = mapped_column(PickleType(), nullable=False)

    def __repr__(self):
        return (
            f'Attempt(timestamp={self.timestamp}, user_name={self.user_name}, '
            f'exercise_name={self.exercise_name}, duration={self.duration}, '
            f'total_score={self.total_score})'
        )


engine = create_engine(f'{config.dialect}{config.db_file}')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
