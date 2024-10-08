import io
import logging
from logging.handlers import RotatingFileHandler
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastai.vision.all import load_learner, PILImage
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
import uvicorn
import imageio
import numpy as np
from skimage import exposure, img_as_ubyte


# Constants
ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/tiff"]
MAX_IMAGE_SIZE = 10 * 1024 * 1024

# function stub needed by models dataloaders
def label_func(f):
    pass

# Configure Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler("app.log", maxBytes=1000000, backupCount=5)
    ]
)
logger = logging.getLogger(__name__)

# Suppress watchfiles INFO logs to reduce verbosity
watchfiles_logger = logging.getLogger("watchfiles.main")
watchfiles_logger.setLevel(logging.WARNING)

# Global dictionary to store loaded models
models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    global models
    try:
        models['xray'] = load_learner('models/xtype-simple_resnet18_fp16_01')
        logger.info("Loaded X-ray classification model.")
        
        models['lateral'] = load_learner('models/lateral_fliprot_resnet18_fp16_07')
        logger.info("Loaded Lateral classification model.")
        
        models['frontal'] = load_learner('models/frontal_fliprot_resnet18_fp16_03')
        logger.info("Loaded Frontal classification model.")
        
    except Exception as e:
        logger.exception("Error loading models: %s", e)
        raise RuntimeError(f"Failed to load models: {e}") from e

    # Yield control back to the application
    yield

    # Shutdown logic (if needed)
    logger.info("Shutdown tasks can be handled here if necessary.")


