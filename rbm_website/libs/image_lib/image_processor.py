import numpy as np
import cStringIO as cst
import re
import base64
from PIL import Image as pil
import os

# A class used to handle images and converting between formats

# Given a data url, returns a PIL image
def convert_url_to_image(url, img_id):
	image = __open_url_canvas(url)
	return image

# Given a data url, returns a NumPy array of the image
def convert_url_to_array(url, img_id):
	image_data = convert_url_to_image(url, img_id)
	image = pil.open(image_data)
	return convert_image_to_array(image)

# Converts a NumPy array representing an image to a PIL image
def convert_array_to_image(array, height, width):
	array = array.flatten()
	img_array = []
	for row in range(0, height):
		img_array.append(array[row*width : (row+1)*width])
	img_array = np.asarray(img_array, np.uint8) * 255
	return pil.fromarray(img_array)

# Converts a PIL image to a NumPy array
def convert_image_to_array(image):
	if image is None:
		return None
	else:
		return np.array(image.convert("L")).flatten() / 255

# Retrieves a image from a given path
def retrieve_image(image_path, height, width):
	image = __open_image(image_path, height, width)
	return (convert_image_to_array(image), os.path.splitext(os.path.split(image_path)[1])[0])

# Retrieves a class of images from a given directory in a folder
def retrieve_image_class(class_path, height, width):
    image_data = []
    image_names = []
    for image_name in os.listdir(class_path):
        image = __open_image(class_path + '/' + image_name, height, width)
        image_data.append(convert_image_to_array(image))
        image_names.append(os.path.splitext(image_name)[0])
    return (image_data, image_names)

# Retrieves all images in a directory
def retrieve_all_images(root_path, height, width):
	data = []
	names = []
	for class_dir in os.listdir(root_path):
		(class_data, class_names) = retrieve_image_class(root_path + '/' + class_dir, height, width)
		data.append(class_data)
		names.append(class_names)
	return ([image for sublist in data for image in sublist], [item for sublist in names for item in sublist])

# Retrieves all images in a directory and returns them as a list of
# Image names and Image data in base 64
def retrieve_images_base64(path):
    image_data = []
    image_names = []
    for image_name in os.listdir(path):
    	with open(path + '/' + image_name, "rb") as image_file:
    		encoded_image = base64.b64encode(image_file.read())
    		image_data.append(encoded_image)

        image_names.append(os.path.splitext(image_name)[0])
    return (image_data, image_names)

# Retrieves a single image in base64
def retrieve_image_base64(path):
    with open(path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read())
        return encoded_image

# Checks to make sure an image is valid
def __check_image(image, image_path, exp_height, exp_width):
	if image is None:
		print("Warning: %s is not a valid image!" % (image_path))
	else:
		(act_width, act_height) = image.size
		if (act_width != exp_width):
			print("Warning: %s has width %s, expected %s!" % (image_path, act_width, exp_width))
		if (act_height != exp_height):
			print("Warning: %s has height %s, expected %s!" % (image_path, act_height, exp_height))

# Checks to make sure a file path is valid
def __check_file(file_path):
	if (os.path.isfile(file_path)):
		return True
	else:
		print("Warning: %s does not exist! ...skipping..." % (file_path))
		return False

def __open_url_canvas(url):
	image_str = re.search(r'base64,(.*)', url).group(1)
	pil_image = cst.StringIO(image_str.decode('base64'))
	return pil_image

# Opens an image and returns a PIL image
def __open_image(image_path, height, width):
	if __check_file(image_path):
		image = pil.open(image_path)
		__check_image(image, image_path, height, width)
		return image
	else:
		return None
