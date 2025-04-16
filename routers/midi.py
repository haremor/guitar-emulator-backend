import pretty_midi
import uuid
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from db.db import get_db
from sqlalchemy.orm import Session
from db.models import MidiFile
from utils.auth import JWTBearer
from schemas import MidiRequest

router = APIRouter(prefix="/midi", tags=["MIDIHandling"])

@router.post("/generate-midi", dependencies=[Depends(JWTBearer())])
def generate_midi(midi_data: MidiRequest, db: Session = Depends(get_db)):
    midi = pretty_midi.PrettyMIDI()
    
    # Convert instrument name to program number
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
    midi_stream.seek(0)  # Reset the stream position to the beginning

    # Save file metadata and binary data in the database
    midi_file = MidiFile(
        id=str(uuid.uuid4()),
        file_name=midi_data.name,  # Use the name from the request body
        file_data=midi_stream.read(),  # Read binary data from the stream
    )
    db.add(midi_file)
    db.commit()

    return {"detail": "MIDI file generated and saved successfully", "file_name": midi_data.name}

@router.get("/get/{file_name}")
def get_midi_file_by_name(file_name: str, db: Session = Depends(get_db)):
    midi_file = db.query(MidiFile).filter(MidiFile.file_name == file_name).first()
    if not midi_file:
        raise HTTPException(status_code=404, detail="MIDI file not found")

    # Create a BytesIO stream from the binary data
    midi_stream = io.BytesIO(midi_file.file_data)
    midi_stream.seek(0)  # Reset the stream position to the beginning

    # Return the binary MIDI file as a streaming response
    return StreamingResponse(
        midi_stream,
        media_type="audio/midi",
        headers={"Content-Disposition": f"attachment; filename={file_name}.mid"}
    )