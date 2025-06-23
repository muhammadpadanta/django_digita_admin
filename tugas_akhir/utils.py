import hashlib

def calculate_file_hash(file_object):
    """
    Calculates the SHA-256 hash of a file-like object efficiently
    by reading it in chunks.
    """
    if not file_object:
        return ""

    sha256_hash = hashlib.sha256()

    # Ensure we're at the beginning of the file
    file_object.seek(0)

    # Use Django's file chunks to read large files without using too much memory
    for chunk in file_object.chunks():
        sha256_hash.update(chunk)

    # Go back to the beginning of the file for any subsequent operations
    file_object.seek(0)

    return sha256_hash.hexdigest()