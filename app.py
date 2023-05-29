import cv2
import dlib
import face_recognition
import pickle5 as pickle
import os
import getpass
import logging
import argparse
import re
import concurrent.futures
import secrets
from argon2 import PasswordHasher
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, select, LargeBinary
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from cv2 import cvtColor, COLOR_BGR2GRAY, equalizeHist, CascadeClassifier
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(filename='app.log', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Haar cascades for face detection
FACE_HAAR_PATH = 'haarcascade_frontalface_default.xml'


class CameraHandler:
    def __init__(self):
        self.video_capture = cv2.VideoCapture(0)

    def capture_frame(self):
        ret, frame = self.video_capture.read()
        return frame

    def close(self):
        self.video_capture.release()


class FaceRecognizer:
    def __init__(self):
        self.face_cascade = CascadeClassifier(FACE_HAAR_PATH)

    def get_face_encodings(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]
        return face_recognition.face_encodings(rgb_small_frame)

    def check_face_quality(self, frame):
        gray = cvtColor(frame, COLOR_BGR2GRAY)
        gray = equalizeHist(gray)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        # Checking if a face is detected
        if len(faces) != 0:
            return True
        else:
            return False


class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class Database:
    def __init__(self):
        engine = create_engine(os.getenv("DATABASE_URL"), echo=True)
        metadata = MetaData()
        self.users = Table('users', metadata,
                           Column('id', Integer, primary_key=True),
                           Column('username', String),
                           Column('password', String),
                           Column('encoding', LargeBinary))

        metadata.create_all(engine)
        self.Session = scoped_session(sessionmaker(bind=engine))

    def check_username_exists(self, username):
        try:
            s = select([self.users]).where(self.users.c.username == username)
            session = self.Session()
            return session.execute(s).fetchone() is not None
        except SQLAlchemyError as e:
            logging.error('Database error during username check: %s', str(e))
            return False
        finally:
            session.remove()

    def add_user(self, user, face_encoding):
        ph = PasswordHasher()
        hashed_password = ph.hash(user.password)
        hashed_face_encoding = ph.hash(pickle.dumps(face_encoding))
        try:
            ins = self.users.insert().values(username=user.username, password=hashed_password,
                                             encoding=hashed_face_encoding)
            session = self.Session()
            session.execute(ins)
            session.commit()
        except SQLAlchemyError as e:
            logging.error('Database error during user registration: %s', str(e))
            return False
        finally:
            session.remove()
            # Securely delete sensitive data
            del hashed_password
            del hashed_face_encoding
        return True


class CLI:
    def get_args(self):
        parser = argparse.ArgumentParser(description='Register a new user.')
        parser.add_argument('--username', required=True, help='Username for the new user.')
        parser.add_argument('--password', required=True, help='Password for the new user.')
        args = parser.parse_args()
        return args


def validate_username(username):
    # Only allow alphanumeric characters and underscores in username
    return re.match(r'^\w+$', username) is not None


def validate_password(password):
    # Enforce minimum password length
    return len(password) >= 8


def register_new_user(args):
    user = User(args.username, args.password)

    if not validate_user(user):
        return

    camera = CameraHandler()
    frame = capture_frame(camera)

    if not validate_frame(frame):
        return

    face_encodings = calculate_face_encodings(frame)

    if face_encodings is None:
        return

    db = Database()
    if not add_user_to_db(db, user, face_encodings[0]):
        return

    print(f'User {user.username} registered successfully.')


def validate_user(user):
    if not validate_username(user.username):
        print('Username can only contain alphanumeric characters and underscores.')
        return False

    if not validate_password(user.password):
        print('Password must be at least 8 characters long.')
        return False

    db = Database()

    # Check if username already exists
    if db.check_username_exists(user.username):
        print('This username is already registered. Please choose a different one.')
        return False

    return True


def capture_frame(camera):
    # Take a photo
    print('Taking photo in 3 seconds...')
    cv2.waitKey(3000)
    frame = camera.capture_frame()
    camera.close()
    return frame


def validate_frame(frame):
    recognizer = FaceRecognizer()

    # Check face quality
    if not recognizer.check_face_quality(frame):
        print('The quality of the face in the photo is not sufficient. Please try again.')
        return False

    return True


def calculate_face_encodings(frame):
    recognizer = FaceRecognizer()
    # Calculate face encoding
    face_encodings = recognizer.get_face_encodings(frame)
    if not face_encodings:
        print('No face was detected in the photo. Please try again.')
        return None

    return face_encodings


def add_user_to_db(db, user, face_encoding):
    # Add user to database
    if not db.add_user(user, face_encoding):
        print('User registration failed due to a database error.')
        return False

    return True


def main():
    cli = CLI()
    args = cli.get_args()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(register_new_user, args)}
        for future in concurrent.futures.as_completed(futures):
            if future.exception() is not None:
                logging.error('Exception during user registration: %s', str(future.exception()))


if __name__ == "__main__":
    main()
