import cv2
import face_recognition
import time
import numpy

"""
recognize_face(paths, known_encodings)
Arguments
    - paths: a list of paths to images that we are checking
    - known_encodings: a dictionary of students ids as the keys matched to the encodings
Return
    - Returns a tuple of the best id match out of all of the image paths and the percentage match
"""
def recognize_face(paths, known_encodings):
    imgs = get_image(paths)
    encoded = encode_image(imgs, paths)
    result = compare_faces(encoded, known_encodings)
    return result

"""
get_image(imgs)
Arguments
    - imgs: a list of paths to images that we are checking
Return
    - Returns a list of the images from the paths
"""
def get_image(imgs):
    result = []
    for img in imgs:
        im = cv2.cvtColor(cv2.imread(img, 0), cv2.COLOR_BGR2RGB)
        result.append(low_res(im))
    return result

"""
low_res(cv2_img)
Arguments
    - cv2_img: a cv2 image
Return
    - Returns the image but scaled down with a set height of 128 pixels
"""
def low_res(cv2_img):
    height, width, channel, = cv2_img.shape
    new_height = 128
    new_width = new_height*width//height
    reduced_res = cv2.resize(cv2_img, (new_width, new_height), interpolation = cv2.INTER_AREA)
    return reduced_res

"""
encode_image(imgs, path=None)
Arguments
    - imgs: a list of cv2 images
    - path: an optional argument which is a list of paths matching to the imgs (used for debugging and tells you which image does not have a face detected)
Return
    - Returns a list of the encoded images 
"""
def encode_image(imgs, path=None):
    all_faces = []
    for i in range(len(imgs)):
        img = imgs[i]
        # * Keep the model at "small" because "large" works worse, change num_jitters to increase accuracy of encodings (slower)
        faces = face_recognition.face_encodings(img, model="small", num_jitters=2) 
        if len(faces) > 0:
            # * If there are multiple faces it just takes the first one
            all_faces.append(faces[0])
        else:
            # * Useful debug
            if path is not None:
                print(f"No face detected in {path[i]}.")
            else:
                print("No face detected.")
    return all_faces

"""
compare_faces(imgs, known_encodings)
Arguments
    - imgs: a list of image encodings
    - known_encodings: the dictionary of students ids matched to pre-processed encodings of images of them
Return
    - Returns the best id match among the images and its percentage
"""
def compare_faces(imgs, known_encodings):
    # ID, percent
    best = ["Nobody", 0]
    for num in known_encodings:
        encoding = numpy.array(known_encodings[num]["encoding"])
        highestPercent = 0
        for img in imgs:
            percents = face_recognition.face_distance([encoding], img)
            # * Reverses the percents so that higher percent means more accurate
            percents = list(map(lambda x: 1 - x, percents))

            if max(percents) > highestPercent:
                highestPercent = max(percents)

        # * Changes the tolerance of the recognition, Ex: if the tolerance is 0.5 that any image which a lower percentage that 50% is ignored
        if highestPercent > 0.5:
            # * Optional print which tells you all of the possible candidates for the best student
            print(known_encodings[num]["sid"], highestPercent, known_encodings[num]["_id"])
            if highestPercent > best[1]:
                best = [known_encodings[num]["sid"], highestPercent]

    
    return best

"""
singleImageEncoding(img)
Arguments
    - img: a single image path
Return
    - Returns the encoding of that image (mainly used for testing or pre-processing images)
"""
def singleImageEncoding(img):
    return encode_image(get_image([img]), [img])



# * Some old tests of the recognition
if __name__ == "__main__":
    database = {}
    database["Musk"] = singleImageEncoding("api/Images/mrmusk3.jpg")
    database["David"] = singleImageEncoding("api/Images/Unknown1.jpg")
    unknown_faces = ["api/Images/mrmusk.jpg","api/Images/mrmusk2.jpg","api/Images/David.jpg"]

    startingtime = ( time.time() )
    print(recognize_face(unknown_faces, database))
    endingtime = ( time.time() )
    print(f"Time taken for {len(unknown_faces)} image(s):",endingtime-startingtime)
