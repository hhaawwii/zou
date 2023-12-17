from collections import defaultdict
from datetime import datetime
from typing import cast

from fileseq import FrameSet
from sqlalchemy import func

from zou.constant import EXCLUDED_PROJECTS
from zou.app import db
from zou.app.models.entity import Entity
from zou.app.models.project import Project
from zou.app.models.validation_record import ValidationRecord
from zou.app.services import (
    shots_service,
)


def get_validation_record(validation_id):
    """
    Return the progress as an active record.
    """
    validation_record = ValidationRecord.get_by(id=validation_id)
    return validation_record.serialize()


def create_validation_record(shot_id, data={}, substract=False):
    """
    Create progress record for given shot.
    """
    shot = shots_service.get_shot_raw(shot_id)
    existing_validation = shot.validation_history
    input_frame_set = FrameSet(data["frame_set"])
    frame_set = FrameSet(input_frame_set)

    # Patch the current latest validation frame set
    if existing_validation:
        existing_frame_set = FrameSet(existing_validation[-1].frame_set)
        if substract:
            frame_set = existing_frame_set.difference(frame_set)
        else:
            frame_set = existing_frame_set.union(frame_set)
    elif substract:
        frame_set = FrameSet([])

    # Make sure the new frame set does not exeed the amount of frames
    frame_set = FrameSet.from_iterable(
        [
            frame
            for frame in frame_set.items
            if frame <= shot.nb_frames and frame > 0
        ]
    )

    validation_record = ValidationRecord.create(
        shot_id=shot_id, frame_set=str(frame_set), total=len(frame_set)
    )

    return validation_record.serialize()


def _apply_progress(progress, total, shot, nb_frames):
    progress["total"] += total
    progress["progress"] = progress["total"] / nb_frames
    shots = cast(list, progress["shots"])
    shots.append(shot)


def get_project_progress(project_id, trunc_key="day"):
    if trunc_key not in [
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "microsecond",
    ]:
        trunc_key = "day"

    truncated_date = func.date_trunc(trunc_key, ValidationRecord.created_at)
    progress_query = (
        db.session.query(
            truncated_date,
            ValidationRecord.total,
            ValidationRecord.shot_id,
        )
        .distinct(truncated_date, ValidationRecord.shot_id)
        .filter(ValidationRecord.shot_id == Entity.id)
        .filter(Entity.project_id == project_id)
        .order_by(
            truncated_date,
            ValidationRecord.shot_id,
            ValidationRecord.created_at.desc(),
        )
    )
    progress_data = progress_query.all()

    nb_frames_query = (
        db.session.query(func.sum(Entity.nb_frames).label("nb_frames"))
        .filter(Entity.entity_type_id == shots_service.get_shot_type()["id"])
        .filter(Entity.project_id == project_id)
    )
    nb_frames = nb_frames_query.first()[0]

    project_progress = defaultdict(
        lambda: {"total": 0, "shots": [], "progress": 0}
    )

    for date, total, shot in progress_data[::-1]:
        if shot in project_progress[date]["shots"] and nb_frames is not 0:
            continue
        _apply_progress(project_progress[date], total, shot, nb_frames)

        for progress in project_progress.values():
            if shot in progress["shots"]:
                continue
            _apply_progress(progress, total, shot, nb_frames)

    formatted_progress = [
        {"date": key, "total": value["total"], "progress": value["progress"]}
        for key, value in project_progress.items()
    ]
    formatted_progress.sort(key=lambda x: x["date"])
    if formatted_progress:
        now = datetime.now()
        formatted_progress.append(
            {
                "date": now.replace(
                    hour=min(now.hour + 1, 23),
                    minute=0,
                    second=0,
                    microsecond=0,
                ),
                "total": formatted_progress[-1]["total"],
                "progress": formatted_progress[-1]["progress"],
            }
        )
    return formatted_progress


def get_projects_progress(
    trunc_key="day",
    excluded_projects=EXCLUDED_PROJECTS,
    include_average=True,
    average_key="AVERAGE",
):
    projects_progress = defaultdict(lambda: {})
    for project in Project.query.all():
        if project.name in excluded_projects:
            continue
        for project_progress in get_project_progress(project.id, trunc_key):
            projects_progress[project_progress["date"]][project.name] = {
                "total": project_progress["total"],
                "progress": project_progress["progress"],
            }

    formatted_progress = [
        {"date": key, "projects": value}
        for key, value in projects_progress.items()
    ]
    formatted_progress.sort(key=lambda x: x["date"])

    if include_average:
        return get_average_progrect_progress(
            formatted_progress, average_key=average_key
        )

    return formatted_progress


def get_average_progrect_progress(projects_progress, average_key="AVERAGE"):
    progress_accumulation = {}
    for progress in projects_progress:
        for project_name, project_progress in progress["projects"].items():
            progress_accumulation[project_name] = project_progress

        # Compute the average of the projects's progress at this time
        progress["projects"].setdefault(average_key, {})
        progress["projects"][average_key]["progress"] = sum(
            accumulation["progress"]
            for accumulation in progress_accumulation.values()
        ) / len(progress_accumulation)

        # Compute the total frames of all the projects at that time
        progress["projects"][average_key]["total"] = sum(
            accumulation["total"]
            for accumulation in progress_accumulation.values()
        )

    return projects_progress
