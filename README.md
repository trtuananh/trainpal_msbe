# TrainPal Backend

## Introduction
TrainPal is a Django-based microservice backend for a mobile application designed to connect fitness trainers and trainees. The backend supports user authentication, course management, online payments via MoMo, and real-time messaging between users. It uses multiple databases (PostgreSQL for user, course, and payment services; MongoDB for messaging; and Redis for WebSocket communication) to ensure modularity and scalability.

This project provides a robust API for managing fitness training sessions, enabling trainers to create courses and schedules, trainees to book sessions, and both to communicate seamlessly. The codebase is organized into four main services: `user_service`, `course_service`, `payment_service`, and `message_service`.

## Installation Guide
This section guides you through setting up the TrainPal backend environment using Conda and running the server.

### Prerequisites
- **Python**: Version 3.8 or higher
- **Conda**: Install Miniconda or Anaconda from [here](https://www.anaconda.com/products/distribution)
- **PostgreSQL**: Version 12 or higher
- **MongoDB**: Version 4.4 or higher
- **Redis**: Version 6 or higher
- **Git**: For cloning the repository

### Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/trtuananh/trainpal_msbe.git
   cd trainpal_msbe
   ```

2. **Create a Conda Environment**:
   ```bash
   conda create -n trainpal_dj python=3.8
   conda activate trainpal_dj
   ```

3. **Install Dependencies**:
   Install the required Python packages listed in `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Databases**:
   - **PostgreSQL**:
     - Install PostgreSQL and create databases for `user_service`, `course_service`, and `payment_service`:
       ```bash
       psql -U postgres
       CREATE DATABASE user_service_db;
       CREATE DATABASE course_service_db;
       CREATE DATABASE payment_service_db;
       ```
     - Update `trainpal_dj/settings.py` with your PostgreSQL credentials (e.g., `USER`, `PASSWORD`).
   - **MongoDB**:
     - Install MongoDB and start the MongoDB server:
       ```bash
       mongod
       ```
     - Ensure `message_service_db` is accessible (default: `localhost:27017`).
   - **Redis**:
     - Install Redis and start the Redis server:
       ```bash
       redis-server
       ```
     - Ensure Redis is running on `localhost:6379`.

5. **Apply Migrations**:
   Run migrations for each service with the appropriate database:
   ```bash
   python manage.py makemigrations user_service
   python manage.py migrate user_service --database=user_service
   python manage.py makemigrations course_service
   python manage.py migrate course_service --database=course_service
   python manage.py makemigrations payment_service
   python manage.py migrate payment_service --database=payment_service
   python manage.py makemigrations message_service
   python manage.py migrate message_service --database=message_service
   ```

6. **Run the Server**:
   Start the Django development server:
   ```bash
   python manage.py runserver
   ```
   The server will be available at `http://localhost:8000`. WebSocket endpoints are accessible at `ws://localhost:8000/ws/chat/<user_id>/`.

7. **Test the Application**:
   - Use tools like Postman or curl to test REST APIs (e.g., `http://localhost:8000/api/user/register/`).
   - Use a WebSocket client (e.g., `wscat`) to test messaging: `wscat -c ws://localhost:8000/ws/chat/<user_id>/ -H "Authorization: Bearer <jwt_token>"`.

## Application Functionality
TrainPal provides a comprehensive set of features for fitness trainers and trainees to interact seamlessly. Below is an overview of the core functionalities, accompanied by illustrative screenshots (placeholders).

### Register & Login
Users can register as either a **trainer** or a **trainee** and log in to access the platform. The authentication system uses JSON Web Tokens (JWT) for secure access.

- **Endpoints**:
  - `POST /api/user/register/`: Register a new user.
  - `POST /api/user/login/`: Log in and receive JWT tokens.
  - `POST /api/user/token-refresh/`: Refresh access tokens.

*Placeholder for Screenshot: [Insert image of registration/login screen here]*

### Manage User Profile
Users can view and update their profiles, including personal details (e.g., name, email, phone, avatar, bio). Trainers can specify their expertise, while trainees can manage their preferences.

- **Endpoints**:
  - `GET /api/user/profile/<pk>/`: Retrieve user profile.
  - `POST /api/user/update-profile/`: Update user profile.

*Placeholder for Screenshot: [Insert image of user profile screen here]*

### For Trainers
Trainers have access to powerful tools to manage their fitness offerings:
- **Create and Manage Courses**: Trainers can create courses (e.g., yoga, boxing) with details like title, description, price, and location.
  - `POST /api/course/create-course/`: Create a new course.
  - `POST /api/course/update-course/`: Update an existing course.
  - `GET /api/course/delete-course/<pk>/`: Delete a course.
- **Schedule Training Sessions**: Trainers can schedule training sessions for their courses.
  - `POST /api/course/add-training/`: Add a training session.
  - `GET /api/course/delete-training/<pk>/`: Delete a training session.
- **View Bookings and Payments**: Trainers can view bookings and payments received for their sessions.
  - `GET /api/course/booking/`: List bookings for the trainer's courses.
  - `GET /api/payment/payments/`: List payments received.

*Placeholder for Screenshot: [Insert image of trainer dashboard showing course creation or session scheduling here]*

### For Trainees
Trainees can browse and book training sessions, make payments, and communicate with trainers:
- **Browse and Book Courses**: Trainees can search for courses by sport, location, or trainer and book sessions.
  - `GET /api/course/courses/`: List available courses.
  - `POST /api/course/add-booking/`: Book a training session.
- **Make Payments**: Trainees can pay for sessions via MoMo or offline methods.
  - `POST /api/payment/create-payment/`: Create a payment.
  - `GET /api/payment/momo-payment/`: Initiate a MoMo payment.
- **Messaging**: Trainees can chat with trainers in real-time to coordinate sessions.
  - `GET /api/message/chatroom/`: Get or create a chat room.
  - `GET /api/message/messages/<room_id>/`: Retrieve messages.
  - WebSocket: `ws://localhost:8000/ws/chat/<user_id>/` for real-time messaging.

*Placeholder for Screenshot: [Insert image of trainee dashboard showing course browsing or chat interface here]*

## Contributing
Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request with your changes. Ensure that your code adheres to the project's coding standards and includes tests.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact
For questions or support, contact the development team at [your-email@example.com].