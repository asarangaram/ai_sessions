# Face Recognition APIs

This implementation is based on the article [Hailo guide: Comprehensive guide to building a face recognition system](https://community.degirum.com/t/hailo-guide-comprehensive-guide-to-building-a-face-recognition-system/143)

The above guide from the DeGirum team explains how to build a face database and how to recognize faces in an image or video using a vector database and machine learning models optimized for Hailo processors.

## Approach
Each known face is registered with a 512-dimensional embedding and a unique label or ID. When a new image is provided, faces are first detected using the detection model. For each detected face, the embedding is computed and compared against the database. If the similarity score exceeds the defined threshold, the face is identified.

## Scope
The scope of this project is to get a more robust API out of this, with the purpose of gradually building a face database for photo collections on your Raspberry Pi 5 + Hailo processor (currently using Hailo-8).

The hardware interface must be clearly abstracted so that the model or hardware can be changed at a later stage.

## Database
LanceDB is sufficient for similarity search; however, it has limitations in managing non-vector data. Therefore, we use an SQLite-based relational database to store additional information, such as address book entries and mappings of multiple faces to the same individual Face images are stored as PNG files in a folder.

## Models
This project uses the following models from DeGirum’s Model Zoo.  
1. retinaface_mobilenet--736x1280_quant_hailort_hailo8_1 - for face detection  
2. arcface_mobilefacenet--112x112_quant_hailort_hailo8_1 - for face embedding  

## Requirements
* A new face can be registered at any time by submitting a face image along with the associated person’s details.  
  If the id of the person is provided, it will be attached to that person.  
  If the name of the person is provided, a new person is automatically registered.  
* A face is always associated with a person.  
* A face may be reassigned from one person to another as a correction. 
* A face can be deleted to avoid getting detected in the future.  

* Multiple people can share the same name; therefore, a unique ID is used.
* A person is associated with at least one face.  
* A person already in the store is identified by ID, not by name.  
* If a person is deleted, all the faces associated with that person are deleted.  
* If all faces of a person are removed, that person’s record is automatically deleted.  

* For the image provided:  
  * All the faces in that image are detected.  
  * Two thresholds are used
    1. If confidence scopre is above threshold1, a person id and confidence score will be returned.  
    2. If no match exceeds threshold1, threshold2 is considered. If multiple people fall within this range, all matches are returned with their confidence scores.  
       The user can use this information to manually verify and register a new face.
  * For unknown persons, only the bounding box will be returned.  
    The user can crop the face, assign a name, and then register that person. 
