##Technology Stack

A simplified overview of the technology powering the Parking Garage Management System, what each component does, and why it was chosen.

##Database — PostgreSQL

What it does: Stores all core records—garages, spots, tickets, and pricing rates. It serves as the single source of truth for the entire system.

Why it was chosen:

Prevents double-parking: Uses a built-in database rule (partial unique index) that instantly blocks a second active ticket from being issued for an occupied spot, even if two cars check in at the exact same millisecond.

Handles high traffic safely: Uses advanced database locking features (SELECT ... FOR UPDATE SKIP LOCKED) so two attendants assigning spots simultaneously never get handed the exact same spot.

All-or-nothing transactions: Ensures that finding an open spot and creating a ticket happen together seamlessly. If one step fails, the whole check-in cancels safely without leaving partial data.

##Backend / API — Python + FastAPI + SQLAlchemy

What it does: Handles all the core rules and logic—calculating fees, finding open spots, searching license plates, and processing check-ins and check-outs.

Why it was chosen:

FastAPI: Automatically creates easy-to-read API documentation, supports real-time updates via WebSockets, and catches invalid data (like a missing plate number) before it hits the database.

SQLAlchemy: Connects Python code cleanly to the database. It makes routine data tasks easy while giving precise control over complex database queries when concurrent check-ins occur.

Pydantic & pytest: Pydantic verifies incoming data automatically, while pytest runs automated checks to guarantee fee calculations and concurrent requests work without errors.

Frontend — React (Vite)

What it does: Powers the screen used by garage attendants to check vehicles in and out, search plates, and view real-time spot availability.

Why it was chosen:

React: Breaks the user interface into independent building blocks (such as a check-in form, a ticket log, and an availability dashboard) that are easy to build and maintain.

Vite: A modern tool that builds and updates the user interface instantly during development.

Plain WebSockets & Standard CSS: Connects directly to real-time updates using built-in browser capabilities without bloating the project with heavy third-party UI or communication libraries.