import argparse
import json
from pathlib import Path

from loguru import logger

from .src.face_rec import load

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Face Store Initializer")
    parser.add_argument(
        "--rebuild-store",
        action="store_true",
        help="Rebuild the face store from dataset (default: False)",
    )
    parser.add_argument(
        "--face-store-dir",
        type=str,
        default=f"{Path.home()}/.local/share/colan_apps/store/face_db",
        help="Directory to store faces (default: face_store)",
    )
    parser.add_argument(
        "--faces",
        nargs="+",
        required=False,
        help="One or more dataset directories containing face images",
    )
    parser.add_argument(
        "--recognize",
        nargs="+",
        required=False,
        help="One or more images to recognize faces in it",
    )
    args = parser.parse_args()

    rebuild_store = args.rebuild_store
    if rebuild_store:
        logger.warning(f"Rebuild Requested")

    preserve_past = not rebuild_store
    recogniser = load(args.face_store_dir, preserve_past=preserve_past)

    if rebuild_store and args.faces:
        for path in args.faces:
            logger.warning(f"Scan folder {path} for faces")
            all_faces = []
            for file in Path(path).rglob("*"):
                if file.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    all_faces.append((file.stem.split("_")[0], str(file)))
            face_ids = recogniser.register_faces_no_batch(all_faces)
            logger.warning(
                f"Found {len(all_faces)} images and registered {len(face_ids)} faces"
            )
            if len(face_ids) < len(all_faces):
                logger.warning(
                    "Some images were skipped as there is no face in main faces in a single image "
                )
    if args.recognize:
        for path in args.recognize:
            result = recogniser.recognize_faces(path)
            print(json.dumps(result, indent=2))
