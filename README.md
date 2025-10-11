# ZK Backend

## Usage

1. Enter your variables in the `.env` file
    - `VEHICLE_PASSWORD` will be the password that all vehicles use to authenticate with the server. Enter this in the
      firmware code/config.
2. Run
   ```shell
    docker compose watch
    ```

### Database Setup

After successfully starting the container, the database should have set up the right tables. Use a tool like pgAdmin to
connect to it.

#### Required Steps

Create a new row in the `vehicledb` table. Enter the imei of your vehicle (It will be printed in hexadecimal when you
launch the firmware). Give it a name and a type (currently only `Car` is available).

Insert your UIDs in the `rfiduiddb` table.

#### Optional

Add firmware files in the `firmwaredb` table. You can use the admin endpoint for this (see fastapi generated docs)
