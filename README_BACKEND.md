# Backend API overview

- `POST /api/auth/register` — create student account
- `POST /api/auth/login` — log in
- `POST /api/auth/logout` — log out
- `GET /api/me` — current account and profile
- `PUT /api/profile` — update onboarding/profile
- `GET /api/courses` — ranked course list
- `GET /api/courses/<course_id>` — course details
- `GET /api/roadmap` — roadmap suggestions
- `GET /api/resources` — external starter resources
- `GET /api/careers` — career skill suggestions
- `GET /api/progress` — saved quiz attempts
- `GET /api/quizzes/<quiz_key>` and `POST /api/quizzes/<quiz_key>/submit` — assessments
- `POST /api/assistant` — built-in study guidance
- `GET /api/health` — service health check
