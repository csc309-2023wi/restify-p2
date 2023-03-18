# REST API Endpoints

-   URL paths
-   [HTTP methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods)
-   Query parameters/JSON body
-   [Error status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

---

## 👍 Property

-   ### `/property/`

    -   #### `GET`: return a list of properties, default to all properties, but possibly limited by query parameters

        **Query Params**

        -   `host_id`: user ID of the host that owns the property

        **Response**

        ```json
        [
            {
                "property_id": 6532,
                "host_id": 9236,
                "address": "123 Broadway, New York, NY, United States",
                "description": "Natus id molestias corporis minima quisquam. Tempora dolor consectetur officia sequi veniam. Nostrum necessitatibus voluptatem et et. Voluptate veritatis minima ipsam aperiam eos dolor sint vero.",
                "guests_allowed": 3,
                "availability": [
                    {
                        "from": "March 1, 2025",
                        "to": "March 1, 2026",
                        "price": 500.34
                    }
                ],
                "amenities": ["WiFi", "Pool", "Air conditioning"],
                "images": ["7f46165474d11ee5836777d85df2cdab", "a4b46da106e59f424a2310cb7766366e"]
            }
        ]
        ```

        **Error Codes**

        -   ...

    -   #### `PUT`: create a new property

        **JSON Body**

        ```json
        {
            "address": "123 Broadway, New York, NY, United States",
            "description": "Natus id molestias corporis minima quisquam. Tempora dolor consectetur officia sequi veniam. Nostrum necessitatibus voluptatem et et. Voluptate veritatis minima ipsam aperiam eos dolor sint vero.",
            "guests_allowed": 3,
            "availability": [
                {
                    "from": "March 1, 2025",
                    "to": "March 1, 2026",
                    "price": 500.34
                }
            ],
            "amenities": ["WiFi", "Pool", "Air conditioning"],
            "images": [
                {
                    "ext": "png",
                    "data": "iVBORw0KGgoAANSUhEAB4AAAAAC/kV7ZAAAAOXRFWHRTb..."
                },
                {
                    "ext": "jpg",
                    "data": "p1aS2M6tYsaJ++eUXtWzZ0uK+f/75R48++qhFvbXnLi4u..."
                }
            ]
        }
        ```

        Host ID inferred from logged in user. Images encoded in `base64` and sent along with file extensions.

        **Response**

        ```json
        {
            "property_id": 6532,
            "host_id": 9236
        }
        ```

        **Error Codes**

        -   `400`: required fields missing or incorrect data format
        -   `401`: user not logged in

-   ### `/property/<id>/`

    -   #### `GET`: fetch a specific property identified by its ID

        **Response**

        ```json
        {
            "property_id": 6532,
            "host_id": 9236,
            "address": "123 Broadway, New York, NY, United States",
            "description": "Natus id molestias corporis minima quisquam. Tempora dolor consectetur officia sequi veniam. Nostrum necessitatibus voluptatem et et. Voluptate veritatis minima ipsam aperiam eos dolor sint vero.",
            "guests_allowed": 3,
            "availability": [
                {
                    "from": "March 1, 2025",
                    "to": "March 1, 2026",
                    "price": 500.34
                }
            ],
            "amenities": ["WiFi", "Pool", "Air conditioning"],
            "images": ["7f46165474d11ee5836777d85df2cdab", "a4b46da106e59f424a2310cb7766366e"]
        }
        ```

        **Error Codes**

        -   `401`: user not logged in
        -   `404`: nonexistent property ID

    -   #### `POST`: update an existing property listing

        **JSON Body**

        ```json
        {
            "address": "123 Broadway, New York, NY, United States",
            "description": "Natus id molestias corporis minima quisquam. Tempora dolor consectetur officia sequi veniam. Nostrum necessitatibus voluptatem et et. Voluptate veritatis minima ipsam aperiam eos dolor sint vero.",
            "guests_allowed": 3,
            "availability": [
                {
                    "from": "March 1, 2025",
                    "to": "March 1, 2026",
                    "price": 500.34
                }
            ],
            "amenities": ["WiFi", "Pool", "Air conditioning"],
            "images": {
                "delete": ["7f46165474d11ee5836777d85df2cdab"],
                "add": [
                    {
                        "filename": "opq.png",
                        "data": "YYfK9AAAACXBIWXMAAC4jAAAuIwF4pT92AAEAAElEQ..."
                    }
                ]
            }
        }
        ```

        **Error Codes**

        -   `400`: incorrect data format
        -   `401`: user not logged in
        -   `403`: user is not the owner of property
        -   `404`: nonexistent property ID

    -   #### `DELETE` delete a specific property

---

## 👍 Image

-   ### `/images/<hash>`

    -   #### `GET`: fetch an image, encoded with the specified parameters

        **Query Params** (all optional)

        -   `width`: width of the encoded image
        -   `height`: height of the encoded image
        -   `ext`: file extension, indicating the encoding of the image; one of `jpg`, `png`, `webp`

        Only one of `width`, `height` should be specified. If both are specified, the request is invalid.

        **Error Codes**

        -   `400`: incorrect parameters
        -   `401`: user not logged in
        -   `404`: nonexistent image hash

---

## 👍 Reservation

-   ### `/reservation/`

    -   #### `GET`: return a list of reservations, limited by query parameters

        **Query Params** (at least one must be specified)

        -   `guest_id`: user ID of the guest that initiated the reservation
        -   `property_id`: propety ID of the property that the reservation is about
        -   `status`: one of `Pending`, `Denied`, `Expired`, `Approved`, `Completed`, `Cancelled`, `Terminated`
        -   `from_date`: start date on or before all returned reservations
        -   `to_date`: end date on or after all returned reservations

        **Response**

        ```json
        [
            {
                "reservation_id": 5874,
                "guest_id": 6113,
                "status": "Pending",
                "property_id": 6532,
                "guests": 2,
                "from": "2025-03-05",
                "to": "2025-03-08"
            }
        ]
        ```

        **Error Codes**

        -   `400`: incorrect parameters
        -   `401`: user not logged in

-   ### `/reservation/create/<id>/`

    -   #### `POST`: create a new reservation request

        **JSON Body**

        ```json
        {
            "guests": 2,
            "from": "2025-03-05",
            "to": "2025-03-08"
        }
        ```

        Guest ID inferred from logged in user. The default status is `pending`. Property ID is inferred from the URL

        **Response** (the entire saved reservation object)

        ```json
        {
            "reservation_id": 5874,
            "guest_id": 6113,
            "status": "Pending",
            "property_id": 6532,
            "guests": 2,
            "from": "2025-03-05",
            "to": "2025-03-08"
        }
        ```

        **Error Codes**

        -   `401`: user not logged in
        -   `403`: invalid values for from and to dates
        -   `404`: nonexistent property ID


-   ### `/reservation/update/<id>/`

    -   #### `PUT`: Allows the host of a property to update the reservation status of pending reservations to 'Approved' or 'Denied.

        **Response** (the entire saved reservation object)

        ```json
        {
            "reservation_id": 5874,
            "guest_id": 6113,
            "status": "Approved",
            "property_id": 6532,
            "guests": 2,
            "from": "2025-03-05",
            "to": "2025-03-08"
        }
        ```

        **Error Codes**
        -   `400`: incorrect parameters
        -   `401`: user not logged in
        -   `403`: user is not the host of the property that is trying to be reserved or the reservation has a non pending status
        -   `404`: nonexistent reservation ID

-   ### `/reservation/cancel/<id>/`

    -   #### `GET`: Allows the user who initiated the reservation to cancel the reservation if status is pending or request cancellation using notification if status is approved.

        **JSON Body**

        ```json
        {
            "status": "Cancelled",
            "guests": 2,
            "from": "2025-03-05",
            "to": "2025-03-08"
        }
        ```
        
        **Error Codes**
        -   `401`: user not logged in
        -   `403`: user does not have permission to cancel this reservation or has a non cancellable status
        -   `404`: nonexistent reservation ID

-   ### `/reservation/cancel/request/<id>/`

    -   #### `GET`: Allows the host of a property that is in the reservation process to cancel any reservation. If cancellation was first requested by user then status is cancelled otherwise status is terminated.

        **Response** (the entire updated reservation object)

        ```json
        {
            "reservation_id": 5874,
            "guest_id": 6113,
            "status": "Terminated",
            "property_id": 6532,
            "guests": 2,
            "from": "2025-03-05",
            "to": "2025-03-08"
        }
        ```

        **Error Codes**

        -   `401`: user not logged in
        -   `403`: user is not the host of the reservation property, or reservation has a non cancellable status
        -   `404`: nonexistent reservation ID


        Valid status changes for host:

        -   `Pending` -> `Approved` || `Denied`,
        -   `Approved` -> `Terminated` || `Cancelled`

        Valid status changes for guest:

        -   `Pending` -> `Cancelled`


## 👍 Notifications

-   ### `/notifications/`

    -   #### `GET`: return a list of all uncleared notifications for a user

       The user is inferred from logged in user.

       **Response**

       ```json
       [
           {
               "notification_id": 5874,
               "user_id": 6113,
               "reservation_id": 6000,
               "created_at": "2025-03-01T20:43:20",
               "is_read": false,
               "is_cancel_req": false,
               "is_cleared": false,
               "content": "Hello"
           }
       ]
       ```

-   ### `/notifications/read/<id>/`

    -   #### `GET`: returns the notification with notifcation id and marks is_read and is_cleared to true

       The user is inferred from logged in user.

       **Response**

       ```json
       [
           {
               "notification_id": 5874,
               "user_id": 6113,
               "reservation_id": 6000,
               "created_at": "2025-03-01T20:43:20",
               "is_read": true,
               "is_cancel_req": false,
               "is_cleared": true,
               "content": "Hello"
           }
       ]
       ```
        

       **Error Codes**

       -   `401`: user not logged in
       -   `403`: user tries to access a notification of a different user or tries to read a notification that has already been cleared
       -   `404`: nonexistent notification id