# Initialize FastAPI application
app = FastAPI(
    title="BFD9000 Ai API",
    description="API for accessing BFD9000 X-ray classification models.",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware to the app to allow only localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log incoming requests and outgoing responses.
    """
    logger.info(f"Incoming request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code} for {request.method} {request.url}")
        return response
    except Exception as e:
        logger.exception("Error processing request: %s", e)
        raise e

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom handler for HTTPExceptions to log errors.
    """
    logger.error(f"HTTPException: {exc.detail} for {request.method} {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Custom handler for unhandled exceptions to log errors.
    """
    logger.exception("Unhandled exception: %s for %s %s", exc, request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )

@app.get("/")
async def root():
    """
    Root endpoint providing a welcome message.
    """
    logger.info("Root endpoint accessed.")
    return {"message": "Welcome to the BFD9000 X-ray Classification API. Visit /docs for API documentation."}

@app.post("/xray-info")
async def get_xray_info(image: UploadFile = File(..., max_size=MAX_IMAGE_SIZE)):
    """
    Endpoint to retrieve detailed information about an X-ray image.
    It first classifies the type of X-ray and then, based on the type,
    uses the appropriate model to get additional information.
    
    Response Structure:
    {
        "type_prediction": "class",
        "type_probability": probability,
        "rotation": rotation,  // 0, 90, 180, 270 or null
        "flip": true/false or null
    }
    """
    logger.info("/xray-info endpoint called.")
    await validate_image(image)
    
    try:
        xray_model = models.get('xray')
        if not xray_model:
            logger.error("X-ray model not loaded.")
            raise HTTPException(status_code=500, detail="X-ray model not loaded.")
        
        # Load and preprocess image
        pil_img = await load_and_preprocess_image(image)
        logger.debug("Image successfully loaded and preprocessed for /xray-info.")
        
        # Step 1: Classify the type of X-ray
        xray_pred, xray_idx, xray_probs = await run_in_threadpool(xray_model.predict, pil_img)
        xray_class = str(xray_pred)
        xray_prob = float(xray_probs[xray_idx])
        logger.info(f"X-ray classification: {xray_class} with probability {xray_prob:.4f}")
        
        # Initialize response
        response_data = {
            "type_prediction": xray_class,
            "type_probability": xray_prob,
            "rotation": None,
            "flip": None
        }
        
        # Step 2: If X-ray is lateral or frontal, get additional info
        if xray_class.lower() == "lateral":
            lateral_model = models.get('lateral')
            if not lateral_model:
                logger.error("Lateral model not loaded.")
                raise HTTPException(status_code=500, detail="Lateral model not loaded.")
            
            lateral_pred, lateral_idx, lateral_probs = await run_in_threadpool(lateral_model.predict, pil_img)
            logger.info(f"Lateral classification: {lateral_pred} with probability {lateral_probs[lateral_idx]:.4f}")
            
            lateral_result = map_fliprot_prediction(str(lateral_pred), 'lateral')
            response_data["rotation"] = lateral_result["rotation"]
            response_data["flip"] = lateral_result["flip"]
        
        elif xray_class.lower() == "frontal":
            frontal_model = models.get('frontal')
            if not frontal_model:
                logger.error("Frontal model not loaded.")
                raise HTTPException(status_code=500, detail="Frontal model not loaded.")
            
            frontal_pred, frontal_idx, frontal_probs = await run_in_threadpool(frontal_model.predict, pil_img)
            logger.info(f"Frontal classification: {frontal_pred} with probability {frontal_probs[frontal_idx]:.4f}")
            
            frontal_result = map_fliprot_prediction(str(frontal_pred), 'frontal')
            response_data["rotation"] = frontal_result["rotation"]
            response_data["flip"] = frontal_result["flip"]
        
        return response_data
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error in /xray-info endpoint: %s", e)
        raise HTTPException(status_code=500, detail="An error occurred while processing the image.")

@app.post("/xray-class")
async def classify_xray(image: UploadFile = File(..., max_size=MAX_IMAGE_SIZE)):
    """
    Endpoint to classify an X-ray image into its type (e.g., lateral, frontal, chest, etc.).
    Uses only the X-ray classification model.
    
    Response Structure:
    {
        "prediction": "class",
        "probability": probability,
        "all_predictions": [
            ["class1", probability1],
            ["class2", probability2],
            ...
        ]
    }
    """
    logger.info("/xray-class endpoint called.")
    await validate_image(image)
    
    try:
        xray_model = models.get('xray')
        if not xray_model:
            logger.error("X-ray model not loaded.")
            raise HTTPException(status_code=500, detail="X-ray model not loaded.")
        
        # Load and preprocess image
        pil_img = await load_and_preprocess_image(image)
        logger.debug("Image successfully loaded and preprocessed for /xray-class.")
        
        # Make prediction
        pred, pred_idx, probs = await run_in_threadpool(xray_model.predict, pil_img)
        logger.info(f"X-ray classification: {pred} with probability {probs[pred_idx]:.4f}")
        
        # Prepare response
        result = {
            "prediction": str(pred),
            "probability": float(probs[pred_idx]),
            "all_predictions": [
                [str(cls), float(prob)] for cls, prob in zip(xray_model.dls.vocab, probs)
            ]
        }
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error in /xray-class endpoint: %s", e)
        raise HTTPException(status_code=500, detail="An error occurred while processing the image.")
    

@app.post("/lateral-fliprot")
async def classify_lateral_fliprot(image: UploadFile = File(..., max_size=MAX_IMAGE_SIZE)):
    """
    Endpoint to classify the rotation and flipping of a lateral ceph X-ray.
    Uses the Lateral classification model.
    
    Response Structure:
    {
        "prediction": "rotation_class",
        "probability": probability,
        "all_predictions": [
            ["class1", probability1],
            ["class2", probability2],
            ...
        ]
    }
    """
    logger.info("/lateral-fliprot endpoint called.")
    await validate_image(image)
    return await classify_specific_model(image, 'lateral')

@app.post("/frontal-fliprot")
async def classify_frontal_fliprot(image: UploadFile = File(..., max_size=MAX_IMAGE_SIZE)):
    """
    Endpoint to classify the rotation of a frontal ceph X-ray.
    Uses the Frontal classification model.
    
    Response Structure:
    {
        "prediction": "rotation",
        "probability": probability,
        "all_predictions": [
            ["class1", probability1],
            ["class2", probability2],
            ...
        ]
    }
    """
    logger.info("/frontal-rot endpoint called.")
    await validate_image(image)
    return await classify_specific_model(image, 'frontal')

async def classify_specific_model(image: UploadFile, model_key: str):
    """
    Generic function to classify an image using a specific model.
    
    Args:
        image (UploadFile): The uploaded image file.
        model_key (str): The key to identify which model to use ('lateral' or 'frontal').
    
    Returns:
        dict: The classification result.
    """
    try:
        model = models.get(model_key)
        if not model:
            logger.error("Model '%s' not loaded.", model_key)
            raise HTTPException(status_code=500, detail=f"Model '{model_key}' not loaded.")
        
        # Load and preprocess image
        pil_img = await load_and_preprocess_image(image)
        logger.debug("Image successfully loaded and preprocessed for model '%s'.", model_key)
        
        # Make prediction
        pred, pred_idx, probs = await run_in_threadpool(model.predict, pil_img)
        logger.info("Model '%s' prediction: %s with probability %.4f", model_key, pred, probs[pred_idx])
        
        # Prepare response
        result = {
            "prediction": str(pred),
            "probability": float(probs[pred_idx]),
            "all_predictions": [
                [str(cls), float(prob)] for cls, prob in zip(model.dls.vocab, probs)
            ]
        }
        return result
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Error in classify_specific_model for model '%s': %s", model_key, e)
        raise HTTPException(status_code=500, detail="An error occurred while processing the image.")

def map_fliprot_prediction(prediction: str, model_type: str):
    """
    Maps the model's prediction to rotation and flip.
    
    Args:
        prediction (str): The class predicted by the model.
        model_type (str): The type of model ('lateral' or 'frontal').

    Returns:
        dict: {"rotation": int or None, "flip": bool or None}
    """
    mapping = {
        "0": {"rotation": 0, "flip": False},
        "0F": {"rotation": 0, "flip": True},
        "90": {"rotation": 90, "flip": False},
        "90F": {"rotation": 90, "flip": True},
        "180": {"rotation": 180, "flip": False},
        "180F": {"rotation": 180, "flip": True},
        "270": {"rotation": 270, "flip": False},
        "270F": {"rotation": 270, "flip": True},
        "None": {"rotation": None, "flip": None}
    }
    result = mapping.get(prediction, {"rotation": None, "flip": None})
    if result["rotation"] is None:
        logger.warning("%s model returned an unrecognized class '%s'. Rotation and flip are set to null.", model_type.capitalize(), prediction)
    return result

async def validate_image(image: UploadFile):
    """
    Validates the uploaded image to ensure it is of an allowed MIME type.
    
    Args:
        image (UploadFile): The uploaded image file.
    
    Raises:
        HTTPException: If the image is not of an allowed type.
    """
    if image.content_type not in ALLOWED_MIME_TYPES:
        logger.warning("Unsupported file type: %s", image.content_type)
        raise HTTPException(status_code=400, detail="Unsupported file type. Only JPEG, PNG, and TIFF are allowed.")
    logger.debug("Image validation passed for content type: %s", image.content_type)


async def load_and_preprocess_image(image: UploadFile) -> PILImage:
    """
    Loads and preprocesses the uploaded image.

    This function performs the following steps:
    1. Loads the image using imageio.
    2. Handles RGBA images by ignoring the alpha channel.
    3. Applies intensity adjustments using scikit-image's exposure.rescale_intensity with out_range=np.float64.
    4. Converts the adjusted image to unsigned bytes (uint8) using img_as_ubyte.
    5. Converts the NumPy array directly to FastAI's PILImage.

    Args:
        image (UploadFile): The uploaded image file.

    Returns:
        PILImage: The preprocessed image compatible with FastAI models.

    Raises:
        HTTPException: If there's an error in loading or processing the image.
    """
    try:
        # Read image bytes
        image_bytes = await image.read()
        logger.debug("Read %d bytes from the uploaded image.", len(image_bytes))

        # Load image using imageio
        img = imageio.imread(io.BytesIO(image_bytes))
        logger.debug("Image loaded with shape %s and dtype %s.", img.shape, img.dtype)

        # Handle RGBA by ignoring the alpha channel
        if img.ndim == 3 and img.shape[2] == 4:
            img = img[..., :3]
            logger.debug("Image has alpha channel. Ignoring the alpha channel.")

        # Apply intensity adjustment with out_range=np.float64
        img_adjusted = exposure.rescale_intensity(img, in_range='image', out_range=np.float64)
        logger.debug("Applied intensity adjustment to the image with out_range=np.float64.")

        # Convert adjusted image to unsigned bytes
        img_ubyte = img_as_ubyte(img_adjusted)
        logger.debug("Converted image to unsigned bytes using img_as_ubyte.")

        # Create PILImage for FastAI directly from NumPy array
        pil_img = PILImage.create(img_ubyte)
        logger.debug("Converted processed image to PILImage.")

        return pil_img
    except Exception as e:
        logger.exception("Failed to load and preprocess image: %s", e)
        raise HTTPException(status_code=400, detail="Invalid image data.")



if __name__ == "__main__":
    # Run the application with Uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
