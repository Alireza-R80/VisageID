from facenet_pytorch import InceptionResnetV1 as IRV1
from facenet_pytorch import MTCNN
from pathlib import Path
from torch import cuda
from tqdm import tqdm
import psycopg2 as pg
import torch
import time
import cv2
import sys
import os

image_size = 160
face_embedding_folder_name = "face_embeddings"


db_connection = pg.connect(database="FaceRecog",
							user = "faceRecogApp",
							password = "facerecogapp@123",
							host = "127.0.0.1",
							port = "5432"
							)
device_name = 'cuda' if cuda.is_available() else 'cpu'
mtcnn_model = MTCNN(
    margin=14,
    factor=0.6,
    keep_all=True,
    device=device_name
)
resnet = IRV1(pretrained='vggface2').double().eval()

def preprocess_face(face):
    face = cv2.resize(face, (image_size,image_size))
    face = torch.from_numpy(face).view(1, 3, image_size, image_size).double().to(device_name)
    return face


def add_embedding_to_db(user_id, embedding_path):
	cursor = db_connection.cursor()
	cursor.execute("INSERT INTO embeddings (user_id, path) VALUES (%d, '%s')" % (user_id, embedding_path))
	db_connection.commit()


def save_face_embedding(face, user_id):
	face_embedding = resnet(preprocess_face(face))
	
	folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), face_embedding_folder_name)
	os.makedirs(folder_path, exist_ok=True)
	file_path = os.path.join(folder_path, f"{user_id}__{int(time.time())}.pt")
	torch.save(face_embedding, file_path)
	add_embedding_to_db(user_id, file_path)
	print("Log:"+ "\033[92m" + " Face saved successfully." + " \033[00m")


def add_user_to_db(user_name):
	cursor = db_connection.cursor()
	cursor.execute("INSERT INTO users (name) VALUES ('%s') RETURNING user_id" % (user_name))
	db_connection.commit()
	user_id = int(cursor.fetchone()[0])
	return user_id


def drawFaceBoundingBox(frame, green=False):
	boxes, probs = mtcnn_model.detect(frame)
	if boxes is None or len(boxes) == 0:
		return None

	box = boxes[0]
	prob = probs[0]

	if prob < 0.9:
		return None

	croppedFace = frame.copy()[int(box[1]): int(box[3]), int(box[0]):int(box[2]), :]
	box_color = (0, 0, 255) if not green else (0,255,0)
	frame = cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), box_color, 3)

	return croppedFace

def start_app():

	user_name = str(input("Enter user name: "))


	print("Usge tips:")
	print("\033[91m" + "- Press [s] button for saving your face into database." + " \033[00m")
	print("\033[91m" + "- Press [q] to exit." + " \033[00m")
	sys.stdout.write("\n")

	for i in range(5, -1, -1):
		sys.stdout.write("\r" + "\033[96m" + "User Creator App will start in "  + " \033[00m" + "\033[91m" + f"{i}s" + " \033[00m")
		sys.stdout.flush()
		if i != 0:
			time.sleep(1)
	sys.stdout.write("\r"+ "\033[96m" + "User Creator App is starting now...+"  + " \033[00m" + "\n")
	sys.stdout.flush()

	return user_name



def start_showing_frames(user_id):
	webcam = cv2.VideoCapture(0)

	while True:
		_, raw_frame = webcam.read()
		frame = raw_frame.copy()

		face = drawFaceBoundingBox(frame)
		cv2.imshow("Webcam", frame)

		key = cv2.waitKey(1) & 0xFF
		if key == ord('s') and face is not None:
			save_face_embedding(face, user_id)
			frame = raw_frame.copy()
			face = drawFaceBoundingBox(frame, green=True)
			cv2.imshow("Webcam", frame)
			key = cv2.waitKey(500) & 0xFF
		elif key == ord('q'):
			break

	webcam.release()
	cv2.destroyAllWindows()
	cv2.waitKey(1)



def main():
	user_name = start_app()
	user_id = add_user_to_db(user_name)
	start_showing_frames(user_id)


if __name__ == '__main__':
	main()
