from typing import Optional

from sqlalchemy import select

from core.database import get_session
from core.models import Participant
from core.schemas import ParticipantCreate, ParticipantUpdate


class ParticipantService:
    def create(self, data: ParticipantCreate) -> Participant:
        with get_session() as session:
            participant = Participant(**data.model_dump())
            session.add(participant)
            session.commit()
            session.refresh(participant)
            return participant

    def get_by_id(self, participant_id: int) -> Optional[Participant]:
        with get_session() as session:
            return session.get(Participant, participant_id)

    def list_active(self) -> list[Participant]:
        with get_session() as session:
            query = (
                select(Participant)
                .where(Participant.is_active.is_(True))
                .order_by(Participant.id)
            )
            return list(session.execute(query).scalars().all())

    def update(self, participant_id: int, data: ParticipantUpdate) -> Optional[Participant]:
        with get_session() as session:
            participant = session.get(Participant, participant_id)
            if not participant:
                return None
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(participant, key, value)
            session.commit()
            session.refresh(participant)
            return participant

    def deactivate(self, participant_id: int) -> Optional[Participant]:
        with get_session() as session:
            participant = session.get(Participant, participant_id)
            if not participant:
                return None
            participant.is_active = False
            session.commit()
            session.refresh(participant)
            return participant


participant_service = ParticipantService()
