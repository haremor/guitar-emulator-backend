import pretty_midi
import uuid
import io
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from db.db import get_main_db, get_file_db
from sqlalchemy.orm import Session
from db.models import MidiFile, MidiMetadata, User, UserRole
from utils.auth import JWTBearer, decodeJWT
from schemas import MidiRequest, UpdateMidiRequest

router = APIRouter(prefix="/midi", tags=["MIDIHandling"])

def validate_uuid(file_id: str):
    try:
        uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file_id format")

async def get_current_user_id(token: str = Depends(JWTBearer()), db: Session = Depends(get_main_db)):
    payload = decodeJWT(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get the user's email from the token payload
    email = payload["sub"]

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.id

@router.post("/generate", dependencies=[Depends(JWTBearer())])
async def generate_midi(
    midi_data: MidiRequest,
    db: Session = Depends(get_main_db),
    file_db: Session = Depends(get_file_db),
    user_id: str = Depends(get_current_user_id)
):
    midi = pretty_midi.PrettyMIDI()
    program = pretty_midi.instrument_name_to_program(midi_data.instrument_name)
    instrument = pretty_midi.Instrument(program=program)

    for event in midi_data.notes:
        pitch = pretty_midi.note_name_to_number(event.note)
        note = pretty_midi.Note(
            velocity=int(event.velocity * 127),
            pitch=pitch,
            start=event.time,
            end=event.time + event.duration
        )
        instrument.notes.append(note)

    midi.instruments.append(instrument)

    # Save the MIDI file to a binary stream
    midi_stream = io.BytesIO()
    midi.write(midi_stream)
    midi_stream.seek(0)

    # Save the binary data in the file database
    file_id = str(uuid.uuid4())
    midi_file = MidiFile(
        id=file_id,
        file_name=midi_data.name,
        file_data=midi_stream.read()
    )
    file_db.add(midi_file)
    file_db.commit()

    # Save the metadata in the main database
    metadata = MidiMetadata(
        id=str(uuid.uuid4()),
        file_name=midi_data.name,
        file_id=file_id,
        user_id=user_id  # Associate the metadata with the user
    )
    db.add(metadata)
    db.commit()

    return {"detail": "MIDI file generated and saved successfully", 'id': metadata.file_id, "file_name": midi_data.name}

@router.get("/get")
async def get_midi_file_by_id(
    file_id: str,
    db: Session = Depends(get_main_db),
    file_db: Session = Depends(get_file_db)
):
    validate_uuid(file_id)
    
    # Get the metadata from the main database
    metadata = db.query(MidiMetadata).filter(MidiMetadata.id == file_id).first()
    if not metadata:
        raise HTTPException(status_code=404, detail="MIDI file not found")

    # Get the binary data from the file database
    midi_file = file_db.query(MidiFile).filter(MidiFile.id == metadata.file_id).first()
    if not midi_file:
        raise HTTPException(status_code=404, detail="MIDI file not found in file database")

    midi_stream = io.BytesIO(midi_file.file_data)
    midi_stream.seek(0)

    return StreamingResponse(
        midi_stream,
        media_type="audio/midi",
        headers={"Content-Disposition": f"attachment; filename={metadata.file_name}.mid"}
    )

@router.get('/list')
async def get_all_midi_files(limit: int = 10, page: int = 1, db: Session = Depends(get_main_db)):
    if limit <= 0 or page <= 0:
        raise HTTPException(status_code=400, detail="Limit and page must be positive integers")

    offset = (page - 1) * limit

    # Query the main database for all MIDI metadata
    midi_files = db.query(MidiMetadata).offset(offset).limit(limit).all()

    if not midi_files:
        return {"detail": "No MIDI files found", "midi_files": []}

    response = [
        {"id": midi_file.id, "file_name": midi_file.file_name, "user_id": midi_file.user_id}
        for midi_file in midi_files
    ]

    return {"midi_files": response}

@router.get('/user-midi')
async def get_user_midi_files(
    user_id: str,
    limit: int = 10,
    page: int = 1,
    db: Session = Depends(get_main_db)
):
    if limit <= 0 or page <= 0:
        raise HTTPException(status_code=400, detail="Limit and page must be positive integers")

    offset = (page - 1) * limit

    # Query the main database for MIDI metadata for the specified user
    midi_files = db.query(MidiMetadata).filter(MidiMetadata.user_id == user_id).offset(offset).limit(limit).all()

    if not midi_files:
        return {"detail": "No MIDI files found for this user", "midi_files": []}

    response = [
        {"id": midi_file.id, "file_name": midi_file.file_name}
        for midi_file in midi_files
    ]

    return {"midi_files": response}

@router.delete("/delete/{file_id}", dependencies=[Depends(JWTBearer())])
async def delete_midi_file(
    file_id: str,
    db: Session = Depends(get_main_db),
    file_db: Session = Depends(get_file_db),
    user_id: str = Depends(get_current_user_id)
):
    validate_uuid(file_id)

    metadata = db.query(MidiMetadata).filter(MidiMetadata.file_id == file_id).first()
    if not metadata:
        raise HTTPException(status_code=404, detail="MIDI metadata not found")

    # Get the user who owns the file
    owner_id = metadata.user_id

    # Get the current user's role
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if the user is the owner or an admin
    if user_id != owner_id and user.role != UserRole.developer:
        raise HTTPException(status_code=403, detail="You do not have permission to delete this file")

    midi_file = file_db.query(MidiFile).filter(MidiFile.id == file_id).first()
    if not midi_file:
        raise HTTPException(status_code=404, detail="MIDI file not found in file database")

    file_db.delete(midi_file)
    file_db.commit()

    db.delete(metadata)
    db.commit()

    return {"detail": "MIDI file and metadata deleted successfully"}

@router.patch("/update/{file_id}", dependencies=[Depends(JWTBearer())])
async def update_midi_file(
    file_id: str,
    update_data: UpdateMidiRequest,
    db: Session = Depends(get_main_db),
    file_db: Session = Depends(get_file_db),
    user_id: str = Depends(get_current_user_id)
):
    validate_uuid(file_id)

    metadata = db.query(MidiMetadata).filter(MidiMetadata.file_id == file_id).first()
    if not metadata:
        raise HTTPException(status_code=404, detail="MIDI metadata not found")

    owner_id = metadata.user_id

    # Ensure the current user is the owner
    if user_id != owner_id:
        raise HTTPException(status_code=403, detail="You do not have permission to update this file")

    # Get the file from the file database
    midi_file = file_db.query(MidiFile).filter(MidiFile.id == file_id).first()
    if not midi_file:
        raise HTTPException(status_code=404, detail="MIDI file not found in file database")

    # Update the file_name if provided
    if update_data.file_name:
        midi_file.file_name = update_data.file_name
        metadata.file_name = update_data.file_name  # Propagate the change to the metadata

    # Update the file_data if provided
    if update_data.file_data:
        midi_file.file_data = update_data.file_data

    file_db.commit()
    db.commit()

    return {"detail": "MIDI file and metadata updated successfully"}