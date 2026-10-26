# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?
==
My initial UML has four classes. Their relationships are shown in diagrams/uml.mmd and match the skeleton in pawpal_system.py.

Task is a dataclass for one care activity. It holds a title, description, duration in minutes, priority, due time, frequency and a completed flag. It can mark itself complete, reschedule to a new time, and report whether it is due at a given moment.
Pet is a dataclass for one animal, with a name, species, age and its own list of tasks. It adds and removes tasks and returns the ones not yet completed.
Owner stores the owner's name, email, daily time budget (available_minutes_per_day) and a list of pets. It adds and removes pets, and get_all_tasks() gathers every task across all pets.
Scheduler holds a reference to one Owner and contains the planning logic. It builds the daily plan, sorts tasks by time or priority, detects conflicts and explains the plan in readable text.
The relationships are composition. An Owner has many Pets, and a Pet has many Tasks. The Scheduler depends on one Owner and works with that owner's Tasks. I kept data in Task, Pet and Owner and put the scheduling decisions in the Scheduler, so the algorithms can change without touching the data model. At this stage the methods are stubs, so the skeleton only defines structure.

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.
== 
While reviewing the skeleton, I found two gaps. First, priority and frequency were free-form strings. sort_by_priority and is_due need known values, and a typo would silently break sorting. I [changed them to an enum / documented the allowed values] so the Scheduler can rank tasks reliably. Second, a Task didn't record which pet it belonged to, so a flat list from Owner.get_all_tasks() couldn't produce an explanation like "Walk for Buddy". I [added a pet_name field to Task / changed get_all_tasks() to return pet–task pairs] so the plan and conflict messages can name the pet. I also changed the detect_conflicts return type to list[tuple[Task, Task]] to make its output clearer.

If you make no changes yet, you can write instead: "I reviewed the skeleton and identified a few improvements, such as constraining priority values and linking tasks to pets. I plan to make them when I implement the scheduling logic." Keep the real change description for when you actually make them.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
