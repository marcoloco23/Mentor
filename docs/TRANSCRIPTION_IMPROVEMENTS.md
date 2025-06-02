# Transcription Issue Fix

## Problem
The `gpt-4o-transcribe` model was returning "unsupported format" errors for WAV files that worked fine with `whisper-1`. This is a known issue documented in the [OpenAI Community](https://community.openai.com/t/gpt-4o-transcribe-unsupported-format-with-wav/1148957).

## Root Causes
1. **Format Mismatch**: Mobile apps using `expo-audio` typically record in M4A format, but the file handling logic was sometimes mislabeling files
2. **WebM Naming Issues**: Web recordings in WebM format were being incorrectly named as `.wav` files
3. **Strict Format Requirements**: `gpt-4o-transcribe` appears to be more strict about audio format validation than `whisper-1`
4. **No Fallback Mechanism**: When `gpt-4o-transcribe` failed, there was no automatic fallback to `whisper-1`

## Solution Implemented

### 1. Backend Changes (`main.py`)
- **Automatic Fallback**: Added intelligent fallback from `gpt-4o-transcribe` to `whisper-1` when format errors occur
- **Better Error Detection**: Detect "unsupported_format" errors specifically and trigger fallback
- **Enhanced Logging**: Added detailed logging for debugging transcription issues
- **M4A Support**: Added `audio/m4a` to supported MIME types

```python
# Key changes in transcribe_audio endpoint:
try:
    response = llm_client.client.audio.transcriptions.create(**clean_kwargs)
    # ... success handling
except Exception as e:
    error_str = str(e).lower()
    
    # Check if it's a format error and we're using gpt-4o models
    if ("unsupported_format" in error_str or "format you provided" in error_str) and model.startswith("gpt-4o"):
        # Fallback to whisper-1
        fallback_kwargs = clean_kwargs.copy()
        fallback_kwargs["model"] = "whisper-1"
        response = llm_client.client.audio.transcriptions.create(**fallback_kwargs)
```

### 2. Mobile App Changes (`AudioRecorder.tsx`)
- **Fixed File Naming**: Web recordings now correctly use `.webm` extension instead of `.wav`
- **Smart Model Selection**: Automatically use `whisper-1` for WebM files since they have known compatibility issues
- **Improved Format Detection**: Better logic to detect actual audio format based on platform and file extension
- **Proper MIME Types**: Correctly set MIME types for different platforms:
  - iOS/Android: `audio/mp4` for M4A files
  - Web: `audio/webm` for WebM files
- **Enhanced Logging**: Added console logging for debugging file format issues

```typescript
// Key changes in stopRecording:
if (Platform.OS === 'web') {
  // Web typically records in WebM format
  mimeType = 'audio/webm';
  filename = 'audio.webm'; // Always use .webm for web recordings
} else {
  // Mobile platforms (iOS/Android) - typically M4A
  if (filename.endsWith('.m4a') || filename.endsWith('.mp4')) {
    mimeType = 'audio/mp4';
    filename = filename.replace(/\.[^.]+$/, '.m4a');
  }
  // ... other format handling
}

// Smart model selection
const response: TranscriptionResponse = await transcribeAudio(
  formData,
  // Use whisper-1 directly for WebM files since they have known issues with gpt-4o-transcribe
  mimeType === 'audio/webm' ? 'whisper-1' : 'gpt-4o-transcribe'
);
```

### 3. API Client Changes (`mentorApi.ts`)
- **Model Parameter**: Added optional model parameter to `transcribeAudio` function
- **URL Construction**: Properly construct URL with query parameters

## Testing
Run the comprehensive test suite to verify the fix:

```bash
# Basic test
python test_transcription.py

# Comprehensive format testing
python test_transcription_formats.py
```

The comprehensive test will verify:
- WAV files with both models
- WebM files with both models
- Fallback mechanisms
- Proper error handling

## Current Behavior
Based on the logs, the system now works as follows:

1. **Web Platform**: 
   - Records in WebM format
   - Automatically uses `whisper-1` (skips `gpt-4o-transcribe`)
   - Files correctly named as `.webm`

2. **Mobile Platforms**:
   - Records in M4A format
   - Tries `gpt-4o-transcribe` first
   - Falls back to `whisper-1` if format issues occur
   - Files correctly named as `.m4a`

3. **Fallback Logging**:
   ```
   [WARNING] Format error with gpt-4o-transcribe, falling back to whisper-1
   [INFO] Retrying transcription with whisper-1
   [INFO] Transcription successful with whisper-1 fallback
   ```

## Benefits
1. **Reliability**: Automatic fallback ensures transcription always works
2. **Performance**: Still attempts to use the newer `gpt-4o-transcribe` model when appropriate
3. **Smart Routing**: WebM files bypass `gpt-4o-transcribe` entirely to avoid known issues
4. **Compatibility**: Better handling of different audio formats across platforms
5. **Debugging**: Enhanced logging makes it easier to diagnose issues

## Migration Notes
- Existing code will continue to work without changes
- The fallback is automatic and transparent to the client
- WebM files now automatically use `whisper-1` for better reliability
- The response includes the actual model used for transcription
- No breaking changes to the API interface 