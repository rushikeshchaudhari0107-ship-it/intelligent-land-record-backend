import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from db_connection import get_db_connection
from upload import router as upload_router

app = FastAPI(
    title="Intelligent Land Record System",
    description="AI-powered Land Record Digitization and Validation System",
    version="1.0.0"
)


app.include_router(upload_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin
        for origin in [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            os.getenv("FRONTEND_URL", "")
        ]
        if origin
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class LandRecord(BaseModel):
    owner_name: str
    survey_number: str
    village: str
    taluka: str
    district: str
    land_area: float
    land_type: str


@app.get("/")
def root():
    return {
        "message": "Intelligent Land Record API is running"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/api/db-test")
def database_test():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("SELECT current_database();")
        database_name = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return {
            "status": "connected",
            "database": database_name
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@app.get("/api/land-records")
def get_land_records():
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                owner_name,
                survey_number,
                village,
                taluka,
                district,
                land_area,
                land_type,
                created_at
            FROM land_records
            ORDER BY id;
        """)

        records = cursor.fetchall()

        result = []

        for record in records:
            result.append({
                "id": record[0],
                "owner_name": record[1],
                "survey_number": record[2],
                "village": record[3],
                "taluka": record[4],
                "district": record[5],
                "land_area": float(record[6]) if record[6] is not None else None,
                "land_type": record[7],
                "created_at": record[8]
            })

        return {
            "count": len(result),
            "records": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
@app.post("/api/land-records")
def create_land_record(record: LandRecord):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO land_records
            (owner_name, survey_number, village, taluka, district, land_area, land_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            record.owner_name,
            record.survey_number,
            record.village,
            record.taluka,
            record.district,
            record.land_area,
            record.land_type
        ))

        new_id = cursor.fetchone()[0]
        connection.commit()

        return {
            "message": "Land record created successfully",
            "id": new_id
        }

    except Exception as e:
        if connection:
            connection.rollback()

        print("DATABASE ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail=str(e)
    )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()

@app.get("/api/land-records/{record_id}")
def get_land_record(record_id: int):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                id,
                owner_name,
                survey_number,
                village,
                taluka,
                district,
                land_area,
                land_type,
                created_at
            FROM land_records
            WHERE id = %s;
        """, (record_id,))

        record = cursor.fetchone()

        if record is None:
            raise HTTPException(
                status_code=404,
                detail="Land record not found"
            )

        return {
            "id": record[0],
            "owner_name": record[1],
            "survey_number": record[2],
            "village": record[3],
            "taluka": record[4],
            "district": record[5],
            "land_area": float(record[6]) if record[6] is not None else None,
            "land_type": record[7],
            "created_at": record[8]
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
@app.put("/api/land-records/{record_id}")
def update_land_record(record_id: int, record: LandRecord):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            UPDATE land_records
            SET
                owner_name = %s,
                survey_number = %s,
                village = %s,
                taluka = %s,
                district = %s,
                land_area = %s,
                land_type = %s
            WHERE id = %s
            RETURNING id;
        """, (
            record.owner_name,
            record.survey_number,
            record.village,
            record.taluka,
            record.district,
            record.land_area,
            record.land_type,
            record_id
        ))

        updated_record = cursor.fetchone()

        if updated_record is None:
            connection.rollback()
            raise HTTPException(
                status_code=404,
                detail="Land record not found"
            )

        connection.commit()

        return {
            "message": "Land record updated successfully",
            "id": updated_record[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        if connection:
            connection.rollback()

        print("UPDATE DATABASE ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail=str(e)
    )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()
@app.delete("/api/land-records/{record_id}")
def delete_land_record(record_id: int):
    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            DELETE FROM land_records
            WHERE id = %s
            RETURNING id;
        """, (record_id,))

        deleted_record = cursor.fetchone()

        if deleted_record is None:
            connection.rollback()
            raise HTTPException(
                status_code=404,
                detail="Land record not found"
            )

        connection.commit()

        return {
            "message": "Land record deleted successfully",
            "id": deleted_record[0]
        }

    except HTTPException:
        raise

    except Exception as e:
        if connection:
            connection.rollback()

        print("DELETE DATABASE ERROR:", e)

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if cursor:
            cursor.close()

        if connection:
            connection.close()