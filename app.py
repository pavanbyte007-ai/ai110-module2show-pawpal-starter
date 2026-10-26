from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

# The Owner (with its pets and tasks) and the Scheduler live in session_state so
# they survive Streamlit reruns. They are created only once.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(
        name="Jordan", email="", available_minutes_per_day=120
    )
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)

owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler



def when_text(task: Task) -> str:
    """Return a task's start time as HH:MM, or "Anytime" when it has none."""
    return task.due_time.strftime("%H:%M") if task.due_time else "Anytime"


# One-shot success message that survives the st.rerun() after a form submit.
if "flash" in st.session_state:
    st.success(st.session_state.pop("flash"))

with st.expander("Scenario", expanded=False):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.
"""
    )

st.divider()

# ---------------------------------------------------------------- Owner
st.subheader("Owner")
col1, col2, col3 = st.columns(3)
with col1:
    owner.name = st.text_input("Owner name", value=owner.name) or owner.name
with col2:
    owner.email = st.text_input("Email", value=owner.email)
with col3:
    owner.available_minutes_per_day = int(
        st.number_input(
            "Minutes available per day",
            min_value=0,
            max_value=1440,
            value=owner.available_minutes_per_day,
        )
    )

# ----------------------------------------------------------------- Pets
st.subheader("Pets")
with st.form("add_pet_form", clear_on_submit=True):
    pcol1, pcol2, pcol3 = st.columns(3)
    with pcol1:
        pet_name = st.text_input("Pet name")
    with pcol2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with pcol3:
        age = st.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        pet_name = pet_name.strip()
        if not pet_name:
            st.error("Please enter a pet name.")
        elif any(p.name.lower() == pet_name.lower() for p in owner.pets):
            st.warning(f"You already have a pet named {pet_name}.")
        else:
            owner.add_pet(Pet(name=pet_name, species=species, age=int(age)))
            st.session_state.flash = f"Added {pet_name}!"
            st.rerun()

if not owner.pets:
    st.info("No pets yet. Add one above.")

# ---------------------------------------------------------------- Tasks
st.subheader("Tasks")
if owner.pets:
    with st.form("add_task_form", clear_on_submit=True):
        selected_name = st.selectbox("Pet", [p.name for p in owner.pets])
        tcol1, tcol2 = st.columns(2)
        with tcol1:
            task_title = st.text_input("Task title", placeholder="Morning walk")
            description = st.text_input("Description (optional)")
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        with tcol2:
            duration = st.number_input(
                "Duration (minutes)", min_value=1, max_value=240, value=20
            )
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            has_time = st.checkbox("Set a time", value=True)
            due = st.time_input("Time", value=time(8, 0))
        if st.form_submit_button("Add task"):
            if not task_title.strip():
                st.error("Please enter a task title.")
            else:
                pet = next(p for p in owner.pets if p.name == selected_name)
                new_due = due if has_time else None
                if any(
                    t.title.lower() == task_title.strip().lower()
                    and t.due_time == new_due
                    and not t.completed
                    for t in pet.tasks
                ):
                    st.warning(
                        f"{pet.name} already has '{task_title.strip()}' at that time."
                    )
                    st.stop()
                pet.add_task(
                    Task(
                        title=task_title.strip(),
                        description=description.strip(),
                        duration_minutes=int(duration),
                        priority=priority,
                        due_time=new_due,
                        frequency=frequency,
                    )
                )
                st.session_state.flash = (
                    f"Added '{task_title.strip()}' for {pet.name}."
                )
                st.rerun()
else:
    st.caption("Add a pet before creating tasks.")

# View the task list using the Scheduler's filter and sort methods.
if owner.pets:
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        pet_filter = st.selectbox("Filter by pet", ["All pets"] + [p.name for p in owner.pets])
    with fcol2:
        status_filter = st.selectbox("Filter by status", ["All", "Pending", "Completed"])
    completed_filter = {"All": None, "Pending": False, "Completed": True}[status_filter]

    # Conflicts among all pending tasks, reported as soon as they exist.
    pending_conflicts = scheduler.conflict_warnings()
    if pending_conflicts:
        st.warning(
            "Some pending tasks overlap in time. Consider rescheduling one of each pair:\n\n"
            + "\n".join(f"- {w}" for w in pending_conflicts)
        )

    for pet in owner.pets:
        if pet_filter != "All pets" and pet.name != pet_filter:
            continue
        st.markdown(f"**{pet.name}** ({pet.species}, age {pet.age})")
        shown = scheduler.sort_by_time(
            scheduler.filter_tasks(completed=completed_filter, pet_name=pet.name)
        )
        if not pet.tasks:
            st.caption("No tasks yet.")
        elif not shown:
            st.caption("No tasks match this filter.")
        for task in shown:
            c1, c2, c3 = st.columns([6, 2, 2])
            label = (
                f"{when_text(task)} - {task.title}, {task.duration_minutes} min, "
                f"{task.priority} ({task.frequency})"
                + (f", {task.due_date}" if task.due_date else "")
            )
            c1.markdown(f"~~{label}~~ ✅" if task.completed else label)
            key = f"{pet.name}_{id(task)}"
            if not task.completed and c2.button("Complete", key=f"done_{key}"):
                pet.complete_task(task)
                st.rerun()
            if c3.button("Remove", key=f"remove_{key}"):
                pet.remove_task(task)
                st.rerun()

st.divider()

# ------------------------------------------------------------- Schedule
st.subheader("Build Schedule")
if st.button("Generate schedule"):
    st.session_state.show_schedule = True

if st.session_state.get("show_schedule"):
    st.markdown("### Today's Schedule")
    plan = scheduler.sort_by_time(scheduler.generate_daily_plan())
    if not plan:
        st.info("Nothing to schedule. Add tasks (or all tasks are completed).")
    else:
        pet_of = {id(t): p.name for p in owner.pets for t in p.tasks}
        minutes = sum(t.duration_minutes for t in plan)
        st.success(
            f"{len(plan)} task(s) planned, {minutes} of "
            f"{owner.available_minutes_per_day} available minutes."
        )
        st.dataframe(
            [
                {
                    "Time": when_text(t),
                    "Pet": pet_of.get(id(t), "?"),
                    "Task": t.title,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority,
                    "Status": "Done" if t.completed else "Pending",
                }
                for t in plan
            ],
            hide_index=True,
        )
        for warning in scheduler.conflict_warnings(plan):
            st.warning(
                f"Overlap in today's plan: {warning}. "
                "Consider rescheduling one of these tasks."
            )
    with st.expander("Why this plan?", expanded=False):
        st.text(scheduler.explain_plan())

    done = scheduler.sort_by_time(scheduler.filter_tasks(completed=True))
    if done:
        with st.expander(f"Completed tasks ({len(done)})"):
            pet_of = {id(t): p.name for p in owner.pets for t in p.tasks}
            st.dataframe(
                [
                    {"Time": when_text(t), "Pet": pet_of.get(id(t), "?"), "Task": t.title}
                    for t in done
                ],
                hide_index=True,
            )
