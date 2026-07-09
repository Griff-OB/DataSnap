class FileUploader {
    constructor() {
        this.chunkSize = 1024 * 1024; // 1MB chunks
        this.activeUploads = new Map();
    }

    async uploadFile(file, onProgress = null, onComplete = null, onError = null) {
        const uploadId = Date.now().toString();
        const totalChunks = Math.ceil(file.size / this.chunkSize);

        this.activeUploads.set(uploadId, {
            file: file,
            totalChunks: totalChunks,
            uploadedChunks: 0,
            progress: 0
        });

        try {
            for (let i = 0; i < totalChunks; i++) {
                const start = i * this.chunkSize;
                const end = Math.min(start + this.chunkSize, file.size);
                const chunk = file.slice(start, end);

                const chunkData = {
                    file_chunk: chunk,
                    upload_id: uploadId,
                    chunk_index: i,
                    total_chunks: totalChunks,
                    original_filename: file.name
                };

                const response = await window.api.uploadChunk(chunkData);

                if (response.status === 'error') {
                    throw new Error(response.message);
                }

                // Update progress
                const upload = this.activeUploads.get(uploadId);
                upload.uploadedChunks++;
                upload.progress = Math.round((upload.uploadedChunks / totalChunks) * 100);

                if (onProgress) {
                    onProgress(upload.progress, upload.uploadedChunks, totalChunks);
                }

                if (response.status === 'complete') {
                    this.activeUploads.delete(uploadId);
                    if (onComplete) {
                        onComplete(response);
                    }
                    return response;
                }
            }
        } catch (error) {
            this.activeUploads.delete(uploadId);
            if (onError) {
                onError(error);
            }
            throw error;
        }
    }

    cancelUpload(uploadId) {
        this.activeUploads.delete(uploadId);
    }

    getUploadProgress(uploadId) {
        const upload = this.activeUploads.get(uploadId);
        return upload ? upload.progress : 0;
    }

    isUploading(uploadId) {
        return this.activeUploads.has(uploadId);
    }
}

// Create global file uploader
window.fileUploader = new FileUploader();
