# Data Retention and Deletion Policy

VisageID stores only encrypted face embeddings derived from user images. Raw images are not persisted. Embedding records are retained for a maximum of 30 days after a user account is removed, after which they are purged automatically. Users may request deletion at any time and associated embeddings are erased within 24 hours.

Encryption keys are supplied through the `ENCRYPTION_KEYS` environment variable. Keys should be rotated on a regular schedule; old keys are kept for decryption only as long as necessary. During rotation, new keys are prepended to the list and the application is restarted so that new data is encrypted with the latest key. Old keys are removed after all data has been re-encrypted or expired.
