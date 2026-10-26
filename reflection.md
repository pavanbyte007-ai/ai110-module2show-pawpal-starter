# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I split the problem into four classes so that each one has a single job. The original UML is in `diagrams/uml.mmd`.

- **Task** is one care activity: title, description, duration, priority, due time, frequency and a completed flag. It can mark itself complete, reschedule, and say whether it is due.
- **Pet** is a name, species, age and its own list of tasks. It adds and removes tasks and returns the ones that are still pending.
- **Owner** is the person's name, email, daily time budget (`available_minutes_per_day`) and a list of pets. `get_all_tasks()` gathers the tasks of every pet.
- **Scheduler** holds one Owner and does the planning: build the daily plan, sort by time or priority, detect conflicts and explain the result.

An Owner has many Pets and a Pet has many Tasks (composition). The Scheduler depends on the Owner and reaches every task through `owner.get_all_tasks()`, so it never needs to know how pets are stored. I kept the data in Task, Pet and Owner and the decisions in the Scheduler, so I could change the scheduling rules without touching the data classes.

**b. Design changes**

The four classes and their relationships stayed the same, but the implementation needed several additions. The final diagram is `diagrams/uml_final.mmd`.

- `Task.due_time` can now be `None`, so a task can have no scheduled time. Sorting puts those tasks last and conflict detection ignores them.
- Recurring tasks needed a date, and a time of day can't hold one. I added an optional `Task.due_date` (default `None`, so existing code kept working), `Task.next_occurrence()` and `Pet.complete_task()`. `mark_complete()` itself is unchanged.
- I added `Scheduler.filter_tasks()` and `Scheduler.conflict_warnings()`, and gave `detect_conflicts` the return type `list[tuple[Task, Task]]`.
- The Scheduler keeps a private `_skipped` list so `explain_plan()` can report tasks that didn't fit in the owner's time.
- Pets and tasks are compared by identity, because dataclass `==` compares every field and two identical tasks would otherwise look like the same task.

In my first design review the AI suggested a `Priority` enum and a `pet_name` on Task. I did not make either change: priority is still a string ranked through a small lookup table, and the Scheduler finds a task's pet by searching the owner's pets when it needs a name for a message.

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers:

- **Completion status:** completed tasks are never planned.
- **Date:** tasks dated in the future (the next copy of a recurring task) are left out of today's plan.
- **Time budget:** the owner's `available_minutes_per_day` is a hard limit, since the owner can't spend more minutes than they have.
- **Priority:** it decides which tasks get the limited minutes (high first, ties go to the earlier time).
- **Time of day and duration:** the plan is shown in time order, and the time plus duration decide whether two tasks overlap.

I ranked the budget first and priority second because running out of time forces a choice, and priority is the natural way to make it. The time of day only affects the order the plan is shown in.

How the algorithms work:

- **Sorting:** `sort_by_time` uses `sorted()` with a key, puts tasks with no time last, and doesn't change the input list.
- **Filtering:** `filter_tasks` walks every pet and keeps tasks that match the completion status and/or pet name.
- **Conflicts:** `detect_conflicts` compares every pair of timed tasks on the same date. A task occupies its start time up to start plus duration, and two tasks conflict if those ranges overlap.
- **Recurrence:** `Pet.complete_task` marks the task done and adds a copy dated one day (daily) or seven days (weekly) later, unless an identical pending copy already exists.

**b. Tradeoffs**

The planner is greedy: it takes tasks in priority order and keeps each one that fits, so it can leave minutes unused when a better combination exists. It also reports conflicts but doesn't move or drop overlapping tasks. This is reasonable for a daily pet-care plan because the rule is easy to explain ("high priority first"), and the owner can decide how to fix an overlap, such as a playtime that runs into dinner.

The second trade-off is in conflict detection. I check whether time ranges overlap instead of only matching identical start times, so a 17:45 playtime that runs 20 minutes is flagged against a vet visit at 17:50. That catches more real clashes, but it depends on accurate durations, and tasks with no time or a zero duration are ignored. My first version sorted the tasks and stopped checking early, which is faster but harder to read. I replaced it with a plain comparison of every pair using a small `_overlaps` helper. That is O(n²) instead of roughly O(n log n), but one owner has a few dozen tasks a day at most, so the simpler version is clear and fast enough. It returns the same pairs and the same tests pass.

