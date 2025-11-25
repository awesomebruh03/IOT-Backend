# API Endpoint Documentation

This document provides a detailed overview of all the API endpoints in the application.

## HTTP Endpoints

### Client Endpoints (`/client`)

#### `POST /client/predict/`

*   **Description:** This endpoint is responsible for processing an audio file to make a prediction about the sound it contains.
*   **Request:**
    *   **Method:** `POST`
    *   **Body:** The request must be a `multipart/form-data` request containing an audio file (e.g., `.wav`, `.mp3`). The file should be associated with the key `file`.
*   **Response:**
    *   **Success (200 OK):** A JSON object with the following structure:
        ```json
        {
            "label": "Siren",
            "confidence": 99.87,
            "status": "success"
        }
        ```
    *   **Error (500 Internal Server Error):** A JSON object with the following structure:
        ```json
        {
            "status": "error",
            "message": "Details about the error."
        }
        ```
*   **Side Effect:** After a successful prediction, the result is broadcasted as a JSON string to all clients connected to the `/client/ws/client/ai` WebSocket endpoint.

#### `GET /client/predictions/`

*   **Description:** Retrieve historical predictions from the PostgreSQL database.
*   **Query Parameters:**
    *   `limit` (optional): The maximum number of predictions to return. Defaults to 100.
*   **Response:**
    *   **Success (200 OK):** A JSON array of prediction objects.
        ```json
        [
            {
                "id": 1,
                "label": "Siren",
                "confidence": 99.87,
                "timestamp": "2024-05-22T12:00:00.000Z"
            }
        ]
        ```

#### `GET /client/predictions/recent/`

*   **Description:** Retrieve recent predictions from the Redis cache.
*   **Query Parameters:**
    *   `limit` (optional): The maximum number of predictions to return. Defaults to 100.
*   **Response:**
    *   **Success (200 OK):** A JSON array of prediction objects from Redis.
        ```json
        [
            {
                "label": "Siren",
                "confidence": 99.87,
                "timestamp": "2024-05-22T12:00:00.000Z"
            }
        ]
        ```

#### `GET /client/sensors/`

*   **Description:** Retrieve historical sensor readings from the PostgreSQL database.
*   **Query Parameters:**
    *   `sensor_id` (optional): Filter readings by a specific sensor ID.
    *   `limit` (optional): The maximum number of readings to return. Defaults to 100.
*   **Response:**
    *   **Success (200 OK):** A JSON array of sensor reading objects.
        ```json
        [
            {
                "id": 1,
                "sensor_id": "temp-01",
                "value": "23.5",
                "timestamp": "2024-05-22T12:00:00.000Z"
            }
        ]
        ```

#### `GET /client/sensors/recent/`

*   **Description:** Retrieve recent sensor readings from the Redis cache.
*   **Query Parameters:**
    *   `limit` (optional): The maximum number of readings to return. Defaults to 100.
*   **Response:**
    *   **Success (200 OK):** A JSON array of sensor reading objects from Redis.
        ```json
        [
            {
                "sensor_id": "temp-01",
                "value": "23.5",
                "timestamp": "2024-05-22T12:00:00.000Z"
            }
        ]
        ```

## WebSocket Endpoints

### IoT Device Endpoints (`/iot`)

#### `WEBSOCKET /iot/ws/data`

*   **Description:** This endpoint is designed for an IoT device to stream JSON sensor data to the backend.
*   **Receives:** JSON objects.
    ```json
    {
        "sensor_id": "temp-01",
        "value": 23.5,
        "timestamp": "2024-05-21T10:00:00Z"
    }
    ```
*   **Sends:** A confirmation text message back to the connected device.
    ```
    Received data: {'sensor_id': 'temp-01', ...}
    ```
*   **Side Effect:** The received JSON data is saved to the databases and broadcasted to all clients connected to the `/client/ws/client/data` endpoint.

#### `WEBSOCKET /iot/ws/audio`

*   **Description:** This endpoint is intended for an IoT device to stream raw audio data to the backend for prediction.
*   **Receives:** Raw audio bytes.
*   **Sends:** A confirmation text message back to the connected device containing the prediction.
    ```
    Received and processed audio. Prediction: Siren
    ```
*   **Side Effect:** The prediction result is saved to the databases and broadcasted as a JSON string to all clients connected to the `/client/ws/client/ai` WebSocket endpoint.

### Client Application Endpoints (`/client`)

#### `WEBSOCKET /client/ws/client/data`

*   **Description:** This endpoint allows a client application to connect and receive real-time sensor data broadcasts.
*   **Receives:** Nothing from the client. The connection is kept alive by the client sending any text message.
*   **Sends:** JSON data broadcasted from the `/iot/ws/data` endpoint.

#### `WEBSOCKET /client/ws/client/ai`

*   **Description:** This endpoint allows a client application to connect and receive real-time AI prediction broadcasts.
*   **Receives:** Nothing from the client. The connection is kept alive by the client sending any text message.
*   **Sends:** JSON prediction data broadcasted from the `/iot/ws/audio` endpoint.
