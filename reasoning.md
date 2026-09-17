Thought Process

A simplified, step-by-step breakdown of how the Parking Garage Management System was planned, designed, and built.

1. Focus on the Real World, Not Just Features

Instead of building a quick, simple demo for just one parking garage, the system was designed from day one to handle real-world operations seamlessly.

Built for Multiple Garages: Every database table tracks a specific garage (garage_id). It is ready to scale to dozens of locations without redesigning the system.

Built in the Right Sequence: The core math for computing parking fees was written and thoroughly tested before building spot assignment or UI components. Getting the core rules right early prevented hidden bugs later.

2. Solve the Hardest Problem First: Preventing Double-Parking

In a busy parking garage, two attendants—or one attendant double-clicking a button—might try to assign the exact same open spot at the same time. Application-level checks fail here because two requests can read a spot as "free" simultaneously before either record is updated.

Prevented by the Database: Rules built directly into the database (partial unique indexes) make storing two active tickets for the same spot physically impossible.

Cooperative Locking: When assigning a spot, the system temporarily locks a single open row (SELECT ... FOR UPDATE SKIP LOCKED), forcing concurrent check-ins to automatically grab different spots without crashing or waiting on each other.

Proven with Automated Tests: A dedicated stress test fires 25 simultaneous check-in requests at only 10 available spots to prove that exactly 10 succeed and 15 fail cleanly.

3. Keep Pricing Math Isolated and Watertight

Parking fee calculations involve tricky edge cases (e.g., partial hours rounding up, daily maximum price caps, and multi-day stays).

The fee calculation logic was isolated into its own standalone module (fee.py) with zero database or web server dependencies.

Every boundary condition—like being one minute over an hour or hitting the daily price limit—was tested individually to eliminate subtle billing errors.

4. Optimize for the Attendant's Daily Work

Database search indexes were tailored around the exact questions a garage attendant asks every day:

"Is an EV spot free right now?" A composite index (garage_id, type, status) allows the system to instantly filter free spots by type without scanning the entire database.

"Where is this license plate parked?" A specialized index tracks active tickets only, keeping license plate searches lightning-fast even after millions of historical, completed tickets accumulate.

5. Prioritize What Matters Most

Development was intentionally split into tiers to keep the system robust and focused:

Must-Haves First: Core guarantees—reliable locking, exact pricing math, and preventing accidental duplicate submissions (idempotency).

High-Value Additions: Real-time updates via WebSockets (so availability updates instantly on screen without refreshing) and smart nearest-spot selection.

Deferred Features: Extra features like monthly parking passes, dynamic pricing, or automated camera check-ins were deliberately deferred so core reliability was secured first.

6. Keep the User Interface Simple

The React frontend contains no business rules or price calculation logic.

The screen serves purely as a visual display that submits requests and shows system status.

If a mobile app or self-service kiosk is added later, all pricing and parking rules remain safe and enforced in one central backend location.

##Summary of Execution Order

Verify Fee Math: Write pure pricing functions and test edge cases in isolation.

Ensure Database Safety: Implement row locking and partial unique indexes, verified with concurrency tests.

Build Fast Lookups: Add specialized database indexes for spot availability and active license plates.

Connect the Interface: Build a clean frontend on top of the backend API without adding duplicated logic.

Add Live Features: Layer on real-time WebSocket updates and smart spot assignments.