Known limitations: a recurring task with no `due_date` repeats from the real current date, tasks with no time are never reported as conflicts, and the plan covers one day only.

## 3. AI Collaboration

**a. How you used AI**

I used an AI coding assistant for most of the project:

- **Design review:** it read my class skeleton and UML and pointed out gaps (free-form priority strings, tasks not knowing their pet) before I wrote any logic.
- **Implementation:** it wrote the class methods, the CLI demo and the Streamlit integration.
- **Algorithms:** it added sorting, filtering, conflict detection and recurrence.
- **Testing and documentation:** it wrote the pytest suite and drafted the README.

The most useful prompts named the files to inspect first, said what to preserve (my class names, UML and existing behavior), and asked it to explain its plan before changing anything. The assistant's ability to run `py_compile`, `pytest` and the demo itself, and read the real output, was the most effective feature, because every step came with evidence instead of a claim.

Separate chat sessions for each phase (design, implementation, algorithms, testing, documentation) kept each conversation focused on one job. Each prompt listed its own checks, so I could review one stage at a time and commit it before starting the next.

**b. Judgment and verification**

One concrete example is the design review. The AI suggested a `Priority` enum and a `pet_name` field on Task. They would have worked, but they change the class interfaces in my UML, and the Scheduler can get the same result with a lookup table and a search of the owner's pets, so I kept the original design. A second case was recurrence: the AI said a time of day can't hold a date and explained the limitation before proposing the smallest change, an optional `due_date`. I accepted that one because the explanation showed why it was needed.

I didn't trust the generated code without checking it:

- I ran `python -m py_compile`, `python -m pytest -v` and `python main.py` after each phase and read the real output.
- The CLI demo caught two mistakes in the demo script itself: it marked the wrong task complete, and it checked conflicts after the overlapping tasks were already completed.
- One test failed on a wrong assertion of mine about an overdue task. I corrected the test and kept the code, because the code was right.
- The Streamlit UI was exercised with a scripted headless run, but I have not tested every click path by hand.
- I asked for the UML to be left alone until I had reviewed the code, and I checked the final diagram against the implementation.

Acting as the lead architect meant deciding what the system should be and letting the AI handle the typing. The AI was quick but eager to add things, so my job was to decide which additions were justified, like `due_date`, and which weren't, like an enum. I also learned that a short design review before coding, and tests with fixed dates afterwards, kept the AI's output honest.

---

## 4. Testing and Verification

**a. What you tested**

`tests/test_pawpal.py` has 35 pytest tests that use fixed dates, so they don't depend on the clock. They cover:

- task completion, adding and removing tasks, and an owner and scheduler seeing tasks from several pets;
- sorting by time, including missing times, equal times and empty input;
- daily and weekly recurrence, one-time tasks, month and year rollover, and no duplicate copies when a task is completed twice;
- conflict detection for the same start time, partial overlap, touching tasks, different pets, empty lists, missing times, bad durations and different dates;
- filtering by pet and completion status, including cases where nothing matches;
- the daily plan and its explanation.

These matter because the scheduler's value is in its edge cases: a wrong sort, a missed overlap or a duplicated recurring task would give the owner a bad plan without any error message.

**b. Confidence**

All 35 tests pass, and `main.py` and `py_compile` run cleanly, so I'm fairly confident in the backend: four out of five. I did not measure code coverage, and the Streamlit app has no automated tests. Next I would test the recurring-task path with no `due_date` using a fixed date, a task that runs past midnight, tasks with no time next to timed ones, `filter_tasks` with an empty pet name, and the UI with Streamlit's testing tools.

---

## 5. Reflection

**a. What went well**

I'm most satisfied that the original four-class design held up. The Scheduler gets every pet's tasks through `Owner.get_all_tasks()`, so adding filtering, conflicts and recurrence didn't require redesigning anything, and the tests could target the Scheduler on its own.

**b. What you would improve**

I would give tasks a proper date and an end time, so recurrence and overlap checks can handle tasks that cross midnight. I would also replace the string priority and frequency values with fixed choices, and make the planner smarter than greedy so it makes better use of the owner's time. The UI needs automated tests, and the UML should be updated as I go instead of at the end.

**c. Key takeaway**

Working with AI goes best when I make the design decisions and write down what must not change, then check every step with real output. The AI is good at producing code quickly, but it's my responsibility to decide whether it is the right code.
