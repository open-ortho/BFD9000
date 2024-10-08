# BFD9000 Backend

This backend provides an API for accessing BFD9000 X-ray classification models. It uses FastAPI to serve endpoints for classifying X-ray images and retrieving detailed information about them.

## Features

- **X-ray Classification**: Classify X-ray images into types (e.g., lateral, frontal, chest).
- **Rotation and Flip Classification**: Determine the rotation and flipping of lateral and frontal ceph X-rays.
- **Detailed X-ray Information**: Retrieve detailed information about an X-ray image, including type, rotation, and flip status.

## Endpoints

- `GET /`: Root endpoint providing a welcome message.
- `POST /xray-info`: Retrieve detailed information about an X-ray image.
- `POST /xray-class`: Classify an X-ray image into its type.
- `POST /lateral-fliprot`: Classify the rotation and flipping of a lateral ceph X-ray.
- `POST /frontal-fliprot`: Classify the rotation and flipping of a frontal ceph X-ray.

## Running Locally

### Prerequisites

- Python 3.12

### Setup

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd bbc_backend
    ```

2. **Create a virtual environment**:
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```sh
    pip install torch torchvision torchaudio
    pip install fastai scikit-image fastapi[standard]
    ```

4. **Run the application**:
    ```sh
    python main.py
    ```

The API will be available at `http://localhost:8000`.

For more information, visit the API documentation at `http://localhost:8000/docs`.