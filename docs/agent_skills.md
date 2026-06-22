# Agent Skills

An agent skill packages a single capability as a folder containing a SKILL.md
file plus any helper code or assets the capability needs. The SKILL.md front
matter declares a name and a description; the description is what an agent reads
to decide whether the skill is relevant to the task at hand.

The value of the skill format is discoverability and portability. Because the
capability is self-describing, an agent can load only the skills it needs for a
given task instead of carrying every instruction in its base prompt. This keeps
the working context small and the behaviour predictable.

A well-written skill states clearly when to use it, what inputs it expects, and
what output it produces. For a Forward Deployed Engineer, skills are how you
encode a customer's domain knowledge and house style into reusable units that
survive across sessions and across team members.
