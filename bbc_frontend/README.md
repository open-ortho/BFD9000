# BFD9000 Frontend

This frontend provides a user interface for uploading and classifying X-ray images using the BFD9000 X-ray Classification API.

## Features

- **Drag and Drop Upload**: Easily upload X-ray images by dragging and dropping them into the designated area.
- **Image Classification**: Display the classification results including X-ray type, rotation, and flip status.

## Setup

### Prerequisites

- A web browser (latest version of Chrome, Firefox, or Edge recommended)
- The BFD9000 backend API running locally or accessible over the network

### Running Locally

1. **Clone the repository**:
    ```sh
    git clone <repository-url>
    cd bbc_frontend
    ```

2. **Start a simple HTTP server**:

    - Using Python:
        ```sh
        python -m http.server 8080
        ```

    - Using Node.js:
        ```sh
        npx http-server -p 8080
        ```

3. **Open your web browser and navigate to** `http://localhost:8080`:
    - You will see the `index.html` file loaded and can start using the application.

### Usage

1. **Upload X-rays**:
    - Drag and drop X-ray images (png, jpg, tiff) into the drop area on the main page.
    - The images will be processed and classified by the backend API.

2. **View Results**:
    - The classification results will be displayed below the drop area, showing the X-ray type, rotation, and flip status.
