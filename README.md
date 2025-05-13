# Voting System

A Django-based voting application that allows administrators to create and manage votings, while voters can participate in active votings.

## Features

- **Two-step authentication** - Secure login with user ID and password
- **Role-based access** - Different interfaces for voters and administrators
- **Real-time updates** - Pages automatically reload when voting status changes
- **Timezone support** - Uses Kathmandu, Nepal timezone (configurable)
- **Responsive design** - Works on desktop and mobile devices
- **Candidate management** - Upload candidate photos and descriptions
- **Voting results** - View results after voting has ended

## Installation

### Prerequisites

- Python 3.8+
- Django 5.2+
- Pillow (for image handling)

### Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd voting_system
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

7. (Optional) Load sample data:
   ```
   python manage.py populate_dummy_data
   ```

## Usage

### Admin Functions

1. **Create Votings**: Set up new votings with title, description, start and end times
2. **Manage Candidates**: Add candidates with photos and descriptions
3. **Assign Voters**: Select which voters can participate in each voting
4. **View Results**: See voting results after completion

### Voter Functions

1. **View Active Votings**: See votings they are eligible to participate in
2. **Cast Votes**: Vote for a candidate in active votings
3. **View Results**: See results of completed votings

## Project Structure

```
voting_system/
├── accounts/              # User authentication and management
├── media/                 # User uploaded files (candidate photos)
├── static/                # Static files (CSS, JS)
│   └── js/
│       └── voting-utils.js # Common JavaScript utilities
├── templates/             # HTML templates
│   ├── accounts/          # Authentication templates
│   ├── base.html          # Base template with common layout
│   └── voting/            # Voting-related templates
├── voting/                # Main voting application
│   ├── management/        # Custom management commands
│   │   └── commands/
│   │       └── populate_dummy_data.py
│   ├── models.py          # Data models
│   ├── views.py           # View functions and classes
│   ├── forms.py           # Form definitions
│   └── urls.py            # URL routing
├── voting_system/         # Project settings
├── manage.py              # Django management script
└── README.md              # This file
```

## Design Decisions

### Authentication System

The system uses a custom authentication system with a two-step process:
1. Enter user ID (username for admins, voter ID for voters)
2. Enter password

This approach provides better security and user experience.

### Blue Theme

The application uses a blue-based color scheme for a professional appearance:
- Primary blue (`#0d6efd`) for main elements
- Light blue (`#cfe2ff`) for backgrounds and accents
- Dark blue (`#0a58ca`) for hover states

### JavaScript Architecture

The application uses a modular JavaScript approach:
- `voting-utils.js` contains common utility functions
- Each page initializes only the functions it needs
- Time handling uses Moment.js for consistent formatting

## Development Guidelines

### Adding New Features

1. Create models in the appropriate app
2. Add views and templates
3. Update URLs
4. Add any necessary JavaScript to `voting-utils.js`
5. Update documentation

### Coding Standards

- Follow PEP 8 for Python code
- Use Django's class-based views where appropriate
- Document complex functions with docstrings
- Use meaningful variable and function names

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Bootstrap for the UI framework
- Moment.js for time handling
- Django for the web framework
