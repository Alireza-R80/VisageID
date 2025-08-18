from facenet_pytorch import InceptionResnetV1 as IRV1
from facenet_pytorch import MTCNN
from pandas.core.frame import DataFrame
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
from torch.functional import F
import matplotlib.pyplot as plt
from tqdm import tqdm
import torch.optim as optim
from torch import cuda
import torch.nn as nn
from glob import glob
import pandas as pd
import random
import cv2
import torch
import psycopg2 as pg



image_size = 160
device_name = 'cuda' if cuda.is_available() else 'cpu'

db_connection = pg.connect(database="FaceRecog",
							user = "faceRecogApp",
							password = "facerecogapp@123",
							host = "127.0.0.1",
							port = "5432"
							)


mtcnn_model = MTCNN(
	margin=14,
	factor=0.6,
	keep_all=True,
	device=device_name
)

resnet = IRV1(pretrained='vggface2').double().eval()


class User:

	def __init__(self, user_id, name):
		self.user_id = user_id
		self.name = name
		self.embeddings = []

	def add_embedding(self, embed):
		self.embeddings.append(embed)

	def from_touple(tp):
		return User(tp[0], tp[1])

	def from_database(touple_list):
		result = []
		for tp in touple_list:
			result.append(User.from_touple(tp))
		return result

	def __str__(self):
		return "User{user_id: " + str(self.user_id) + \
		", name: " + str(self.name) + \
		", embeddings: "+ str(len(self.embeddings)) + \
		" }"


def distance(embd1, embd2):
    return torch.sum(torch.square(torch.subtract(embd1, embd2))).item()


def load_dataset():
	cursor = db_connection.cursor()
	cursor.execute("SELECT * FROM users")
	users = User.from_database(cursor.fetchall())
	for user in users:
		cursor.execute(f"SELECT * from embeddings WHERE user_id={user.user_id}")
		embeddings = cursor.fetchall()
		for embed in embeddings:
			embed_torch = torch.load(embed[2], map_location=torch.device(device_name))
			user.add_embedding(embed_torch)
	return users


def predict_id(face_embeddings, users):

	names = list(map(lambda user: user.name, users))
	distances = []

	for user in users:
		minimum_distance = 1000
		for embed in user.embeddings:
			dist = distance(face_embeddings, embed)
			if dist < minimum_distance:
				minimum_distance = dist
		distances.append(minimum_distance)

	return names[distances.index(min(distances))]


def preprocess_face(face):
	face = cv2.resize(face, (image_size,image_size))
	face = torch.from_numpy(face).view(1, 3, image_size, image_size).double().to(device_name)
	return face


def drawFaceBoundingBox(frame):
	boxes, probs = mtcnn_model.detect(frame)
	if boxes is not None:
		for box, prob in zip(boxes, probs):
			if prob < 0.9:
				continue
			frame = cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 0, 255), 3)
	return boxes


def drawFaceRecogText(users, frame, boxes):
	if boxes is None:
		return

	for box in boxes:

		croppedFace = frame.copy()[int(box[1]): int(box[3]), int(box[0]):int(box[2]), :]
		if croppedFace.shape[0] == 0 or croppedFace.shape[1] == 0:
			continue

		face_embedding = resnet(preprocess_face(croppedFace))
		class_name = predict_id(face_embedding, users)
		(tw, th), _ = cv2.getTextSize(class_name, cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, 1)
		frame = cv2.rectangle(frame, (int(box[0]), int(box[1]) - th - 10), (int(box[0]) + tw + 10, int(box[1])), (0,0,255), -1)
		frame = cv2.putText(frame, class_name, (int(box[0]) + 5, int(box[1]) - 5), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255, 255, 255))


def start_show_frames(users):
	webcam = cv2.VideoCapture(0)
	while True:
		
		_, frame = webcam.read()
		boxes = drawFaceBoundingBox(frame)
		drawFaceRecogText(users, frame, boxes)
					
		cv2.imshow("Face Recognition", frame)
		key = cv2.waitKey(1) & 0xFF
		if key == ord('q'):
			break
	cv2.destroyAllWindows()
	webcam.release()
	cv2.waitKey(1)


def main():
	users = load_dataset()
	start_show_frames(users)


if __name__ == '__main__':
	main()

