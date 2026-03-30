import json
from pathlib import Path

from db.models.problem import Problem
from db.models.step import Step
from db.models.step_problem import StepProblem
from db.models.user import User
from db.session import SessionLocal


def main() -> None:
    with SessionLocal() as session:
        admin_user = session.query(User).filter(User.id == 1).first()
        if admin_user is None:
            raise RuntimeError("Super user with id=1 does not exist")

    for file in Path("steps").iterdir():
        if file.suffix != ".json":
            continue
        with open(file) as fr:
            data = json.load(fr)

        step_title = file.stem

        with SessionLocal() as session:
            step = session.query(Step).filter(Step.title == step_title).first()
            if step is None:
                step = Step(title=step_title, created_by=1, group_id=None)
                session.add(step)
                session.flush()

            for row in data:
                prob = (
                    session.query(Problem)
                    .filter(
                        Problem.source == row["source"],
                        Problem.problem_id == row["problem_id"],
                    )
                    .first()
                )
                if prob is None:
                    prob = Problem()
                prob.problem_id = row["problem_id"]
                prob.title = row["title"]
                prob.source = row["source"]
                session.merge(prob)
                session.flush()

                sp = (
                    session.query(StepProblem)
                    .filter(
                        StepProblem.step_id == step.id,
                        StepProblem.problem_id == prob.id,
                    )
                    .first()
                )
                if sp is None:
                    sp = StepProblem(step_id=step.id, problem_id=prob.id)
                    session.add(sp)
                sp.order = row["order"]
                sp.specialty = row["specialty"]
                sp.topic = row["topic"]

            session.commit()
        print(file)


if __name__ == "__main__":
    main()
